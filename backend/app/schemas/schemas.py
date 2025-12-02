# app/schemas.py
from pydantic import BaseModel
from typing import List

class UserSchema(BaseModel):
    username: str
    online: bool

class RoomResponse(BaseModel):
    roomId: str
    users: List[UserSchema]
    limit : int


class AutocompleteRequest(BaseModel):
    code: str
    cursorPosition: int
    language: str

class AutocompleteResponse(BaseModel):
    suggestion: str


class SaveRequest(BaseModel):
    roomId: str
    username: str
    code: str
