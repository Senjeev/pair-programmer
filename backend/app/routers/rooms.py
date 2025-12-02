import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.models.room import Room
from app.schemas.schemas import RoomResponse, SaveRequest
from app.services.room_service import RoomService
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
                limit=existing.limit
            )

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
    except SQLAlchemyError:
        db.rollback()
        logger.exception("SQLAlchemy error while creating room")
        raise HTTPException(500, "Database error")
    except Exception:
        logger.exception("Unexpected error in creating room")
        raise HTTPException(500, "Unexpected server error")


@router.get("/rooms/{room_id}", response_model=RoomResponse)
def get_room(
    room_id: str,
    username: str = Query(...),
    db: Session = Depends(get_db)
):
    try:
        room = RoomService.join_room(db, room_id, username)

        return RoomResponse(
            roomId=room.id,
            users=room.users or [],
            limit=room.limit
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error in joining room")
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
        logger.exception("SQLAlchemy error in save code")
        raise HTTPException(500, "Failed to save code")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while saving code")
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

        if new_limit <= room.limit:
            raise HTTPException(400, "New limit cannot be lower than current limit")
        room.limit = new_limit
        db.commit()
        db.refresh(room)
        return {"message": "Room limit updated", "limit": new_limit}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error updating limit")
        raise HTTPException(500, "Failed to update limit")