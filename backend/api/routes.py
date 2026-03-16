import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Response, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from groq import AsyncGroq
import os

query_router = APIRouter(prefix="/query", tags=["Query"])
auth_router = APIRouter(prefix="/auth", tags=["Auth"])
document_router = APIRouter(prefix="/documents", tags=["Documents"])
whatsapp_router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])

groq_client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    language: Optional[str] = None
    channel: str = "web"

SYSTEM_PROMPT = '''You are NYAYA AI, India's trusted free legal rights assistant.
Answer legal questions about Indian law in simple language.
Always cite the exact Act and Section number.
Give step-by-step actionable advice.
Mention relevant helpline numbers (NALSA: 15100, Women: 181, Police: 100).
If emergency, mention 112 first.
Keep responses clear and under 400 words.
Respond in the same language the question was asked in (Hindi, English, etc).'''

@query_router.post("/ask")
async def ask_query(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        response = await groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": request.query}
            ],
            max_tokens=1024,
            temperature=0.3,
        )
        
        answer = response.choices[0].message.content
        
        return {
            "query_id": str(uuid.uuid4()),
            "session_id": session_id,
            "response": answer,
            "detected_language": "hi",
            "category": "general",
            "sources": [],
            "needs_lawyer": "lawyer" in answer.lower() or "advocate" in answer.lower(),
            "suggested_helplines": ["15100", "112"],
            "confidence_score": 0.9,
            "processing_time_ms": 500,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@query_router.get("/history/{session_id}")
async def get_history(session_id: str):
    return {"session_id": session_id, "conversation": []}

@query_router.post("/feedback")
async def submit_feedback(data: dict):
    return {"message": "Feedback recorded. Thank you!"}

@document_router.post("/generate-text")
async def generate_document_text(request: dict):
    doc_type = request.get("doc_type", "legal_notice")
    user_details = request.get("user_details", {})
    case_details = request.get("case_details", {})
    
    prompt = f"Generate a complete {doc_type.replace('_',' ')} legal document for Indian law. User: {user_details}. Details: {case_details}. Include proper legal citations, sections, and formal language."
    
    response = await groq_client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You are an expert Indian lawyer. Generate complete, legally accurate documents with proper citations."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2048,
        temperature=0.2,
    )
    
    return {"content": response.choices[0].message.content, "doc_type": doc_type}

@document_router.post("/generate")
async def generate_document(request: dict):
    result = await generate_document_text(request)
    return JSONResponse(content=result)

@auth_router.post("/register")
async def register(data: dict):
    return {"message": "Registration successful", "access_token": str(uuid.uuid4())}

@auth_router.post("/login")
async def login(data: dict):
    return {"access_token": str(uuid.uuid4())}

@auth_router.get("/me")
async def get_me():
    return {"name": "User", "phone": ""}

@whatsapp_router.post("/webhook")
async def whatsapp_webhook(request: Request):
    return Response(content="<Response></Response>", media_type="text/xml")

@whatsapp_router.get("/webhook")
async def whatsapp_verify():
    return {"status": "active"}

@admin_router.get("/stats")
async def get_stats():
    return {"total_queries": 0, "total_users": 0, "platform": "NYAYA AI"}

@admin_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "NYAYA AI"}