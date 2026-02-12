# BSK Assistant

RAG-based assistant for BSK operators with:
- FastAPI backend (`api/`)
- Streamlit frontend (`app.py`, `ui/`)
- MongoDB for metadata/chat/logs
- ChromaDB for vector storage
- Ollama for local LLM + embeddings

## Python Version
- Recommended: **Python 3.12**

## Prerequisites
Install and run these before starting the app:

1. **Python 3.12**
2. **MongoDB** (local or remote)
3. **Ollama**
4. (Optional) **Git**

### Ollama models required
```bash
ollama pull llama3.1:latest
ollama pull mxbai-embed-large:latest
```

## Environment Variables
Create `.env` in project root:

```env
OLLAMA_BASE_URL=http://localhost:11434

MONGODB_URI=mongodb://localhost:27017
MONGO_DB_NAME=bsk_assistant

ENVIRONMENT=development
LOG_LEVEL=INFO

CHUNK_SIZE=1000
CHUNK_OVERLAP=350
CHROMA_PERSIST_DIRECTORY=./db/chroma
```

## Local Setup
From project root:

### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux/macOS
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Initialize Services
Run one-time initialization checks/setup:

```bash
python scripts/initialize_system.py
```

This will:
- initialize MongoDB collections/indexes
- initialize Chroma
- verify Ollama availability and required models
- run startup health checks

## Run the API (FastAPI)
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Useful URLs:
- API root: `http://localhost:8000/`
- Swagger docs: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`

## Run the Streamlit App
In a second terminal (same venv):

```bash
streamlit run app.py
```

Default URL: `http://localhost:8501`

## API Endpoints (v1)
Base prefix: `/api/v1`

- `GET /api/v1/` - health check
- `POST /api/v1/chat` - create chat
- `POST /api/v1/chat/query` - send query
- `GET /api/v1/chat/{chat_id}` - get chat history
- `DELETE /api/v1/chat/{chat_id}` - delete chat
- `POST /api/v1/documents/upload` - upload PDF (+ metadata)
- `GET /api/v1/documents` - list documents
- `DELETE /api/v1/documents/{filename}` - delete document
- `GET /api/v1/services` - list services
- `POST /api/v1/services` - add service
- `GET /api/v1/logs` - list logs (optional filters)

## Quick Health Checks
```bash
python scripts/check_ollama.py
python scripts/initialize_mongodb.py
python scripts/initialize_chroma.py
```

## Docker (Optional)
If using Docker Compose:

```bash
docker compose up --build
```

Notes:
- `docker-compose.yml` maps API to `http://localhost:8001`
- Update `OLLAMA_BASE_URL` in compose to your reachable Ollama host

## Troubleshooting
- **Ollama not reachable**: verify `ollama serve` is running and `OLLAMA_BASE_URL` is correct.
- **Model not found**: run the two `ollama pull ...` commands above.
- **MongoDB connection failed**: verify MongoDB is running and `MONGODB_URI` is reachable.
- **No answers from RAG**: ensure PDFs were uploaded and indexed in vector store.
