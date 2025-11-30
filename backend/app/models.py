# app/models.py
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import JSON
from sqlalchemy import Column, String,Text,Integer
from sqlalchemy.sql import func
from .database import Base

class Room(Base):
    __tablename__ = "rooms"
    id = Column(String, primary_key=True, index=True)
    code = Column(Text)
    users = Column(MutableList.as_mutable(JSON))
    name = Column(String, nullable=True) 
    limit = Column(Integer)
