from beanie import Document
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Query(Document):
    session_id: Optional[str] = None
    question: str
    answer: Optional[str] = None
    language: str = "en"
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "queries"