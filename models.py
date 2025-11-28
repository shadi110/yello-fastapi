from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from database import Base

class Entry(Base):
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    profile_image = Column(String, nullable=True)
    location = Column(String, nullable=True)

    mobiles = Column(JSON, default=[])
    reaching_video = Column(String, nullable=True)

    social = Column(JSON, default={})     # instagram / facebook...
    type = Column(JSON, default={})       # main / sub

    date_added = Column(DateTime(timezone=True), server_default=func.now())
    date_updated = Column(DateTime(timezone=True), onupdate=func.now())
