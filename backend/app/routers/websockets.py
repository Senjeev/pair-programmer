import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from sqlalchemy.ext.mutable import MutableDict

from app.core.database import get_db
from app.services.websocket_manager import ConnectionManager, get_manager
from app.services.room_service import RoomService
from app.models.room import Room

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/{room_id}/{username}")
async def websocket_endpoint(
    websocket: WebSocket, 
    room_id: str, 
    username: str, 
    db: Session = Depends(get_db),
    manager: ConnectionManager = Depends(get_manager) 
):
    try:
        await manager.connect(room_id, websocket, username)
    except Exception:
        logger.exception(f"Failed to connect websocket for {username}")
        await websocket.close()
        return

    try:

        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            room = Room(id=room_id, users=[MutableDict({"username": username, "online": True})], limit=5)
            db.add(room)
            db.commit()
        else:
            users = room.users or []
            existing = next((u for u in users if u.get("username") == username), None)
            if existing:
                existing["online"] = True
            else:
                users.append(MutableDict({"username": username, "online": True}))
                room.users = users
            db.commit()

        latest_code = manager.get_code(room_id)
        if latest_code:
            await websocket.send_json({
                "type": "CODE_UPDATE", 
                "code": latest_code, 
                "sender": "System"
            })
        elif room.code:
            await websocket.send_json({
                "type": "CODE_UPDATE", 
                "code": room.code, 
                "sender": "System"
            })

        await RoomService.send_user_list(room_id, db, manager)

        # 4. Message Loop
        while True:
            try:
                raw = await websocket.receive_text()
                data = json.loads(raw)
                msg_type = data.get("type")

                if msg_type == "CODE_UPDATE":
                    code = data.get("code", "")
                    await manager.broadcast_code(room_id, code, websocket)

                elif msg_type == "TYPING_UPDATE":
                    await manager.broadcast_typing(room_id, websocket, data.get("typing", False))
                    await RoomService.send_user_list(room_id, db, manager)
                
                elif msg_type == "USER_UPDATE":
                     await RoomService.send_user_list(room_id, db, manager)

            except WebSocketDisconnect:
                break
            except Exception:
                logger.exception(f"Error in websocket loop for {username}")
                break

    finally:
        await manager.disconnect(room_id, websocket)
        RoomService.mark_user_offline(db, room_id, username)
        await RoomService.send_user_list(room_id, db, manager)
        db.close()