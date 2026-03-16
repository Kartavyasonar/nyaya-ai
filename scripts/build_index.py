"""
NYAYA AI — Index Builder Script
Run this ONCE before deploying to build the FAISS vector index.

Usage:
    cd backend
    python scripts/build_index.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from rag.pipeline import rag_pipeline
from rag.data_loader import LegalDataLoader


async def build():
    logger.info("=" * 60)
    logger.info("NYAYA AI — Building Legal Knowledge Index")
    logger.info("=" * 60)

    logger.info("Step 1: Initializing embedding models...")
    # Load models without loading existing index
    from sentence_transformers import SentenceTransformer, CrossEncoder
    rag_pipeline.embedding_model = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    )
    rag_pipeline.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    logger.info("✅ Models loaded")

    logger.info("Step 2: Loading legal documents...")
    loader = LegalDataLoader()
    documents = await loader.load_all()
    logger.info(f"✅ Loaded {len(documents)} legal chunks")

    logger.info("Step 3: Building FAISS index...")
    await rag_pipeline.index_documents(documents)
    logger.info("✅ FAISS index built and saved")

    logger.info("=" * 60)
    logger.info(f"🎉 Index ready! {len(documents)} chunks indexed.")
    logger.info(f"Index saved to: {rag_pipeline.index_path}")
    logger.info("You can now start the backend server.")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(build())
