import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from database import connect_db, disconnect_db
from api.routes import query_router, auth_router, document_router, whatsapp_router, admin_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting NYAYA AI...")
    await connect_db()
    logger.info("NYAYA AI is ready to serve justice!")
    yield
    await disconnect_db()

app = FastAPI(title="NYAYA AI", version="1.0.0", docs_url="/api/docs", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(document_router, prefix="/api/v1")
app.include_router(whatsapp_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"service": "NYAYA AI", "status": "running", "message": "Justice for every Indian"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "NYAYA AI"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)