from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class Social(BaseModel):
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    snapchat: Optional[str] = None
    telegram: Optional[str] = None
    tiktok: Optional[str] = None

class EntryType(BaseModel):
    main: str
    sub: str

class EntryBase(BaseModel):
    title: str
    description: Optional[str] = None
    profile_image: Optional[str] = None
    location: Optional[str] = None
    mobiles: List[str] = []
    reaching_video: Optional[str] = None

    social: Social
    type: EntryType

class EntryCreate(EntryBase):
    pass

class EntryUpdate(EntryBase):
    pass

class Entry(EntryBase):
    id: int
    date_added: datetime
    date_updated: Optional[datetime]

    class Config:
        orm_mode = True
