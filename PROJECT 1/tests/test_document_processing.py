import pytest
from pathlib import Path
from app.services.document_loader import DocumentLoader, DocumentPage
from app.services.chunker import DocumentChunker

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"

def test_load_text_document():
    txt_path = SAMPLE_DIR / "HR_Policy_Handbook.txt"
    pages = DocumentLoader.load_text(txt_path)
    assert len(pages) >= 1
    assert "HUMAN RESOURCES POLICY HANDBOOK" in pages[0].content
    assert pages[0].metadata["source"] == "HR_Policy_Handbook.txt"
    assert pages[0].metadata["file_type"] == "text"

def test_load_pdf_document():
    pdf_path = SAMPLE_DIR / "HR_Policy_Handbook.pdf"
    pages = DocumentLoader.load_pdf(pdf_path)
    assert len(pages) == 2
    assert "HR Policy Handbook" in pages[0].content
    assert pages[0].metadata["page"] == 1
    assert pages[1].metadata["page"] == 2
    assert pages[0].metadata["file_type"] == "pdf"

def test_chunker_splitting_and_overlap():
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    pages = [
        DocumentPage(
            content="This is the first sentence. This is the second sentence of the test document that should be split into multiple chunks properly.",
            metadata={"source": "test.txt", "page": 1}
        )
    ]
    chunks = chunker.chunk_pages(pages, doc_id="test")
    assert len(chunks) > 1
    for c in chunks:
        assert c.chunk_id.startswith("test_p1_c")
        assert c.metadata["source"] == "test.txt"
        assert c.metadata["page"] == 1
        assert len(c.content) > 0
