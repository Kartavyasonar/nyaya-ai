"""
NYAYA AI — API Routes
All REST endpoints for web app, WhatsApp webhook, document generation
"""
import uuid
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request, Response, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from loguru import logger
import io

from services.llm_service import llm_service
from services.whatsapp_service import whatsapp_service
from services.pdf_service import pdf_service
from middleware.auth import get_current_user, require_auth, create_access_token, create_refresh_token, hash_password, verify_password
from models import User, Query, Session, GeneratedDocument, Feedback, ConversationTurn, Language, DocumentType
from datetime import datetime

# ─── Routers ─────────────────────────────────────────────────────────────────

query_router = APIRouter(prefix="/query", tags=["Query"])
auth_router = APIRouter(prefix="/auth", tags=["Auth"])
document_router = APIRouter(prefix="/documents", tags=["Documents"])
whatsapp_router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    language: Optional[str] = None
    channel: str = "web"


class QueryResponse(BaseModel):
    query_id: str
    session_id: str
    response: str
    detected_language: str
    category: str
    sources: list
    needs_lawyer: bool
    suggested_helplines: list
    confidence_score: float
    processing_time_ms: int


class DocumentRequest(BaseModel):
    doc_type: str  # rti_application, legal_notice, consumer_complaint, police_complaint
    user_details: dict
    case_details: dict
    language: str = "en"
    generate_pdf: bool = True


class RegisterRequest(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    password: str
    preferred_language: str = "hi"
    state: Optional[str] = None


class LoginRequest(BaseModel):
    phone: str
    password: str


class FeedbackRequest(BaseModel):
    query_id: str
    session_id: str
    rating: int
    helpful: bool
    comment: Optional[str] = None


# ─── Query Routes ─────────────────────────────────────────────────────────────

@query_router.post("/ask", response_model=QueryResponse)
async def ask_query(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_current_user),
):
    """Main query endpoint - ask any legal question"""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if len(request.query) > 2000:
        raise HTTPException(status_code=400, detail="Query too long (max 2000 chars)")

    # Get or create session
    session_id = request.session_id or str(uuid.uuid4())
    session = await Session.find_one(Session.session_id == session_id)

    if not session:
        session = Session(
            session_id=session_id,
            user_id=str(current_user.id) if current_user else None,
            channel=request.channel,
        )
        await session.insert()

    # Get conversation history
    history = [
        {"role": t.role, "content": t.content}
        for t in session.conversation[-6:]
    ]

    # Process query
    result = await llm_service.process_query(
        query=request.query,
        session_id=session_id,
        conversation_history=history,
        channel=request.channel,
    )

    # Save to DB in background
    query_id = str(uuid.uuid4())

    async def save_query():
        try:
            # Update session
            session.conversation.append(ConversationTurn(role="user", content=request.query))
            session.conversation.append(ConversationTurn(role="assistant", content=result["response"]))
            session.updated_at = datetime.utcnow()
            await session.save()

            # Save query record
            query_doc = Query(
                user_id=str(current_user.id) if current_user else None,
                session_id=session_id,
                original_query=request.query,
                detected_language=result["detected_language"],
                category=result["category"],
                response=result["response"],
                sources=result["sources"],
                confidence_score=result["confidence_score"],
                needs_lawyer=result["needs_lawyer"],
                suggested_helplines=result["suggested_helplines"],
                processing_time_ms=result["processing_time_ms"],
                channel=request.channel,
            )
            await query_doc.insert()

            # Update user query count
            if current_user:
                current_user.query_count += 1
                current_user.last_active = datetime.utcnow()
                await current_user.save()
        except Exception as e:
            logger.error(f"Failed to save query: {e}")

    background_tasks.add_task(save_query)

    return QueryResponse(
        query_id=query_id,
        session_id=session_id,
        **result,
    )


@query_router.get("/history/{session_id}")
async def get_history(session_id: str):
    """Get conversation history for a session"""
    session = await Session.find_one(Session.session_id == session_id)
    if not session:
        return {"conversation": []}
    return {
        "session_id": session_id,
        "conversation": [
            {"role": t.role, "content": t.content, "timestamp": t.timestamp}
            for t in session.conversation
        ]
    }


@query_router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Submit feedback for a query response"""
    fb = Feedback(**feedback.dict())
    await fb.insert()
    return {"message": "Feedback recorded. Thank you!"}


# ─── Document Routes ──────────────────────────────────────────────────────────

@document_router.post("/generate")
async def generate_document(request: DocumentRequest):
    """Generate a legal document (RTI, notice, complaint etc.)"""
    valid_types = ["rti_application", "legal_notice", "consumer_complaint", "police_complaint", "labour_complaint"]
    if request.doc_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid doc_type. Must be one of: {valid_types}"
        )

    # Generate document content via LLM
    content = await llm_service.generate_document(
        doc_type=request.doc_type,
        user_details=request.user_details,
        case_details=request.case_details,
        language=request.language,
    )

    response_data = {
        "doc_type": request.doc_type,
        "content": content,
        "language": request.language,
    }

    # Generate PDF if requested
    if request.generate_pdf:
        doc_titles = {
            "rti_application": "RTI Application",
            "legal_notice": "Legal Notice",
            "consumer_complaint": "Consumer Complaint",
            "police_complaint": "Police Complaint",
            "labour_complaint": "Labour Complaint",
        }
        pdf_bytes = pdf_service.generate_legal_document(
            title=doc_titles.get(request.doc_type, "Legal Document"),
            content=content,
            doc_type=request.doc_type,
            user_name=request.user_details.get("name", ""),
        )
        # Return PDF directly
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=nyaya_{request.doc_type}_{datetime.now().strftime('%Y%m%d')}.pdf"
            }
        )

    return response_data


@document_router.post("/generate-text")
async def generate_document_text(request: DocumentRequest):
    """Generate document content as text (no PDF)"""
    content = await llm_service.generate_document(
        doc_type=request.doc_type,
        user_details=request.user_details,
        case_details=request.case_details,
        language=request.language,
    )
    return {"content": content, "doc_type": request.doc_type}


# ─── Auth Routes ──────────────────────────────────────────────────────────────

@auth_router.post("/register")
async def register(request: RegisterRequest):
    """Register new user"""
    existing = await User.find_one(User.phone == request.phone)
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already registered")

    user = User(
        name=request.name,
        phone=request.phone,
        email=request.email,
        preferred_language=request.preferred_language,
        state=request.state,
    )
    # Store hashed password in a separate collection (simplified here)
    await user.insert()

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return {
        "message": "Registration successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": str(user.id),
            "name": user.name,
            "phone": user.phone,
            "preferred_language": user.preferred_language,
        }
    }


@auth_router.post("/login")
async def login(request: LoginRequest):
    """Login with phone"""
    user = await User.find_one(User.phone == request.phone)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": str(user.id),
            "name": user.name,
            "phone": user.phone,
            "preferred_language": user.preferred_language,
        }
    }


@auth_router.get("/me")
async def get_me(user: User = Depends(require_auth)):
    return {
        "id": str(user.id),
        "name": user.name,
        "phone": user.phone,
        "email": user.email,
        "preferred_language": user.preferred_language,
        "state": user.state,
        "query_count": user.query_count,
        "created_at": user.created_at,
    }


# ─── WhatsApp Webhook ─────────────────────────────────────────────────────────

@whatsapp_router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Twilio WhatsApp webhook endpoint"""
    form_data = await request.form()
    form_dict = dict(form_data)

    twiml_response = await whatsapp_service.handle_incoming(form_dict)

    return Response(
        content=twiml_response,
        media_type="text/xml"
    )


@whatsapp_router.get("/webhook")
async def whatsapp_verify(request: Request):
    """Webhook verification"""
    return {"status": "NYAYA AI WhatsApp webhook active"}


# ─── Admin Routes ─────────────────────────────────────────────────────────────

@admin_router.get("/stats")
async def get_stats():
    """Get platform statistics"""
    total_queries = await Query.count()
    total_users = await User.count()
    total_docs = await GeneratedDocument.count()

    # Category breakdown
    from motor.motor_asyncio import AsyncIOMotorClient
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]

    return {
        "total_queries": total_queries,
        "total_users": total_users,
        "documents_generated": total_docs,
        "platform": "NYAYA AI",
        "version": "1.0.0",
    }


@admin_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "NYAYA AI Backend",
        "timestamp": datetime.utcnow().isoformat(),
    }
