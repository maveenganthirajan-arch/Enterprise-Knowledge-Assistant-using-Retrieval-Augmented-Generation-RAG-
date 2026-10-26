from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.sql_models import FeedbackModel, QueryLogModel
from app.models.schemas import FeedbackRequest, FeedbackResponse

router = APIRouter(prefix="/api/feedback", tags=["User Feedback"])

@router.post("", response_model=FeedbackResponse)
def submit_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    """Submit user feedback (thumbs up / thumbs down / comment) for a specific query response."""
    # Verify query exists
    query = db.query(QueryLogModel).filter(QueryLogModel.id == request.query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Referenced query not found in database.")

    feedback_entry = FeedbackModel(
        query_id=request.query_id,
        rating=request.rating,
        feedback_type=request.feedback_type or ("thumbs_up" if request.rating > 0 else "thumbs_down"),
        comment=request.comment
    )
    db.add(feedback_entry)
    db.commit()
    db.refresh(feedback_entry)

    return FeedbackResponse.model_validate(feedback_entry)

@router.get("", response_model=List[FeedbackResponse])
def list_feedback(db: Session = Depends(get_db)):
    """List all stored user feedback logs."""
    feedbacks = db.query(FeedbackModel).order_by(FeedbackModel.created_at.desc()).all()
    return [FeedbackResponse.model_validate(f) for f in feedbacks]
