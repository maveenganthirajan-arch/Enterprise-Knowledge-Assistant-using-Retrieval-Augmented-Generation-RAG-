import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from app.config import settings
from app.services.chunker import TextChunk

class VectorStore:
    """Manages vector indexing and similarity retrieval using FAISS with cosine similarity."""

    def __init__(self, storage_dir: Path = None):
        self.storage_dir = storage_dir or settings.VECTOR_STORE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "faiss.index"
        self.metadata_file = self.storage_dir / "chunks_metadata.json"
        self.vectors_file = self.storage_dir / "vectors.npy"

        self.index = None
        self.vectors: Optional[np.ndarray] = None
        self.chunks: List[Dict[str, Any]] = []
        self._faiss_available = False

        self._check_faiss()
        self.load()

    def _check_faiss(self):
        try:
            import faiss
            self.faiss = faiss
            self._faiss_available = True
        except ImportError:
            self._faiss_available = False
            print("[VectorStore] FAISS not found, using NumPy cosine similarity index.")

    def _rebuild_faiss_index(self):
        if self._faiss_available and self.vectors is not None and len(self.vectors) > 0:
            dim = self.vectors.shape[1]
            self.index = self.faiss.IndexFlatIP(dim)
            self.index.add(self.vectors)
        else:
            self.index = None

    def add_chunks(self, chunks: List[TextChunk], embeddings: np.ndarray):
        """Adds text chunks and their normalized embedding vectors into the index."""
        if len(chunks) == 0:
            return

        # Ensure L2 normalization for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized_embeddings = (embeddings / norms).astype(np.float32)

        if self.vectors is not None and len(self.vectors) > 0:
            self.vectors = np.vstack([self.vectors, normalized_embeddings])
        else:
            self.vectors = normalized_embeddings

        # Store metadata
        for chunk in chunks:
            self.chunks.append({
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
                "metadata": chunk.metadata
            })

        self._rebuild_faiss_index()
        self.save()

    def search(self, query_embedding: np.ndarray, top_k: int = 4, threshold: float = 0.0) -> List[Tuple[Dict[str, Any], float]]:
        """Searches for top_k most similar chunks, filtered by minimum cosine similarity threshold."""
        if len(self.chunks) == 0:
            return []

        # Normalize query vector
        norm = np.linalg.norm(query_embedding)
        if norm > 0:
            q_vec = (query_embedding / norm).astype(np.float32).reshape(1, -1)
        else:
            q_vec = query_embedding.astype(np.float32).reshape(1, -1)

        actual_k = min(top_k, len(self.chunks))
        results: List[Tuple[Dict[str, Any], float]] = []

        if self._faiss_available and self.index is not None:
            scores, indices = self.index.search(q_vec, actual_k)
            for score, idx in zip(scores[0], indices[0]):
                if idx != -1 and idx < len(self.chunks):
                    sim_score = float(score)
                    if sim_score >= threshold:
                        results.append((self.chunks[idx], sim_score))
        elif self.vectors is not None:
            sims = np.dot(self.vectors, q_vec.T).flatten()
            top_indices = np.argsort(sims)[::-1][:actual_k]
            for idx in top_indices:
                sim_score = float(sims[idx])
                if sim_score >= threshold:
                    results.append((self.chunks[idx], sim_score))

        return results

    def delete_document(self, filename: str) -> int:
        """Deletes all chunks belonging to a document and rebuilds the index."""
        initial_count = len(self.chunks)
        retained_chunks = []
        indices_to_keep = []

        for idx, chunk in enumerate(self.chunks):
            if chunk["metadata"].get("source") != filename:
                retained_chunks.append(chunk)
                indices_to_keep.append(idx)

        deleted_count = initial_count - len(retained_chunks)
        if deleted_count > 0:
            self.chunks = retained_chunks
            if self.vectors is not None and len(indices_to_keep) > 0:
                self.vectors = self.vectors[indices_to_keep]
            else:
                self.vectors = None
            self._rebuild_faiss_index()
            self.save()

        return deleted_count

    def clear(self):
        """Clears all vectors and metadata."""
        self.index = None
        self.vectors = None
        self.chunks = []
        if self.index_file.exists():
            self.index_file.unlink()
        if self.metadata_file.exists():
            self.metadata_file.unlink()
        if self.vectors_file.exists():
            self.vectors_file.unlink()

    def count(self) -> int:
        return len(self.chunks)

    def save(self):
        """Persists FAISS index, embedding matrix, and metadata to disk."""
        if self.vectors is not None:
            np.save(self.vectors_file, self.vectors)
        if self._faiss_available and self.index is not None:
            self.faiss.write_index(self.index, str(self.index_file))

        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, indent=2)

    def load(self):
        """Loads FAISS index and metadata from disk if available."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
            except Exception as e:
                print(f"[VectorStore] Failed to load metadata: {e}")
                self.chunks = []

        if self.vectors_file.exists():
            try:
                self.vectors = np.load(self.vectors_file)
                self._rebuild_faiss_index()
                return
            except Exception as e:
                print(f"[VectorStore] Failed to load vectors from npy: {e}")

        if self._faiss_available and self.index_file.exists():
            try:
                self.index = self.faiss.read_index(str(self.index_file))
            except Exception as e:
                print(f"[VectorStore] Failed to read FAISS index: {e}")
                self.index = None

vector_store = VectorStore()
