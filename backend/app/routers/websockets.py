import json
import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.websocket_manager import ConnectionManager, get_manager
from app.services.room_service import RoomService

router = APIRouter()
logger = logging.getLogger(__name__)

async def run_sync_db_op(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args)

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
        room = await run_sync_db_op(RoomService.join_room, db, room_id, username)

        latest_code = manager.get_code(room_id)

        code_to_send = latest_code if latest_code is not None else (room.code or "")
        
        await websocket.send_json({
            "type": "CODE_UPDATE", 
            "code": code_to_send, 
            "sender": "System"
        })
        
        active_users = RoomService.get_active_user_objs(manager, room_id)

        final_list = await run_sync_db_op(
            RoomService.get_room_users_sync, 
            db, 
            room_id, 
            active_users
        )
        await RoomService.broadcast_user_list(manager, room_id, final_list)

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

                    active_users = RoomService.get_active_user_objs(manager, room_id)

                    final_list = await run_sync_db_op(
                        RoomService.get_room_users_sync, 
                        db, 
                        room_id, 
                        active_users
                    )
                    await RoomService.broadcast_user_list(manager, room_id, final_list)
                
                elif msg_type == "USER_UPDATE":
                     active_users = RoomService.get_active_user_objs(manager, room_id)
                     final_list = await run_sync_db_op(
                        RoomService.get_room_users_sync, 
                        db, 
                        room_id, 
                        active_users
                    )
                     await RoomService.broadcast_user_list(manager, room_id, final_list)

            except WebSocketDisconnect:
                break
            except Exception:
                logger.exception(f"Error in websocket loop for {username}")
                break

    finally:
        await manager.disconnect(room_id, websocket)

        await run_sync_db_op(RoomService.mark_user_offline_sync, db, room_id, username)
        active_users = RoomService.get_active_user_objs(manager, room_id)
        final_list = await run_sync_db_op(
            RoomService.get_room_users_sync, 
            db, 
            room_id, 
            active_users
        )
        await RoomService.broadcast_user_list(manager, room_id, final_list)
        db.close()