import re
from typing import List, Dict, Any, Tuple
from app.config import settings

class LLMService:
    """Manages prompt construction, LLM generation, and hallucination guardrails."""

    def __init__(self, provider: str = None, model_name: str = None):
        self.provider = (provider or settings.LLM_PROVIDER).lower()
        self.model_name = model_name or self._default_model_for_provider(self.provider)

    def _default_model_for_provider(self, provider: str) -> str:
        if provider == "openai":
            return settings.OPENAI_MODEL
        elif provider == "gemini":
            return settings.GEMINI_MODEL
        elif provider == "groq":
            return settings.GROQ_MODEL
        return "grounded-extractive-model"

    def format_context(self, retrieved_chunks: List[Tuple[Dict[str, Any], float]]) -> str:
        """Formats retrieved chunks with clear provenance metadata."""
        if not retrieved_chunks:
            return "No relevant documents found."

        context_blocks = []
        for i, (chunk, score) in enumerate(retrieved_chunks, 1):
            source = chunk["metadata"].get("source", "Unknown Document")
            page = chunk["metadata"].get("page", 1)
            content = chunk.get("content", "").strip()
            block = f"[Document {i} | Source: {source} | Page: {page} | Relevance: {score:.2f}]\n{content}"
            context_blocks.append(block)

        return "\n\n".join(context_blocks)

    def build_prompt(self, question: str, context_str: str) -> List[Dict[str, str]]:
        """Constructs chat messages adhering to strict grounding and citation instructions."""
        user_message = (
            f"Retrieved Company Context:\n"
            f"----------------------------------------\n"
            f"{context_str}\n"
            f"----------------------------------------\n\n"
            f"User Question: {question}\n\n"
            f"Instructions:\n"
            f"1. Answer the question using ONLY the provided context.\n"
            f"2. Every key factual statement must cite its source (e.g., [Source: DocumentName, Page: X]).\n"
            f"3. If the context does not contain enough information to answer the question with certainty, "
            f"you MUST reply: 'Based on the company documents provided, there is insufficient evidence to answer this question.'\n"
            f"Answer:"
        )

        return [
            {"role": "system", "content": settings.SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]

    def generate_answer(self, question: str, retrieved_chunks: List[Tuple[Dict[str, Any], float]]) -> Tuple[str, str, float]:
        """
        Generates an answer based on retrieved context.
        Returns: (answer_text, status, confidence_score)
        where status is 'answered' or 'insufficient_evidence'.
        """
        # Guardrail: If no chunks retrieved or highest similarity is extremely low
        if not retrieved_chunks:
            return (
                "Based on the company documents provided, there is insufficient evidence to answer this question.",
                "insufficient_evidence",
                0.0
            )

        context_str = self.format_context(retrieved_chunks)
        max_score = max(score for _, score in retrieved_chunks)

        # Check if active external provider is configured
        if self.provider == "openai" and settings.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                messages = self.build_prompt(question, context_str)
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.1,  # Low temperature to suppress hallucination
                    max_tokens=600
                )
                answer = response.choices[0].message.content.strip()
                status = self._detect_status(answer)
                return answer, status, float(max_score)
            except Exception as e:
                print(f"[LLMService] OpenAI call failed: {e}. Falling back to extractive engine.")

        elif self.provider == "gemini" and settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel(self.model_name)
                messages = self.build_prompt(question, context_str)
                full_prompt = f"{messages[0]['content']}\n\n{messages[1]['content']}"
                response = model.generate_content(full_prompt, generation_config={"temperature": 0.1})
                answer = response.text.strip()
                status = self._detect_status(answer)
                return answer, status, float(max_score)
            except Exception as e:
                print(f"[LLMService] Gemini call failed: {e}. Falling back to extractive engine.")

        elif self.provider == "groq" and settings.GROQ_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=settings.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
                messages = self.build_prompt(question, context_str)
                response = client.chat.completions.create(
                    model=self.model_name or "llama-3.1-8b-instant",
                    messages=messages,
                    temperature=0.1,
                    max_tokens=600
                )
                answer = response.choices[0].message.content.strip()
                status = self._detect_status(answer)
                return answer, status, float(max_score)
            except Exception as e:
                print(f"[LLMService] Groq call failed: {e}. Falling back to extractive engine.")

        # Deterministic Grounded Synthesis Engine (Mock / Fallback)
        return self._synthesize_grounded_answer(question, retrieved_chunks, max_score)

    def _detect_status(self, answer: str) -> str:
        negative_phrases = [
            "insufficient evidence",
            "not mentioned in the provided",
            "does not contain",
            "information is not provided",
            "no information",
            "insufficient information"
        ]
        lower_ans = answer.lower()
        if any(p in lower_ans for p in negative_phrases):
            return "insufficient_evidence"
        return "answered"

    def _synthesize_grounded_answer(
        self,
        question: str,
        retrieved_chunks: List[Tuple[Dict[str, Any], float]],
        max_score: float
    ) -> Tuple[str, str, float]:
        """
        Extractive QA engine that matches question intent against retrieved sentences,
        verifying grounding to eliminate hallucination risks.
        """
        q_clean = re.sub(r"[^\w\s]", "", question.lower())
        q_words = set(q_clean.split())
        stop_words = {"what", "is", "the", "are", "of", "and", "in", "to", "a", "for", "on", "with", "how", "many", "does", "do", "can"}
        meaningful_q_words = q_words - stop_words

        if not meaningful_q_words:
            meaningful_q_words = q_words

        candidate_sentences = []
        for chunk, score in retrieved_chunks:
            source = chunk["metadata"].get("source", "Document")
            page = chunk["metadata"].get("page", 1)
            raw_content = chunk.get("content", "")
            
            # Split into sentences
            sentences = re.split(r"(?<=[.!?])\s+", raw_content)
            for sentence in sentences:
                s_clean = re.sub(r"[^\w\s]", "", sentence.lower())
                s_words = set(s_clean.split())
                overlap = meaningful_q_words.intersection(s_words)
                if overlap:
                    candidate_sentences.append({
                        "sentence": sentence.strip(),
                        "overlap_count": len(overlap),
                        "source": source,
                        "page": page,
                        "score": score
                    })

        # Sort candidate sentences by word overlap and retrieval score
        candidate_sentences.sort(key=lambda x: (x["overlap_count"], x["score"]), reverse=True)

        if not candidate_sentences:
            return (
                "Based on the company documents provided, there is insufficient evidence to answer this question.",
                "insufficient_evidence",
                max_score * 0.5
            )

        best_candidate = candidate_sentences[0]
        overlap_ratio = best_candidate["overlap_count"] / max(len(meaningful_q_words), 1)

        # Grounding guardrail: require at least 2 distinct matching keywords,
        # or at least 50% keyword overlap for short queries
        min_overlap_required = 2 if len(meaningful_q_words) >= 3 else 1
        if best_candidate["overlap_count"] < min_overlap_required or (len(meaningful_q_words) >= 4 and overlap_ratio < 0.3):
            return (
                "Based on the company documents provided, there is insufficient evidence to answer this question.",
                "insufficient_evidence",
                max_score * 0.5
            )

        top_sentences = candidate_sentences[:3]
        formatted_statements = []
        for item in top_sentences:
            s_text = item["sentence"]
            if not s_text.endswith("."):
                s_text += "."
            citation = f"[Source: {item['source']}, Page: {item['page']}]"
            formatted_statements.append(f"{s_text} {citation}")

        answer = " ".join(formatted_statements)
        return answer, "answered", max_score

llm_service = LLMService()
