import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def initialize_system():
    init_db()

def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "Enterprise Knowledge Assistant" in data["project"]

def test_load_sample_documents_endpoint():
    resp = client.post("/api/documents/load-samples")
    assert resp.status_code == 200
    data = resp.json()
    assert "documents" in data

def test_list_documents_endpoint():
    resp = client.get("/api/documents")
    assert resp.status_code == 200
    docs = resp.json()
    assert isinstance(docs, list)

def test_ask_question_api():
    req_body = {
        "question": "What is the password rotation policy for corporate systems?",
        "top_k": 3
    }
    resp = client.post("/api/chat", json=req_body)
    assert resp.status_code == 200
    data = resp.json()
    assert "query_id" in data
    assert "answer" in data
    assert "status" in data
    assert "response_time_ms" in data

def test_feedback_submission_api():
    # Ask a question first
    q_resp = client.post("/api/chat", json={"question": "What are the core working hours?"})
    assert q_resp.status_code == 200
    query_id = q_resp.json()["query_id"]

    # Submit positive feedback
    fb_body = {
        "query_id": query_id,
        "rating": 1,
        "comment": "Accurate response with exact source citation.",
        "feedback_type": "thumbs_up"
    }
    fb_resp = client.post("/api/feedback", json=fb_body)
    assert fb_resp.status_code == 200
    fb_data = fb_resp.json()
    assert fb_data["query_id"] == query_id
    assert fb_data["rating"] == 1

def test_evaluation_benchmark_api():
    resp = client.post("/api/evaluate", json={"benchmark_type": "full"})
    assert resp.status_code == 200
    data = resp.json()
    assert "correctness_score" in data
    assert "retrieval_precision" in data
    assert "hallucination_prevention_rate" in data
    assert "average_response_time_ms" in data
    assert data["total_tests"] > 0

def test_analytics_api():
    resp = client.get("/api/analytics")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_documents" in data
    assert "total_queries" in data
    assert "satisfaction_rate" in data
