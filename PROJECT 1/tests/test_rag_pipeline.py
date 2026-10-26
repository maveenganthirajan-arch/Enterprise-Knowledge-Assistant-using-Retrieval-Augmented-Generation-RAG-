import pytest
from pathlib import Path
from app.services.rag_engine import RAGEngine
from app.services.vector_store import vector_store
from app.database import SessionLocal, init_db

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"

@pytest.fixture(autouse=True)
def setup_rag():
    init_db()
    vector_store.clear()
    engine = RAGEngine()
    
    # Ingest HR policy document
    hr_file = SAMPLE_DIR / "HR_Policy_Handbook.txt"
    engine.ingest_document(hr_file, filename="HR_Policy_Handbook.txt")
    yield engine
    vector_store.clear()

def test_rag_answers_in_context_question(setup_rag):
    engine = setup_rag
    db = SessionLocal()
    try:
        query = "How many days of paid annual leave are employees entitled to?"
        resp = engine.answer_query(question=query, db=db)

        assert resp.status == "answered"
        assert "20" in resp.answer or "leave" in resp.answer
        assert len(resp.sources) > 0
        assert resp.sources[0].document_name == "HR_Policy_Handbook.txt"
        assert resp.response_time_ms > 0
    finally:
        db.close()

def test_rag_declares_insufficient_evidence_for_unrelated_questions(setup_rag):
    engine = setup_rag
    db = SessionLocal()
    try:
        # Question not found in company documents
        query = "What is the policy for personal rocket flights to Mars?"
        resp = engine.answer_query(question=query, db=db)

        assert resp.status == "insufficient_evidence"
        assert "insufficient evidence" in resp.answer.lower()
    finally:
        db.close()
