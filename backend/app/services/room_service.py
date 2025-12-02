import json
import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.mutable import MutableDict
from app.models.room import Room

logger = logging.getLogger(__name__)

class RoomService:

    @staticmethod
    def join_room(db: Session, room_id: str, username: str):
        room = db.query(Room).filter(Room.id == room_id).first()

        if not room:

            raise HTTPException(404, "Room does not exist")

        users_list = room.users or []
        room.users = [MutableDict(u) for u in users_list]
        
        active_usernames = {u["username"] for u in room.users}

        if len(room.users) >= room.limit and username not in active_usernames:
            raise HTTPException(403, "Room is full")

        existing_user = next((u for u in room.users if u["username"] == username.lower()), None)

        if existing_user:
            if existing_user.get("online"):
                raise HTTPException(409, "User already online")
            existing_user["online"] = True
        else:
            room.users.append(MutableDict({"username": username, "online": True}))

        db.commit()
        db.refresh(room)
        return room

    @staticmethod
    def mark_user_offline(db: Session, room_id: str, username: str):
        if not username: 
            return

        try:
            room = db.query(Room).filter(Room.id == room_id).first()
            if not room: 
                return

            users = room.users or []
            updated = False

            for i, u in enumerate(users):
                if not isinstance(u, MutableDict):
                    users[i] = MutableDict(u)
                
                if users[i].get("username") == username and users[i].get("online"):
                    users[i]["online"] = False
                    users[i]["typing"] = False
                    updated = True

            if updated:
                room.users = users 
                db.add(room)
                db.commit()
                db.refresh(room)                
        except Exception:
            logger.exception(f"Error marking user {username} offline")
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
            logger.exception("Error getting active user objects")
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
                if not await manager._safe_send(s, msg):
                    dead_sockets.append(s)
            
            if dead_sockets:
                await manager.remove_dead_sockets(room_id, dead_sockets)
        except Exception:
            logger.exception("Failed to send user list")