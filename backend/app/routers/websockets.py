# app/routers/websockets.py
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from sqlalchemy.ext.mutable import MutableDict
from ..database import get_db
from ..manager import ConnectionManager
from ..services.roomServices import RoomService
from ..models import Room

router = APIRouter()
logger = logging.getLogger(__name__)
manager = ConnectionManager()


@router.websocket("/ws/{room_id}/{username}")
async def websocket_endpoint(
    websocket: WebSocket, 
    room_id: str, 
    username: str, 
    db: Session = Depends(get_db)
):
    try:
        await manager.connect(room_id, websocket, username)
        # logger.info("User %s connected to room %s", username, room_id)
    except Exception:
        logger.exception("Failed to connect websocket for %s in room %s", username, room_id)
        await websocket.close()
        return

    try:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            room = Room(id=room_id, users=[MutableDict({"username": username, "online": True})])
            db.add(room)
            db.commit()
            db.refresh(room)
        else:
            existing = next((u for u in room.users if u.get("username") == username), None)
            if existing:
                existing["online"] = True
            else:
                room.users.append(MutableDict({"username": username, "online": True}))
            db.commit()

        # NEW: send in-memory code first, fallback to DB
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

        while True:
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                logger.info("User %s disconnected from room %s", username, room_id)
                break
            except Exception:
                logger.exception("Error receiving message from %s in room %s", username, room_id)
                break

            try:
                data = json.loads(raw)
                msg_type = data.get("type")
            except json.JSONDecodeError:
                manager.set_code(room_id, raw)
                await manager.broadcast_code(room_id, raw, websocket)
                continue

            if msg_type == "CODE_UPDATE":
                code = data.get("code", "")
                manager.set_code(room_id, code)  
                await manager.broadcast_code(room_id, code, websocket)

            elif msg_type == "TYPING_UPDATE":
                await manager.broadcast_typing(room_id, websocket, data.get("typing", False))
                await RoomService.send_user_list(room_id, db, manager)

            elif msg_type == "USER_UPDATE":
                await RoomService.send_user_list(room_id, db, manager)

            else:
                logger.warning("Unknown message type %s from %s in room %s", msg_type, username, room_id)

    finally:
        # Cleanup on disconnect
        try:
            await manager.disconnect(room_id, websocket, db)
            RoomService.mark_user_offline(db, room_id, username)
            await RoomService.send_user_list(room_id, db, manager)
            db.close()
        except Exception:
            logger.exception("Error during cleanup for %s in room %s", username, room_id)

