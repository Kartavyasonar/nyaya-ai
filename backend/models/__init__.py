from beanie import Document, Indexed
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ─── Enums ───────────────────────────────────────────────────────────────────

class UserRole(str, Enum):
    USER = "user"
    NGO = "ngo"
    LAWYER = "lawyer"
    ADMIN = "admin"


class Language(str, Enum):
    HINDI = "hi"
    ENGLISH = "en"
    BENGALI = "bn"
    TELUGU = "te"
    MARATHI = "mr"
    TAMIL = "ta"
    GUJARATI = "gu"
    URDU = "ur"
    KANNADA = "kn"
    ODIA = "or"
    MALAYALAM = "ml"
    PUNJABI = "pa"
    ASSAMESE = "as"
    MAITHILI = "mai"
    SANTALI = "sat"
    KASHMIRI = "ks"
    NEPALI = "ne"
    SINDHI = "sd"
    KONKANI = "kok"
    DOGRI = "doi"
    MANIPURI = "mni"
    BODO = "brx"


class QueryCategory(str, Enum):
    CRIMINAL = "criminal"
    CIVIL = "civil"
    LABOUR = "labour"
    PROPERTY = "property"
    FAMILY = "family"
    CONSUMER = "consumer"
    RTI = "rti"
    SCHEME = "scheme"
    CONSTITUTIONAL = "constitutional"
    WOMEN_RIGHTS = "women_rights"
    CHILD_RIGHTS = "child_rights"
    TRIBAL = "tribal"
    ENVIRONMENT = "environment"
    OTHER = "other"


class DocumentType(str, Enum):
    RTI_APPLICATION = "rti_application"
    LEGAL_NOTICE = "legal_notice"
    CONSUMER_COMPLAINT = "consumer_complaint"
    LABOUR_COMPLAINT = "labour_complaint"
    POLICE_COMPLAINT = "police_complaint"
    AFFIDAVIT = "affidavit"
    BAIL_APPLICATION = "bail_application"
    TENANT_NOTICE = "tenant_notice"
    DOMESTIC_VIOLENCE_APPLICATION = "domestic_violence_application"


# ─── User Model ──────────────────────────────────────────────────────────────

class User(Document):
    name: str
    phone: Indexed(str, unique=True)
    email: Optional[EmailStr] = None
    preferred_language: Language = Language.HINDI
    state: Optional[str] = None
    district: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False
    whatsapp_id: Optional[str] = None
    query_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
        indexes = ["phone", "whatsapp_id"]


# ─── Query Model ─────────────────────────────────────────────────────────────

class Source(BaseModel):
    act: str
    section: Optional[str] = None
    title: str
    excerpt: str
    relevance_score: float


class Query(Document):
    user_id: Optional[str] = None
    session_id: str
    original_query: str
    translated_query: Optional[str] = None
    detected_language: Language = Language.HINDI
    category: QueryCategory = QueryCategory.OTHER
    response: str
    response_translated: Optional[str] = None
    sources: List[Source] = []
    confidence_score: float = 0.0
    needs_lawyer: bool = False
    suggested_helplines: List[str] = []
    processing_time_ms: int = 0
    channel: str = "web"  # web, whatsapp, sms, ivr
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "queries"
        indexes = ["session_id", "user_id", "category", "created_at"]


# ─── Generated Document Model ─────────────────────────────────────────────────

class GeneratedDocument(Document):
    user_id: Optional[str] = None
    session_id: str
    doc_type: DocumentType
    title: str
    content: str
    language: Language = Language.HINDI
    pdf_url: Optional[str] = None
    metadata: dict = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "generated_documents"
        indexes = ["user_id", "session_id", "doc_type"]


# ─── Session Model ────────────────────────────────────────────────────────────

class ConversationTurn(BaseModel):
    role: str  # user / assistant
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    language: Optional[str] = None


class Session(Document):
    session_id: Indexed(str, unique=True)
    user_id: Optional[str] = None
    channel: str = "web"
    language: Language = Language.HINDI
    state: Optional[str] = None
    conversation: List[ConversationTurn] = []
    context: dict = {}
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "sessions"
        indexes = ["session_id", "user_id"]


# ─── Feedback Model ───────────────────────────────────────────────────────────

class Feedback(Document):
    query_id: str
    session_id: str
    rating: int  # 1-5
    helpful: bool
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "feedback"
