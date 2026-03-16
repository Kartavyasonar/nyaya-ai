"""
NYAYA AI â€” RAG Pipeline
Hybrid retrieval: Dense (FAISS) + Sparse (BM25) + Reranking
"""
import os
import pickle
import asyncio
from typing import List, Tuple, Optional
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder
from langchain.text_splitter import RecursiveCharacterTextSplitter
from loguru import logger

from config import settings


class LegalDocument:
    """Represents a chunk of legal text with metadata"""
    def __init__(
        self,
        content: str,
        act: str,
        section: Optional[str] = None,
        section_title: Optional[str] = None,
        doc_type: str = "law",
        language: str = "en",
        source_url: Optional[str] = None,
    ):
        self.content = content
        self.act = act
        self.section = section
        self.section_title = section_title
        self.doc_type = doc_type  # law, judgment, scheme, procedure
        self.language = language
        self.source_url = source_url

    def to_dict(self):
        return {
            "content": self.content,
            "act": self.act,
            "section": self.section,
            "section_title": self.section_title,
            "doc_type": self.doc_type,
            "language": self.language,
            "source_url": self.source_url,
        }


class NyayaRAGPipeline:
    """
    Hybrid RAG Pipeline with:
    - Dense retrieval via FAISS + multilingual sentence embeddings
    - Sparse retrieval via BM25
    - Cross-encoder reranking
    - Metadata filtering
    """

    def __init__(self):
        self.embedding_model = None
        self.reranker = None
        self.faiss_index = None
        self.documents: List[LegalDocument] = []
        self.bm25 = None
        self.tokenized_corpus = []
        self.index_path = Path(settings.FAISS_INDEX_PATH)
        self._initialized = False

    async def initialize(self):
        """Load models and index on startup"""
        if self._initialized:
            return

        logger.info("ðŸ§  Initializing RAG pipeline...")

        # Load multilingual embedding model (supports all 22 Indian languages)
        logger.info("Loading embedding model...")
        self.embedding_model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        # Load cross-encoder for reranking
        logger.info("Loading reranker model...")
        self.reranker = None

        # Load or create FAISS index
        if self.index_path.with_suffix(".faiss").exists():
            logger.info("Loading existing FAISS index...")
            await self._load_index()
        else:
            logger.warning("No FAISS index found. Building from scratch...")
            await self._build_initial_index()

        self._initialized = True
        logger.info(f"âœ… RAG pipeline ready. {len(self.documents)} documents indexed.")

    async def _build_initial_index(self):
        """Build FAISS index from legal data files"""
        from rag.data_loader import LegalDataLoader
        loader = LegalDataLoader()
        documents = await loader.load_all()
        await self.index_documents(documents)

    async def index_documents(self, documents: List[LegalDocument]):
        """Add documents to FAISS and BM25 index"""
        if not documents:
            logger.warning("No documents to index")
            return

        logger.info(f"Indexing {len(documents)} documents...")

        # Generate embeddings in batches
        texts = [doc.content for doc in documents]
        batch_size = 64
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self.embedding_model.encode(
                batch,
                normalize_embeddings=True,
                show_progress_bar=True
            )
            all_embeddings.append(embeddings)

        embeddings_matrix = np.vstack(all_embeddings).astype(np.float32)

        # Build FAISS index (Inner Product = cosine similarity on normalized vectors)
        dim = embeddings_matrix.shape[1]
        if len(documents) > 10000:
            # IVF index for large corpora
            nlist = 256
            quantizer = faiss.IndexFlatIP(dim)
            self.faiss_index = faiss.IndexIVFFlat(quantizer, dim, nlist)
            self.faiss_index.train(embeddings_matrix)
        else:
            self.faiss_index = faiss.IndexFlatIP(dim)

        self.faiss_index.add(embeddings_matrix)
        self.documents.extend(documents)

        # Build BM25 index
        self.tokenized_corpus = [doc.content.lower().split() for doc in self.documents]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

        # Save index
        await self._save_index()
        logger.info(f"âœ… Indexed {len(documents)} documents")

    async def retrieve(
        self,
        query: str,
        top_k: int = 8,
        category_filter: Optional[str] = None,
        language: str = "en",
    ) -> List[Tuple[LegalDocument, float]]:
        """
        Hybrid retrieval: Dense + BM25 + Reranking
        Returns list of (document, score) tuples
        """
        if not self._initialized:
            await self.initialize()

        # Step 1: Dense retrieval via FAISS
        query_embedding = self.embedding_model.encode(
            [query], normalize_embeddings=True
        ).astype(np.float32)

        k_dense = min(top_k * 4, len(self.documents))
        scores, indices = self.faiss_index.search(query_embedding, k_dense)

        dense_results = {
            idx: float(score)
            for idx, score in zip(indices[0], scores[0])
            if idx >= 0
        }

        # Step 2: BM25 sparse retrieval
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        top_bm25_indices = np.argsort(bm25_scores)[::-1][:k_dense]

        bm25_results = {
            int(idx): float(bm25_scores[idx])
            for idx in top_bm25_indices
            if bm25_scores[idx] > 0
        }

        # Step 3: Reciprocal Rank Fusion
        all_indices = set(dense_results.keys()) | set(bm25_results.keys())
        rrf_scores = {}

        dense_ranked = sorted(dense_results.keys(), key=lambda x: dense_results[x], reverse=True)
        bm25_ranked = sorted(bm25_results.keys(), key=lambda x: bm25_results[x], reverse=True)

        for idx in all_indices:
            dense_rank = dense_ranked.index(idx) + 1 if idx in dense_ranked else k_dense
            bm25_rank = bm25_ranked.index(idx) + 1 if idx in bm25_ranked else k_dense
            rrf_scores[idx] = (1 / (60 + dense_rank)) + (1 / (60 + bm25_rank))

        # Step 4: Category filter
        if category_filter:
            rrf_scores = {
                idx: score for idx, score in rrf_scores.items()
                if self.documents[idx].doc_type == category_filter
                or category_filter in self.documents[idx].act.lower()
            }

        # Get top candidates for reranking
        top_candidates = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:top_k * 2]

        if not top_candidates:
            return []

        # Step 5: Cross-encoder reranking
        candidate_docs = [self.documents[idx] for idx in top_candidates]
        pairs = [[query, doc.content] for doc in candidate_docs]

        rerank_scores = self.reranker.predict(pairs)
        reranked = sorted(
            zip(candidate_docs, rerank_scores.tolist()),
            key=lambda x: x[1],
            reverse=True
        )

        return reranked[:top_k]

    async def _save_index(self):
        """Persist FAISS index and documents to disk"""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.faiss_index, str(self.index_path.with_suffix(".faiss")))
        with open(self.index_path.with_suffix(".pkl"), "wb") as f:
            pickle.dump({
                "documents": self.documents,
                "tokenized_corpus": self.tokenized_corpus,
            }, f)
        logger.info(f"Index saved to {self.index_path}")

    async def _load_index(self):
        """Load persisted FAISS index"""
        self.faiss_index = faiss.read_index(str(self.index_path.with_suffix(".faiss")))
        with open(self.index_path.with_suffix(".pkl"), "rb") as f:
            data = pickle.load(f)
            self.documents = data["documents"]
            self.tokenized_corpus = data["tokenized_corpus"]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        logger.info(f"Loaded index with {len(self.documents)} documents")


# Singleton instance
rag_pipeline = NyayaRAGPipeline()
