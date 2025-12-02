from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import Column, String, Text, Integer, JSON, DateTime
from sqlalchemy.sql import func
from ..core.database import Base

class Room(Base):
    __tablename__ = "rooms"

    id = Column(String, primary_key=True, index=True)
    code = Column(Text, default="")
    users = Column(MutableList.as_mutable(JSON), default=list)
    name = Column(String, nullable=True)
    limit = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
