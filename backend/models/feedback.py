from beanie import Document
from typing import Optional
from datetime import datetime

class Feedback(Document):
    session_id: Optional[str] = None
    rating: int = 5
    comment: Optional[str] = None
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "feedback"