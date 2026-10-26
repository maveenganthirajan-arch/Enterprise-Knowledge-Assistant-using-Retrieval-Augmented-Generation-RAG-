import re
from typing import List, Dict, Any
from app.services.document_loader import DocumentPage

class TextChunk:
    def __init__(self, chunk_id: str, content: str, metadata: Dict[str, Any]):
        self.chunk_id = chunk_id
        self.content = content
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "metadata": self.metadata
        }

class DocumentChunker:
    """Splits documents into semantically coherent chunks with overlap and provenance tracking."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text_recursively(self, text: str, separators: List[str] = None) -> List[str]:
        if separators is None:
            separators = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]

        if len(text) <= self.chunk_size or not separators:
            return [text.strip()] if text.strip() else []

        sep = separators[0]
        splits = text.split(sep) if sep else list(text)

        chunks: List[str] = []
        current_chunk = ""

        for part in splits:
            candidate = (current_chunk + sep + part) if current_chunk else part
            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                if len(part) > self.chunk_size and len(separators) > 1:
                    sub_chunks = self.split_text_recursively(part, separators[1:])
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    # Apply overlap from previous part if possible
                    overlap_prefix = current_chunk[-self.chunk_overlap:] if current_chunk and self.chunk_overlap > 0 else ""
                    current_chunk = (overlap_prefix + " " + part).strip()

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return [c for c in chunks if c]

    def chunk_pages(self, pages: List[DocumentPage], doc_id: str = None) -> List[TextChunk]:
        """Chunks a list of DocumentPages, maintaining exact page provenance."""
        all_chunks: List[TextChunk] = []
        chunk_idx = 0

        for page in pages:
            raw_splits = self.split_text_recursively(page.content)
            for split_text in raw_splits:
                if not split_text.strip():
                    continue

                c_id = f"{doc_id or page.metadata.get('source', 'doc')}_p{page.metadata.get('page', 1)}_c{chunk_idx}"
                metadata = {
                    **page.metadata,
                    "chunk_index": chunk_idx,
                    "char_count": len(split_text)
                }
                all_chunks.append(TextChunk(chunk_id=c_id, content=split_text, metadata=metadata))
                chunk_idx += 1

        return all_chunks
