# Enterprise Knowledge Assistant

An AI-powered Enterprise Knowledge Assistant built using **Retrieval-Augmented Generation (RAG), LangChain, FAISS, FastAPI, SQL persistence, and a web-based user interface**. The application enables users to upload documents, ask questions about their contents, and receive context-grounded answers with source citations.

## Features

- **Document Processing:** Parse multi-page PDF documents and plain-text files.
- **Intelligent Chunking:** Split documents into manageable text chunks with overlap to preserve contextual continuity.
- **Vector Search:** Use FAISS for efficient embedding indexing and similarity-based document retrieval.
- **Persistent Vector Store:** Save and reload the vector index from disk.
- **Retrieval-Augmented Generation:** Generate answers using retrieved document context.
- **Grounded Responses:** Provide source citations and reject questions when the available evidence is insufficient.
- **Similarity Thresholding:** Filter retrieval results based on configured similarity criteria.
- **Precision Scoring:** Support relevance-oriented scoring of retrieved results.
- **Document Synchronization:** Manage updates to the vector store as document data changes.
- **REST API:** Expose application functionality through FastAPI endpoints.
- **SQL Persistence:** Persist application data, feedback, or analytics in a relational database.
- **Evaluation Support:** Access the latest evaluation results through an API endpoint.
- **Web Interface:** Interact with the assistant through a browser-based UI.
- **API Documentation:** Explore and test endpoints through automatically generated Swagger documentation.
- **Automated Testing:** Validate document processing, retrieval, grounding, persistence, and API functionality using pytest.

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| RAG framework | LangChain |
| Vector database / index | FAISS |
| API framework | FastAPI |
| Document formats | PDF, TXT |
| Relational persistence | SQL |
| Testing framework | pytest |
| API documentation | Swagger UI / OpenAPI |
| Frontend | HTML, CSS, JavaScript |

## Architecture

The application follows a retrieval-augmented generation pipeline.

```text
                 ┌──────────────────────┐
                 │     Web Interface    │
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │      FastAPI         │
                 │    API Endpoints     │
                 └──────────┬───────────┘
                            │
             ┌──────────────▼──────────────┐
             │     Document Processing     │
             │      PDF / TXT Parsing      │
             └──────────────┬──────────────┘
                            │
                 ┌──────────▼───────────┐
                 │   Text Chunking      │
                 │   With Overlap       │
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │ Embedding Generation │
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │    FAISS Index       │
                 │  Vector Persistence  │
                 └──────────┬───────────┘
                            │
User Question ──► Similarity Search
                            │
                 ┌──────────▼───────────┐
                 │ Context & Relevance  │
                 │      Filtering       │
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │   Grounded Answer    │
                 │ + Source Citations   │
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │   Chat Response      │
                 └──────────────────────┘

          SQL Database ◄──► Application Data
          Evaluation    ◄──► Evaluation API
          Feedback      ◄──► Feedback API
```

*The diagram represents the intended high-level workflow; exact implementation details may vary.*

## Project Structure

A suggested project structure is shown below. Adjust the paths to match the actual repository.

```text
enterprise-knowledge-assistant/
├── run.py
├── requirements.txt
├── README.md
├── tests/
│   └── ...
├── static/
│   ├── js/
│   │   └── app.js
│   └── ...
├── templates/
│   └── ...
├── data/
│   └── ...
├── vector_store/
│   └── ...
└── ...
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd enterprise-knowledge-assistant
```

Replace `<your-repository-url>` with the actual Git repository URL.

### 2. Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Ensure that `requirements.txt` contains the dependencies used by the project.

### 4. Configure environment variables

Configure the model provider, API credentials, database connection, embedding model, and other settings required by your implementation.

If the application uses environment variables, create a `.env` file using the variable names expected by the code. Do not commit API keys, credentials, or other secrets to Git.

### 5. Run the application

```bash
python run.py
```

Open the application in your browser:

- **Web interface:** `http://127.0.0.1:8000/`
- **Swagger API documentation:** `http://127.0.0.1:8000/docs`
- **OpenAPI schema:** `http://127.0.0.1:8000/openapi.json`

These URLs assume the server is configured to use port `8000`. If `run.py` specifies another port, use that port instead.

## API Endpoints

The following endpoints are present in the reported application logs and tests.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Serve the web interface |
| GET | `/api/documents` | Retrieve document information |
| POST | `/api/chat` | Submit a question and receive an answer |
| POST | `/api/feedback` | Submit feedback |
| GET | `/api/analytics` | Retrieve analytics |
| GET | `/api/evaluate/latest` | Retrieve the latest evaluation results |
| GET | `/docs` | Open interactive Swagger documentation |

For the precise request schemas, response formats, and available HTTP methods, inspect the generated OpenAPI documentation at `/docs`.

## How to Use the Application

1. Start the FastAPI application.
2. Open the web interface in a browser.
3. Upload or ingest supported documents using the application's implemented document workflow.
4. Allow the document-processing pipeline to parse, chunk, embed, and index the content.
5. Ask a question related to the indexed documents.
6. Review the generated answer and its source citations.
7. If the evidence is insufficient, the assistant should return an appropriate insufficient-evidence response rather than inventing an answer.
8. Submit feedback and review analytics or evaluation results where supported.

## Running Tests

Run the automated test suite from the project root:

```bash
pytest -v
```

### Latest reported test results

**13 tests passed in 3.45 seconds.**

The reported test coverage includes:

| Area | Verified behavior |
|---|---|
| Document processing | Parsing multi-page PDFs and text files with page extraction |
| Chunking | Text chunking and overlap |
| FAISS | Vector indexing and similarity search |
| Persistence | Saving and reloading the vector index |
| Grounding | Answers based on available context with source citations |
| Anti-hallucination | Insufficient-evidence handling for out-of-scope questions |
| FastAPI | Document, chat, feedback, and analytics endpoints |
| SQL | Database persistence functionality |

These results reflect the reported test run; they do not establish that every production scenario has been tested.

## Recent Git History

The following commits represent the reported development history, with the latest commit listed first.

```text
60222e5 Add favicon handler to prevent 404 in web browser
f7cf5ff Optimize vector store synchronization, similarity threshold, and precision scoring
18659d9 Complete Enterprise Knowledge Assistant using RAG (LangChain, FAISS, FastAPI, SQL, Evaluation, Web UI)
```

### Recent improvements

**Favicon handling**

Added a favicon handler to prevent unnecessary browser requests from generating a `404` response.

**Vector store synchronization and retrieval**

Optimized vector store synchronization, similarity threshold handling, and precision scoring. The exact behavioral improvements should be confirmed by inspecting the commit diff.

**Core application implementation**

Introduced the main Enterprise Knowledge Assistant functionality, including RAG, FAISS, FastAPI, SQL persistence, evaluation, and the web UI.

Inspect the commit changes with:

```bash
git show --stat f7cf5ff
git show f7cf5ff
```

## Grounding and Reliability

The assistant is designed to improve response reliability by grounding answers in retrieved document content.

Key principles include:

- Retrieve relevant document chunks before generating an answer.
- Apply similarity or relevance criteria to retrieval results.
- Include source references where supported.
- Return an insufficient-evidence response when the retrieved context does not support an answer.
- Persist the vector index so it can be reused across application restarts.

A passing test suite is useful evidence of correctness, but retrieval quality should also be evaluated on representative documents, ambiguous questions, missing information, and conflicting sources.

## Future Enhancements

Potential future improvements include:

- Support for additional file formats such as DOCX and HTML.
- More comprehensive retrieval evaluation using precision, recall, and ranking metrics.
- Hybrid retrieval combining keyword and vector search.
- Reranking retrieved passages using a dedicated relevance model.
- Authentication and role-based access control.
- Document-level permissions and tenant isolation.
- Background processing for large document collections.
- Monitoring, structured logging, and performance metrics.
- Automated tests for concurrent updates and vector-store recovery.
- Deployment using Docker and a production-grade ASGI server.

## Security Considerations

- Keep API credentials and database secrets out of source control.
- Validate uploaded files and enforce file-size limits.
- Restrict access to sensitive documents.
- Treat retrieved document text as untrusted input.
- Configure authentication and authorization before exposing the service publicly.
- Review the security implications of loading persisted FAISS indexes and other serialized data.
- Avoid logging confidential document contents or sensitive user queries unnecessarily.

## License

Add the license applicable to this project before distributing it publicly.

## Author

Developed as an Enterprise Knowledge Assistant project demonstrating document ingestion, vector search, retrieval-augmented generation, API development, persistence, evaluation, and web integration.
