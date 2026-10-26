import os
from pathlib import Path
from typing import List, Dict, Any
from pypdf import PdfReader

class DocumentPage:
    def __init__(self, content: str, metadata: Dict[str, Any]):
        self.content = content
        self.metadata = metadata

    def __repr__(self):
        return f"<DocumentPage doc={self.metadata.get('source')} page={self.metadata.get('page')}>"

class DocumentLoader:
    """Extracts text and metadata from PDF and text documents."""

    @staticmethod
    def load_pdf(file_path: Path, filename: str = None) -> List[DocumentPage]:
        pages: List[DocumentPage] = []
        name = filename or file_path.name
        
        reader = PdfReader(str(file_path))
        total_pages = len(reader.pages)
        
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                pages.append(
                    DocumentPage(
                        content=text,
                        metadata={
                            "source": name,
                            "page": idx + 1,
                            "total_pages": total_pages,
                            "file_type": "pdf"
                        }
                    )
                )
        return pages

    @staticmethod
    def load_text(file_path: Path, filename: str = None) -> List[DocumentPage]:
        pages: List[DocumentPage] = []
        name = filename or file_path.name

        # Try UTF-8 first, fallback to latin-1
        text = ""
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    text = f.read()
                break
            except (UnicodeDecodeError, Exception):
                continue

        text = text.strip()
        if text:
            # If the text file has multiple sections marked by standard dividers, we can track pages
            # Or treat as single document with page 1
            pages.append(
                DocumentPage(
                    content=text,
                    metadata={
                        "source": name,
                        "page": 1,
                        "total_pages": 1,
                        "file_type": "text"
                    }
                )
            )
        return pages

    @classmethod
    def load_document(cls, file_path: Path, filename: str = None) -> List[DocumentPage]:
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            return cls.load_pdf(file_path, filename)
        elif ext in [".txt", ".md", ".log", ".csv", ".json"]:
            return cls.load_text(file_path, filename)
        else:
            # Attempt text load as default fallback
            try:
                return cls.load_text(file_path, filename)
            except Exception as e:
                raise ValueError(f"Unsupported file format: {ext}. Error: {str(e)}")
