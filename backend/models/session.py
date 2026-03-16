from beanie import Document
from typing import Optional, List
from datetime import datetime

class Session(Document):
    session_id: str
    language: str = "en"
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "sessions"