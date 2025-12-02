import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.mutable import MutableDict

from typing import Optional
from ..database import get_db
from ..models import Room
from ..schemas import RoomResponse, SaveRequest

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/rooms", response_model=RoomResponse)
def create_room(
    username: str = Query(...),
    roomId: str = Query(...),
    limit: int = Query(..., ge=1, le=10),
    db: Session = Depends(get_db)
):
    try:
        existing = db.query(Room).filter(Room.id == roomId).first()
        if existing:
            return RoomResponse(
                roomId=existing.id,
                users=existing.users or [],
                limit=existing.limit)

        room = Room(
            id=roomId,
            users=[{"username": username, "online": True}],
            limit=limit
        )

        db.add(room)
        db.commit()
        db.refresh(room)
        return RoomResponse(
            roomId=room.id,
            users=room.users or [],
            limit=room.limit
        )

    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("SQLAlchemy error while creating room")
        raise HTTPException(500, "Database error while creating room")

    except HTTPException:
        raise

    except Exception:
        logger.exception("Unexpected error in create_room")
        raise HTTPException(500, "Unexpected server error")


@router.get("/rooms/{room_id}", response_model=RoomResponse)
def get_room(
    room_id: str,
    username: str = Query(...),
    db: Session = Depends(get_db)
):
    try:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise HTTPException(404, "Room does not exist")

        room.users = [MutableDict(u) for u in (room.users or [])]
        print("New name",username)
        active_usernames = {u["username"] for u in room.users}
        print("Active usernames:", active_usernames)    
        if len(room.users) >= room.limit and username not in active_usernames:
            raise HTTPException(403, "Room is full")

        existing = next((u for u in room.users if u["username"] == username), None)

        if existing:
            if existing.get("online"):
                raise HTTPException(409, "User already online")
            existing["online"] = True
        else:
            room.users.append(MutableDict({"username": username, "online": True}))

        db.commit()
        db.refresh(room)
        return RoomResponse(
            roomId=room.id,
            users=room.users or [],
            limit=room.limit)

    except SQLAlchemyError:
        db.rollback()
        logger.exception("SQLAlchemy error in get_room")
        raise HTTPException(500, "Database error")

    except HTTPException:
        raise

    except Exception:
        logger.exception("Unexpected error in get_room")
        raise HTTPException(500, "Unexpected server error")


@router.post("/rooms/save")
def save_code(payload: SaveRequest, db: Session = Depends(get_db)):
    try:
        room = db.query(Room).filter(Room.id == payload.roomId).first()
        if not room:
            raise HTTPException(404, "Room not found")
        
        if (room.code or "").strip() == payload.code.strip():
            raise HTTPException(304, "No changes")

        room.code = payload.code
        room.name = payload.username

        db.commit()
        return {"message": "Code saved successfully"}

    except SQLAlchemyError:
        db.rollback()
        logger.exception("SQLAlchemy error in save_code")
        raise HTTPException(500, "Failed to save code")

    except HTTPException:
        raise

    except Exception:
        logger.exception("Unexpected error in save_code")
        raise HTTPException(500, "Unexpected server error")

@router.patch("/rooms/{room_id}/limit")
def update_room_limit(
    room_id: str,
    new_limit: int = Query(..., ge=1, le=10),
    db: Session = Depends(get_db)
):
    try:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise HTTPException(404, "Room not found")

        current_limit = room.limit

        if new_limit <= current_limit:
            raise HTTPException(
                400,
                detail=f"New limit cannot be lower than or equal to current limit"
            )

        room.limit = new_limit
        db.commit()
        db.refresh(room)

        return {"message": "Room limit updated", "limit": new_limit}

    except SQLAlchemyError:
        db.rollback()
        logger.exception("SQLAlchemy error in update_room_limit")
        raise HTTPException(500, "Failed to update limit")

    except HTTPException:
        raise

    except Exception:
        logger.exception("Unexpected error in update_room_limit")
        raise HTTPException(500, "Unexpected server error")
