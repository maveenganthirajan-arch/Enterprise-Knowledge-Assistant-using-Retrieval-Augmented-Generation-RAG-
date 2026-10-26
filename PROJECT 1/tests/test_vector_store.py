import pytest
import numpy as np
from pathlib import Path
from app.services.vector_store import VectorStore
from app.services.chunker import TextChunk

def test_vector_store_indexing_and_search(tmp_path):
    store = VectorStore(storage_dir=tmp_path)
    store.clear()

    # Create dummy chunks
    chunks = [
        TextChunk(chunk_id="c1", content="Cloud security standards require AWS multi-AZ.", metadata={"source": "sec.pdf", "page": 1}),
        TextChunk(chunk_id="c2", content="Employees receive 20 days of paid annual leave.", metadata={"source": "hr.pdf", "page": 1}),
        TextChunk(chunk_id="c3", content="Q3 financial software revenue reached 48.5 million.", metadata={"source": "fin.pdf", "page": 1}),
    ]

    # Generate synthetic 4-dimensional normalized vectors
    embeddings = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
    ], dtype=np.float32)

    store.add_chunks(chunks, embeddings)
    assert store.count() == 3

    # Query closest to vector 1 (c2: HR)
    query_vec = np.array([0.0, 0.99, 0.0, 0.0], dtype=np.float32)
    results = store.search(query_vec, top_k=2, threshold=0.5)

    assert len(results) >= 1
    top_chunk, score = results[0]
    assert top_chunk["chunk_id"] == "c2"
    assert "paid annual leave" in top_chunk["content"]
    assert score > 0.9

    # Test delete
    deleted = store.delete_document("hr.pdf")
    assert deleted == 1
    assert store.count() == 2
