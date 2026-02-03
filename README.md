# DocuBot - AI Documentation Generator

DocuBot auto-generates and maintains README and API documentation for GitHub repositories.
It analyzes code locally, stores structured metadata, builds embeddings for search, and
uses local or free LLMs to create docs and answer questions about the codebase.

## Features

- Parse Python code (functions, classes, docstrings, signatures)
- Index code into Qdrant for search and chat (RAG)
- Generate README and API docs via Ollama (DeepSeek Coder) with Groq fallback
- Incremental re-indexing via GitHub webhooks
- Async background processing with Celery + Redis

## Architecture (High Level)

1) **Quick file tree** - GitHub API for fast UI rendering
2) **Deep analysis** - local clone in a worker for parsing and indexing
3) **Cache** - store results in Postgres to avoid repeated work

## Quick Start (Local)

```bash
make setup
make dev
```

Access the app at http://localhost:3000

## Environment

Create `backend/.env` with at least:

```
DATABASE_URL=postgresql://docubot:docubot@postgres:5432/docubot
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
SECRET_KEY=change-me
GITHUB_WEBHOOK_SECRET=change-me
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

Optional:
- `OLLAMA_URL` (default `http://ollama:11434`)
- `OLLAMA_MODEL` (default `llama3.1:8b`)

## API Documentation (Summary)

Base URL: `http://localhost:8000/api/v1`

### Auth
- `POST /auth/register` - create user
- `POST /auth/login` - get JWT token
- `GET /auth/me` - current user

### Repositories
- `GET /repos` - list repos
- `POST /repos` - add repo (GitHub URL)
- `GET /repos/{repo_id}` - repo details
- `POST /repos/{repo_id}/analyze` - trigger analysis task
- `GET /repos/{repo_id}/analyze/{task_id}` - task status

### Docs
- `POST /docs/generate` - trigger README/API doc generation
- `GET /docs/generate/{task_id}` - task status
- `GET /docs/{repo_id}?doc_type=readme|api` - latest docs

### Chat
- `POST /chat` - ask a question about repo code
- `GET /chat/history/{session_id}` - chat history
- `POST /chat/stream` - stream responses (SSE)

### Webhooks
- `POST /webhooks/github` - GitHub webhook endpoint (push, pull_request)

## Deployment Guide

### Docker Compose (Recommended)

1) Build images:
   ```bash
   docker compose build
   ```

2) Start services:
   ```bash
   docker compose up -d
   ```

3) Run migrations:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

4) Verify health:
   ```bash
   curl http://localhost:8000/health
   ```

### Ollama Models (Local)

Pull the recommended models:
```bash
docker compose exec ollama ollama pull deepseek-coder:6.7b
docker compose exec ollama ollama pull llama3.1:8b
```

## Notes

- Docs generation uses **Ollama** (DeepSeek Coder) and falls back to **Groq** if Ollama is unavailable.
- Vector search uses **Qdrant** and embeddings from **sentence-transformers** (`all-MiniLM-L6-v2`).
