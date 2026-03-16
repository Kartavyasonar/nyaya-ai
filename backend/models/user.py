from beanie import Document
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(Document):
    phone: Optional[str] = None
    name: Optional[str] = None
    language: str = "en"
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "users"