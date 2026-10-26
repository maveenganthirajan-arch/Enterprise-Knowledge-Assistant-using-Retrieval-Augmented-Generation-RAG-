import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.sql_models import DocumentModel, QueryLogModel, FeedbackModel, EvaluationResultModel
from app.models.schemas import EvaluationRequest, EvaluationResponse, AnalyticsResponse
from app.services.evaluator import evaluator
from app.services.vector_store import vector_store

router = APIRouter(prefix="/api", tags=["Evaluation & Analytics"])

@router.post("/evaluate", response_model=EvaluationResponse)
def run_evaluation_benchmark(request: EvaluationRequest = None, db: Session = Depends(get_db)):
    """
    Run automated benchmark tests assessing:
    - Answer correctness
    - Retrieval relevance (Precision & Recall)
    - Hallucination risk prevention (insufficient evidence detection)
    - Response latency
    Stores results into SQL.
    """
    benchmark_name = "Enterprise RAG Automated Benchmark"
    if request and request.benchmark_type:
        benchmark_name = f"Enterprise RAG Benchmark ({request.benchmark_type.title()})"

    eval_result = evaluator.run_benchmark(db=db, benchmark_name=benchmark_name)
    return eval_result

@router.get("/evaluate/latest", response_model=EvaluationResponse)
def get_latest_evaluation(db: Session = Depends(get_db)):
    """Retrieve the most recent evaluation benchmark from SQL."""
    latest = db.query(EvaluationResultModel).order_by(EvaluationResultModel.created_at.desc()).first()
    if not latest:
        raise HTTPException(status_code=404, detail="No evaluation results found. Run /api/evaluate first.")

    details = json.loads(latest.details_json or "[]")
    return EvaluationResponse(
        id=latest.id,
        benchmark_name=latest.benchmark_name,
        total_tests=latest.total_tests,
        correctness_score=latest.correctness_score,
        retrieval_precision=latest.retrieval_precision,
        retrieval_recall=latest.retrieval_recall,
        hallucination_prevention_rate=latest.hallucination_prevention_rate,
        average_response_time_ms=latest.average_response_time_ms,
        details=details,
        created_at=latest.created_at
    )

@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(db: Session = Depends(get_db)):
    """System-wide analytics, document statistics, and user satisfaction metrics."""
    total_docs = db.query(DocumentModel).count()
    total_chunks = vector_store.count()
    total_queries = db.query(QueryLogModel).count()
    insufficient_queries = db.query(QueryLogModel).filter(QueryLogModel.status == "insufficient_evidence").count()
    answered_queries = total_queries - insufficient_queries

    # Latency average
    avg_latency = db.query(func.avg(QueryLogModel.response_time_ms)).scalar() or 0.0

    # Feedback stats
    positive_feedbacks = db.query(FeedbackModel).filter(FeedbackModel.rating > 0).count()
    negative_feedbacks = db.query(FeedbackModel).filter(FeedbackModel.rating <= 0).count()
    total_feedbacks = positive_feedbacks + negative_feedbacks
    satisfaction_rate = round((positive_feedbacks / total_feedbacks) * 100, 2) if total_feedbacks > 0 else 100.0

    return AnalyticsResponse(
        total_documents=total_docs,
        total_chunks=total_chunks,
        total_queries=total_queries,
        answered_queries=answered_queries,
        insufficient_evidence_queries=insufficient_queries,
        avg_response_time_ms=round(float(avg_latency), 2),
        positive_feedback_count=positive_feedbacks,
        negative_feedback_count=negative_feedbacks,
        satisfaction_rate=satisfaction_rate
    )
