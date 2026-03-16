from beanie import Document
from typing import Optional
from datetime import datetime

class GeneratedDocument(Document):
    session_id: Optional[str] = None
    doc_type: str
    content: str
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "documents"