import os
import math
import numpy as np
from typing import List
from app.config import settings

class EmbeddingService:
    """Provides vector embeddings using SentenceTransformers, OpenAI, Gemini, or a TF-IDF dense fallback."""

    def __init__(self, provider: str = None, model_name: str = None):
        self.provider = (provider or settings.EMBEDDING_PROVIDER).lower()
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._st_model = None
        self._openai_client = None
        self._gemini_configured = False
        self._initialized = False

    def _ensure_initialized(self):
        if self._initialized:
            return
        self._initialized = True
        self._initialize_provider()

    def _initialize_provider(self):
        if self.provider == "sentence-transformers":
            try:
                from sentence_transformers import SentenceTransformer
                self._st_model = SentenceTransformer(self.model_name)
            except Exception as e:
                print(f"[Warning] Could not initialize SentenceTransformers ({e}). Falling back to tfidf provider.")
                self.provider = "tfidf"
        elif self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                self.provider = "tfidf"
            else:
                try:
                    from openai import OpenAI
                    self._openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                except Exception as e:
                    self.provider = "tfidf"
        elif self.provider == "gemini":
            if not settings.GEMINI_API_KEY:
                self.provider = "tfidf"
            else:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=settings.GEMINI_API_KEY)
                    self._gemini_configured = True
                except Exception as e:
                    self.provider = "tfidf"

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        self._ensure_initialized()
        if not texts:
            return np.empty((0, self.get_dimension()), dtype=np.float32)

        if self.provider == "sentence-transformers" and self._st_model is not None:
            embeddings = self._st_model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
            return np.array(embeddings, dtype=np.float32)

        elif self.provider == "openai" and self._openai_client is not None:
            resp = self._openai_client.embeddings.create(input=texts, model=self.model_name or "text-embedding-3-small")
            embeddings = [item.embedding for item in resp.data]
            arr = np.array(embeddings, dtype=np.float32)
            # L2 normalize
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            return arr / norms

        elif self.provider == "gemini" and self._gemini_configured:
            import google.generativeai as genai
            embeddings = []
            for t in texts:
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=t,
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])
            arr = np.array(embeddings, dtype=np.float32)
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            return arr / norms

        else:
            return self._tfidf_dense_embed(texts)

    def embed_query(self, query: str) -> np.ndarray:
        return self.embed_documents([query])[0]

    def get_dimension(self) -> int:
        if self.provider == "sentence-transformers" and self._st_model is not None:
            return self._st_model.get_sentence_embedding_dimension()
        elif self.provider == "openai":
            return 1536
        elif self.provider == "gemini":
            return 768
        return 384  # TF-IDF dense projection dimension

    def _tfidf_dense_embed(self, texts: List[str]) -> np.ndarray:
        """Deterministic hashing + character/word n-gram vectorizer with L2 normalization."""
        dim = 384
        vectors = []
        for text in texts:
            vec = np.zeros(dim, dtype=np.float32)
            tokens = text.lower().replace("\n", " ").split()
            if not tokens:
                vectors.append(vec)
                continue
            for i, token in enumerate(tokens):
                h1 = hash(token) % dim
                vec[h1] += 1.0
                # Bi-grams
                if i < len(tokens) - 1:
                    bigram = f"{token}_{tokens[i+1]}"
                    h2 = hash(bigram) % dim
                    vec[h2] += 1.5
            # Substring hashing for keywords
            for word in tokens:
                for length in (3, 4):
                    if len(word) >= length:
                        sub = word[:length]
                        h3 = hash(sub) % dim
                        vec[h3] += 0.5
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec)
        return np.array(vectors, dtype=np.float32)

embedding_service = EmbeddingService()
