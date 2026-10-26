import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.sql_models import QueryLogModel
from app.models.schemas import QueryRequest, QueryResponse, SourceCitation
from app.services.rag_engine import rag_engine

router = APIRouter(prefix="/api/chat", tags=["Conversational AI / RAG"])

@router.post("", response_model=QueryResponse)
def ask_question(request: QueryRequest, db: Session = Depends(get_db)):
    """
    Ask a question against ingested company documents.
    Returns context-grounded answer with source references and confidence score.
    """
    try:
        response = rag_engine.answer_query(
            question=request.question,
            session_id=request.session_id,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            db=db
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")

@router.get("/history/{session_id}", response_model=List[QueryResponse])
def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    """Retrieve chat history for conversational sessions."""
    logs = db.query(QueryLogModel).filter(QueryLogModel.session_id == session_id).order_by(QueryLogModel.created_at.asc()).all()
    
    results: List[QueryResponse] = []
    for log in logs:
        try:
            raw_sources = json.loads(log.retrieved_chunks or "[]")
            citations = [SourceCitation(**s) for s in raw_sources]
        except Exception:
            citations = []

        results.append(QueryResponse(
            query_id=log.id,
            session_id=log.session_id,
            question=log.question,
            answer=log.answer,
            status=log.status,
            confidence_score=log.confidence_score,
            sources=citations,
            response_time_ms=log.response_time_ms,
            llm_provider=log.llm_provider,
            model_name=log.model_name
        ))
    return results

@router.get("/logs", response_model=List[QueryResponse])
def get_recent_query_logs(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    """Retrieve recent queries and answers logged in SQL."""
    logs = db.query(QueryLogModel).order_by(QueryLogModel.created_at.desc()).limit(limit).all()
    
    results: List[QueryResponse] = []
    for log in logs:
        try:
            raw_sources = json.loads(log.retrieved_chunks or "[]")
            citations = [SourceCitation(**s) for s in raw_sources]
        except Exception:
            citations = []

        results.append(QueryResponse(
            query_id=log.id,
            session_id=log.session_id,
            question=log.question,
            answer=log.answer,
            status=log.status,
            confidence_score=log.confidence_score,
            sources=citations,
            response_time_ms=log.response_time_ms,
            llm_provider=log.llm_provider,
            model_name=log.model_name
        ))
    return results
