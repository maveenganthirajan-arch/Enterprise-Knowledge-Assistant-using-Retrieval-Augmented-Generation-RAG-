from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class SourceCitation(BaseModel):
    document_name: str
    page: Optional[int] = 1
    chunk_id: str
    snippet: str
    similarity_score: float

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=2, description="The user's question regarding company documents")
    session_id: Optional[str] = Field(None, description="Optional session/conversation ID for conversational continuity")
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Override default number of chunks retrieved")
    similarity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum similarity score")

class QueryResponse(BaseModel):
    query_id: str
    session_id: Optional[str] = None
    question: str
    answer: str
    status: str  # "answered", "insufficient_evidence", "error"
    confidence_score: float
    sources: List[SourceCitation]
    response_time_ms: float
    llm_provider: str
    model_name: str

class FeedbackRequest(BaseModel):
    query_id: str
    rating: int = Field(..., description="1 for positive / thumbs-up, -1 for negative / thumbs-down")
    comment: Optional[str] = None
    feedback_type: Optional[str] = "thumbs_up"

class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    query_id: str
    rating: int
    comment: Optional[str] = None
    feedback_type: str
    created_at: datetime

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    char_count: int
    created_at: datetime

class DocumentUploadResponse(BaseModel):
    message: str
    documents: List[DocumentResponse]

class EvaluationRequest(BaseModel):
    benchmark_type: Optional[str] = "full"

class EvaluationResponse(BaseModel):
    id: str
    benchmark_name: str
    total_tests: int
    correctness_score: float
    retrieval_precision: float
    retrieval_recall: float
    hallucination_prevention_rate: float
    average_response_time_ms: float
    details: List[Dict[str, Any]]
    created_at: datetime

class AnalyticsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    total_queries: int
    answered_queries: int
    insufficient_evidence_queries: int
    avg_response_time_ms: float
    positive_feedback_count: int
    negative_feedback_count: int
    satisfaction_rate: float
