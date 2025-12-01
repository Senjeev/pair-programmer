# app/services/roomServices.py
import json
from sqlalchemy.orm import Session
from sqlalchemy.ext.mutable import MutableDict
from fastapi import WebSocket
from app.models import Room
import logging

logger = logging.getLogger(__name__)

class RoomService:

    @staticmethod
    def mark_user_offline(db: Session, room_id: str, username: str):
        if not username:
            return

        try:
            room = db.query(Room).filter(Room.id == room_id).first()
            if not room:
                logger.debug("No room found for id=%s", room_id)
                return

            users = room.users or []

            # Ensure MutableDict
            for i, u in enumerate(users):
                if not isinstance(u, MutableDict):
                    try:
                        users[i] = MutableDict(u)
                    except Exception:
                        logger.debug("Failed converting user to MutableDict: %s", u)

            updated = False
            for u in users:
                if u.get("username") == username and u.get("online", True):
                    u["online"] = False
                    u["typing"] = False
                    updated = True
                    break

            if updated:
                room.users = users
                db.add(room)
                db.commit()
                db.refresh(room)

        except Exception:
            logger.exception("Error marking user offline: %s")
            db.rollback()


    @staticmethod
    def active_user_objs(manager, room_id: str):
        try:
            conns = manager.active_connections.get(room_id, [])
            return [
                {
                    "username": c["username"],
                    "typing": c.get("typing", False),
                    "online": True
                }
                for c in conns
            ]
        except Exception:
            logger.exception("Error getting active user objects: %s")
            return []


    @staticmethod
    async def send_user_list(room_id: str, db: Session, manager):
        try:
            active_users = RoomService.active_user_objs(manager, room_id)
            active_names = {u["username"] for u in active_users}

            room = db.query(Room).filter(Room.id == room_id).first()
            db_users = list(room.users or []) if room else []

            offline_users = []
            for u in db_users:
                uname = u.get("username")
                if uname and uname not in active_names:
                    offline_users.append({
                        "username": uname,
                        "online": False,
                        "typing": False
                    })

            final_list = active_users + offline_users
            msg = json.dumps({"type": "USER_UPDATE", "users": final_list})

            async with manager._get_lock(room_id):
                sockets = [c["socket"] for c in manager.active_connections.get(room_id, [])]

            dead_sockets = []

            for s in sockets:
                try:
                    ok = await manager._safe_send(s, msg)
                    if not ok:
                        dead_sockets.append(s)
                except Exception :
                    logger.exception("Failed sending to socket: %s")
                    dead_sockets.append(s)
            if dead_sockets:
                await manager.remove_dead_sockets(room_id, dead_sockets)

        except Exception:
            logger.exception("Failed to send user list: %s")
