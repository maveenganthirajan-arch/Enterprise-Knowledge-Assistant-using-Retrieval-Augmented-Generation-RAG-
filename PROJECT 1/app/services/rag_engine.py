import time
import uuid
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.models.sql_models import DocumentModel, QueryLogModel
from app.models.schemas import QueryResponse, SourceCitation
from app.services.document_loader import DocumentLoader
from app.services.chunker import DocumentChunker
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store
from app.services.llm_service import llm_service

class RAGEngine:
    """Orchestrates end-to-end Ingestion, Vector Search, Prompt Augmentation, and Grounded Generation."""

    def __init__(self):
        self.chunker = DocumentChunker(chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)

    def ingest_document(self, file_path: Path, filename: str, db: Optional[Session] = None) -> DocumentModel:
        """Parses, chunks, embeds, indexes into Vector DB, and records in SQL."""
        # 1. Load document
        pages = DocumentLoader.load_document(file_path, filename=filename)
        if not pages:
            raise ValueError(f"No readable content could be extracted from {filename}")

        # 2. Chunk document
        chunks = self.chunker.chunk_pages(pages, doc_id=filename)
        if not chunks:
            raise ValueError(f"No chunks generated from {filename}")

        # 3. Generate embeddings
        chunk_texts = [c.content for c in chunks]
        embeddings = embedding_service.embed_documents(chunk_texts)

        # 4. Add to Vector Store
        vector_store.add_chunks(chunks, embeddings)

        # 5. Record in SQL
        total_chars = sum(len(c.content) for c in chunks)
        doc_record = DocumentModel(
            filename=filename,
            file_type=file_path.suffix.lstrip(".").lower() or "txt",
            file_size=file_path.stat().st_size if file_path.exists() else 0,
            chunk_count=len(chunks),
            char_count=total_chars
        )

        if db:
            db.add(doc_record)
            db.commit()
            db.refresh(doc_record)

        return doc_record

    def answer_query(
        self,
        question: str,
        session_id: Optional[str] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        db: Optional[Session] = None
    ) -> QueryResponse:
        """Runs the RAG query pipeline, tracks performance, and stores query in SQL."""
        start_time = time.perf_counter()
        k = top_k or settings.TOP_K_RESULTS
        thresh = similarity_threshold if similarity_threshold is not None else settings.SIMILARITY_THRESHOLD

        # 1. Embed query
        query_vec = embedding_service.embed_query(question)

        # 2. Vector search
        retrieved_raw = vector_store.search(query_vec, top_k=k, threshold=thresh)

        # 3. Generate answer
        answer, status, confidence = llm_service.generate_answer(question, retrieved_raw)

        # 4. Compute latency
        response_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # 5. Format source citations
        citations: List[SourceCitation] = []
        citations_for_db = []
        for chunk, score in retrieved_raw:
            cit = SourceCitation(
                document_name=chunk["metadata"].get("source", "Document"),
                page=chunk["metadata"].get("page", 1),
                chunk_id=chunk.get("chunk_id", ""),
                snippet=chunk.get("content", "")[:250] + ("..." if len(chunk.get("content", "")) > 250 else ""),
                similarity_score=round(float(score), 4)
            )
            citations.append(cit)
            citations_for_db.append(cit.model_dump())

        query_id = str(uuid.uuid4())

        # 6. Save in SQL
        if db:
            log_entry = QueryLogModel(
                id=query_id,
                session_id=session_id,
                question=question,
                answer=answer,
                status=status,
                confidence_score=confidence,
                retrieved_chunks=json.dumps(citations_for_db),
                response_time_ms=response_time_ms,
                llm_provider=llm_service.provider,
                model_name=llm_service.model_name
            )
            db.add(log_entry)
            db.commit()

        return QueryResponse(
            query_id=query_id,
            session_id=session_id,
            question=question,
            answer=answer,
            status=status,
            confidence_score=round(confidence, 4),
            sources=citations,
            response_time_ms=response_time_ms,
            llm_provider=llm_service.provider,
            model_name=llm_service.model_name
        )

rag_engine = RAGEngine()
