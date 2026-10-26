import uvicorn
import os
from app.config import settings

if __name__ == "__main__":
    print(f"Starting {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}...")
    print(f"Vector Store Directory: {settings.VECTOR_STORE_DIR}")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Embedding Provider: {settings.EMBEDDING_PROVIDER}")
    print(f"LLM Provider: {settings.LLM_PROVIDER}")
    print("Application URL: http://localhost:8000")
    print("Interactive API Docs: http://localhost:8000/docs")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
