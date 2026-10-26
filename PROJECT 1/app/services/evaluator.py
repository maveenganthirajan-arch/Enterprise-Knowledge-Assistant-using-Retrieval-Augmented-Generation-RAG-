import json
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.sql_models import EvaluationResultModel
from app.models.schemas import EvaluationResponse
from app.services.rag_engine import rag_engine

BENCHMARK_CASES = [
    {
        "id": "tc_01",
        "question": "How many days of paid annual leave are employees entitled to?",
        "expected_source": "HR_Policy_Handbook.txt",
        "expected_keywords": ["20", "days", "annual leave", "paid"],
        "category": "factual_in_context",
        "should_answer": True
    },
    {
        "id": "tc_02",
        "question": "What is the password rotation policy for corporate systems?",
        "expected_source": "Cloud_Infrastructure_Security_Manual.txt",
        "expected_keywords": ["90", "days", "password", "rotation"],
        "category": "factual_in_context",
        "should_answer": True
    },
    {
        "id": "tc_03",
        "question": "What was the enterprise cloud software revenue in Q3?",
        "expected_source": "Q3_Financial_Performance_Report.txt",
        "expected_keywords": ["48.5", "million", "revenue"],
        "category": "factual_in_context",
        "should_answer": True
    },
    {
        "id": "tc_04",
        "question": "What are the rules for remote work and home office stipends?",
        "expected_source": "HR_Policy_Handbook.txt",
        "expected_keywords": ["remote", "stipend", "500", "home office"],
        "category": "factual_in_context",
        "should_answer": True
    },
    {
        "id": "tc_05",
        "question": "What is the procedure for reporting high severity security incidents?",
        "expected_source": "Cloud_Infrastructure_Security_Manual.txt",
        "expected_keywords": ["severity", "incident", "15", "minutes", "security"],
        "category": "factual_in_context",
        "should_answer": True
    },
    {
        "id": "tc_06",
        "question": "What is the company's reimbursement policy for personal travel to Mars?",
        "expected_source": None,
        "expected_keywords": [],
        "category": "hallucination_test",
        "should_answer": False
    },
    {
        "id": "tc_07",
        "question": "Does the company provide company-issued hoverboards to all interns?",
        "expected_source": None,
        "expected_keywords": [],
        "category": "hallucination_test",
        "should_answer": False
    },
    {
        "id": "tc_08",
        "question": "What is the secret recipe for the cafeteria double-chocolate cookies?",
        "expected_source": None,
        "expected_keywords": [],
        "category": "hallucination_test",
        "should_answer": False
    }
]

class EvaluationService:
    """Automated benchmark test suite testing Correctness, Retrieval Precision/Recall, Hallucination Risks, and Latency."""

    @staticmethod
    def run_benchmark(db: Optional[Session] = None, benchmark_name: str = "Enterprise RAG Evaluation Suite") -> EvaluationResponse:
        results_detail = []
        total_tests = len(BENCHMARK_CASES)
        
        correct_count = 0
        hallucination_prevention_count = 0
        total_unanswerable = 0
        total_precision_samples = []
        total_recall_samples = []
        response_times = []

        for case in BENCHMARK_CASES:
            q = case["question"]
            start_t = time.perf_counter()
            resp = rag_engine.answer_query(question=q, db=None) # Don't log benchmark queries into user logs
            elapsed_ms = (time.perf_counter() - start_t) * 1000
            response_times.append(elapsed_ms)

            is_correct = False
            hallucination_guarded = False
            precision = 0.0
            recall = 0.0

            if case["should_answer"]:
                # In-context question: check if answered and contains expected keywords
                if resp.status == "answered":
                    ans_lower = resp.answer.lower()
                    matched_kws = [kw for kw in case["expected_keywords"] if kw.lower() in ans_lower]
                    if len(matched_kws) >= 1:
                        is_correct = True
                        correct_count += 1

                # Retrieval precision & recall
                retrieved_sources = [s.document_name for s in resp.sources]
                if retrieved_sources:
                    target = case["expected_source"]
                    target_stem = target.split(".")[0].lower() if target else ""
                    relevant_in_retrieved = sum(1 for s in retrieved_sources if target_stem and target_stem in s.lower())
                    precision = relevant_in_retrieved / len(retrieved_sources)
                    recall = 1.0 if relevant_in_retrieved > 0 else 0.0
                    total_precision_samples.append(precision)
                    total_recall_samples.append(recall)
            else:
                # Hallucination test case: should NOT answer or declare insufficient evidence
                total_unanswerable += 1
                if resp.status == "insufficient_evidence" or "insufficient evidence" in resp.answer.lower():
                    is_correct = True
                    correct_count += 1
                    hallucination_guarded = True
                    hallucination_prevention_count += 1
                else:
                    hallucination_guarded = False

            results_detail.append({
                "test_id": case["id"],
                "question": case["question"],
                "category": case["category"],
                "should_answer": case["should_answer"],
                "actual_status": resp.status,
                "answer_snippet": resp.answer[:150] + ("..." if len(resp.answer) > 150 else ""),
                "is_correct": is_correct,
                "hallucination_guarded": hallucination_guarded if not case["should_answer"] else None,
                "retrieval_precision": round(precision, 2) if case["should_answer"] else None,
                "sources_retrieved": [s.document_name for s in resp.sources],
                "latency_ms": round(elapsed_ms, 2)
            })

        correctness_score = round(correct_count / total_tests, 4) if total_tests > 0 else 0.0
        hallucination_rate = round(hallucination_prevention_count / total_unanswerable, 4) if total_unanswerable > 0 else 1.0
        avg_precision = round(sum(total_precision_samples) / len(total_precision_samples), 4) if total_precision_samples else 0.0
        avg_recall = round(sum(total_recall_samples) / len(total_recall_samples), 4) if total_recall_samples else 0.0
        avg_latency = round(sum(response_times) / len(response_times), 2) if response_times else 0.0

        eval_record = EvaluationResultModel(
            benchmark_name=benchmark_name,
            total_tests=total_tests,
            correctness_score=correctness_score,
            retrieval_precision=avg_precision,
            retrieval_recall=avg_recall,
            hallucination_prevention_rate=hallucination_rate,
            average_response_time_ms=avg_latency,
            details_json=json.dumps(results_detail)
        )

        if db:
            db.add(eval_record)
            db.commit()
            db.refresh(eval_record)

        return EvaluationResponse(
            id=eval_record.id,
            benchmark_name=benchmark_name,
            total_tests=total_tests,
            correctness_score=correctness_score,
            retrieval_precision=avg_precision,
            retrieval_recall=avg_recall,
            hallucination_prevention_rate=hallucination_rate,
            average_response_time_ms=avg_latency,
            details=results_detail,
            created_at=eval_record.created_at
        )

evaluator = EvaluationService()
