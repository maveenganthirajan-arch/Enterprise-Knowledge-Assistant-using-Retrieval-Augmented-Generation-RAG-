import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.sql_models import DocumentModel
from app.models.schemas import DocumentResponse, DocumentUploadResponse
from app.services.rag_engine import rag_engine
from app.services.vector_store import vector_store

router = APIRouter(prefix="/api/documents", tags=["Documents"])

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".csv", ".json", ".log"}

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process PDF and text documents into the RAG vector store."""
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    uploaded_docs: List[DocumentModel] = []
    
    for file in files:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
            )

        # Save to disk
        dest_path = settings.UPLOAD_DIR / file.filename
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Ingest, chunk, embed, and store in vector db + SQL
        try:
            doc_record = rag_engine.ingest_document(dest_path, filename=file.filename, db=db)
            uploaded_docs.append(doc_record)
        except Exception as e:
            if dest_path.exists():
                dest_path.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process and index document '{file.filename}': {str(e)}"
            )

    return DocumentUploadResponse(
        message=f"Successfully processed and indexed {len(uploaded_docs)} document(s).",
        documents=[DocumentResponse.model_validate(d) for d in uploaded_docs]
    )

@router.get("", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    """Retrieve all ingested documents and their index statistics."""
    docs = db.query(DocumentModel).order_by(DocumentModel.created_at.desc()).all()
    return [DocumentResponse.model_validate(d) for d in docs]

@router.delete("/{doc_id}")
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    """Remove a document from the SQL catalog and clean up its vector embeddings."""
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    filename = doc.filename

    # Delete from SQL
    db.delete(doc)
    db.commit()

    # Delete from Vector Store
    deleted_chunks = vector_store.delete_document(filename)

    # Delete file from upload directory
    file_path = settings.UPLOAD_DIR / filename
    if file_path.exists():
        file_path.unlink()

    return {
        "message": f"Document '{filename}' successfully deleted.",
        "deleted_chunks": deleted_chunks
    }

@router.post("/load-samples")
def load_sample_documents_endpoint(db: Session = Depends(get_db)):
    """Convenience endpoint to index the pre-packaged sample enterprise documents."""
    sample_dir = settings.BASE_DIR / "sample_data"
    sample_files = [
        "HR_Policy_Handbook.pdf",
        "Cloud_Infrastructure_Security_Manual.pdf",
        "Q3_Financial_Performance_Report.pdf",
        "HR_Policy_Handbook.txt",
        "Cloud_Infrastructure_Security_Manual.txt",
        "Q3_Financial_Performance_Report.txt"
    ]

    ingested = []
    for s_name in sample_files:
        src = sample_dir / s_name
        if src.exists():
            # Check if already in DB
            exists = db.query(DocumentModel).filter(DocumentModel.filename == s_name).first()
            if not exists:
                doc = rag_engine.ingest_document(src, filename=s_name, db=db)
                ingested.append(doc)

    return {
        "message": f"Ingested {len(ingested)} sample documents.",
        "documents": [DocumentResponse.model_validate(d) for d in ingested]
    }

