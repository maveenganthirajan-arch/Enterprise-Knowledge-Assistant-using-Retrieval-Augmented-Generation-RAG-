import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(32), nullable=False)
    file_size = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    char_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)

class QueryLogModel(Base):
    __tablename__ = "queries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(64), nullable=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    status = Column(String(32), default="answered")  # "answered", "insufficient_evidence", "error"
    confidence_score = Column(Float, default=0.0)
    retrieved_chunks = Column(Text, default="[]")    # JSON serialized list of source citations
    response_time_ms = Column(Float, default=0.0)
    llm_provider = Column(String(64), default="")
    model_name = Column(String(64), default="")
    created_at = Column(DateTime, default=utc_now)

    feedback = relationship("FeedbackModel", back_populates="query", cascade="all, delete-orphan")

class FeedbackModel(Base):
    __tablename__ = "feedbacks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    query_id = Column(String(36), ForeignKey("queries.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 for positive, -1 or 0 for negative, or 1-5 scale
    feedback_type = Column(String(32), default="thumbs_up") # "thumbs_up", "thumbs_down", "issue"
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    query = relationship("QueryLogModel", back_populates="feedback")

class EvaluationResultModel(Base):
    __tablename__ = "evaluation_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    benchmark_name = Column(String(128), default="Enterprise RAG Benchmark")
    total_tests = Column(Integer, default=0)
    correctness_score = Column(Float, default=0.0)             # Fraction of correct answers
    retrieval_precision = Column(Float, default=0.0)           # Relevant chunks retrieved / retrieved chunks
    retrieval_recall = Column(Float, default=0.0)              # Relevant chunks retrieved / total relevant chunks
    hallucination_prevention_rate = Column(Float, default=0.0) # Correct refusals on unanswerable questions
    average_response_time_ms = Column(Float, default=0.0)
    details_json = Column(Text, default="{}")                  # Detailed per-case results
    created_at = Column(DateTime, default=utc_now)
