from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import json
from ..database import get_db
from ..manager import ConnectionManager
from ..services.roomServices import RoomService
from ..models import Room
from sqlalchemy.ext.mutable import MutableDict

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws/{room_id}/{username}")
async def websocket_endpoint(
    websocket: WebSocket, 
    room_id: str, 
    username: str, 
    db: Session = Depends(get_db)
):
    await manager.connect(room_id, websocket, username)

    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        room = Room(id=room_id, users=[MutableDict({"username": username, "online": True})])
        db.add(room)
        db.commit()
        db.refresh(room)
    else:
        room.users = room.users or []
        existing = next((u for u in room.users if u.get("username") == username), None)
        if not existing:
            room.users.append(MutableDict({"username": username, "online": True}))
        else:
            existing["online"] = True
        db.commit()

    if room.code:
        try:
            await websocket.send_json({"type": "CODE_UPDATE", "code": room.code, "sender": "System"})
        except Exception:
            pass

    await RoomService.send_user_list(room_id, db, manager)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                # If raw text, treat as code update
                room.code = raw
                db.commit()
                await manager.broadcast_code(room_id, raw, websocket)
                continue

            msg_type = data.get("type")

            if msg_type == "CODE_UPDATE":
                room.code = data.get("code", "")
                await manager.broadcast_code(room_id, room.code, websocket)

            elif msg_type == "TYPING_UPDATE":
                await manager.broadcast_typing(room_id, websocket, data.get("typing", False))
                await RoomService.send_user_list(room_id, db, manager)

            elif msg_type == "USER_UPDATE":
                await RoomService.send_user_list(room_id, db, manager)

    except WebSocketDisconnect:
        await manager.disconnect(room_id, websocket, db)
        RoomService.mark_user_offline(db, room_id, username)
        await RoomService.send_user_list(room_id, db, manager)
