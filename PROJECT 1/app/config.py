import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

class Settings:
    BASE_DIR: Path = BASE_DIR
    PROJECT_NAME: str = "Enterprise Knowledge Assistant (RAG)"
    PROJECT_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # Storage paths
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    VECTOR_STORE_DIR: Path = DATA_DIR / "vector_store"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'enterprise_rag.db'}")

    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock").lower()
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    # Embedding Settings
    # options: "sentence-transformers", "openai", "gemini", "tfidf"
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "tfidf").lower()
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # Chunking & Retrieval
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "4"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.15"))

    # System Prompt for Context-Grounded QA
    SYSTEM_PROMPT: str = (
        "You are an expert Enterprise Knowledge Assistant. Your job is to answer employee and stakeholder "
        "questions strictly using the retrieved context passages provided below.\n\n"
        "Guidelines:\n"
        "1. GROUNDING: Base your answer EXCLUSIVELY on the provided context passages. Do not extrapolate, "
        "assume, or use outside knowledge.\n"
        "2. CITATIONS: Whenever stating a fact or policy, cite the source document name and page or section "
        "(e.g., [Source: HR_Policy.pdf, Page: 2]).\n"
        "3. INSUFFICIENT EVIDENCE: If the context does not contain enough information to answer the question, "
        "state clearly: 'Based on the company documents provided, there is insufficient evidence to answer this question.' "
        "Do not guess or fabricate policies.\n"
        "4. TONE: Professional, concise, helpful, and accurate."
    )

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
