from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional

from ..database import get_db
from ..models import Room
from ..schemas import RoomResponse, SaveRequest

router = APIRouter()

# CREATE ROOM
@router.post("/rooms", response_model=RoomResponse)
def create_room(
    username: Optional[str] = Query(None),
    roomId: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    if not roomId:
        raise HTTPException(status_code=400, detail="roomId is required")
    if limit < 1 or limit >= 10:
        raise HTTPException(status_code=400, detail="Limit must be 1-10")

    existing = db.query(Room).filter(Room.id == roomId).first()
    if existing:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "roomId": existing.id,
                "users": existing.users or [],
                "limit": existing.limit
            }
        )

    new_room = Room(
        id=roomId,
        users=[{"username": username, "online": True}],
        limit=limit
    )
    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "roomId": new_room.id,
            "users": new_room.users,
            "limit": new_room.limit
        }
    )

# GET / JOIN ROOM
@router.get("/rooms/{room_id}", response_model=RoomResponse)
def get_room(
    room_id: str,
    username: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    room: Room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room does not exist")

    room.users = room.users or []
    room.users = [MutableDict(u) for u in room.users]

    # Check if room limit exceeded
    if len(room.users) >= (room.limit or 0) and not any(u["username"] == username for u in room.users):
        raise HTTPException(status_code=403, detail="Room is full")

    existing_user = next((u for u in room.users if u["username"] == username), None)
    if existing_user and existing_user.get("online"):
        raise HTTPException(status_code=409, detail="User already online")
    if existing_user:
        existing_user["online"] = True
    else:
        room.users.append(MutableDict({"username": username, "online": True}))
    db.commit()
    db.refresh(room)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "roomId": room.id,
            "users": room.users,
            "limit": room.limit
        }
    )

# SAVE CODE
@router.post("/rooms/save")
def save_code(payload: SaveRequest, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == payload.roomId).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    old_code = room.code or ""
    if old_code.strip() == payload.code.strip():
        raise HTTPException(status_code=304, detail="No changes")

    room.code = payload.code
    room.name = payload.username
    db.commit()
    return {"message": "Code saved successfully"}

@router.patch("/rooms/{room_id}/limit")
def update_room_limit(
    room_id: str,
    new_limit: int = Query(..., ge=1, le=10),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    # Check current users count
    current_count = room.limit or 0
    if new_limit < current_count:
        raise HTTPException(
            status_code=400,
            detail=f"New limit {new_limit} is less than current users {current_count}"
        )

    room.limit = new_limit
    db.commit()
    db.refresh(room)
    return {"message": f"Room limit updated to {new_limit}", "limit": new_limit}