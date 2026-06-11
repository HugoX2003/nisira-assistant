# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**NISIRA Assistant** is a full-stack RAG (Retrieval-Augmented Generation) chat application. Users ask questions; the system retrieves relevant document chunks, passes them to an LLM, and returns grounded answers. It has a Django REST API backend and a React SPA frontend, with optional Google Drive document sync.

## Common Commands

### Backend (Django)
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver          # dev server on :8000
python manage.py test               # run all tests
python manage.py test api           # run tests for a single app
python manage.py createsuperuser
```

### Frontend (React / Create React App)
```bash
cd frontend
npm install
npm start                           # dev server on :3000
npm run build
npm test                            # run tests
```

### Docker (local development — MySQL)
```bash
docker-compose up                   # starts db + backend + frontend
docker-compose down
docker-compose exec backend python manage.py migrate
```

### Docker (production — PostgreSQL + pgvector + Nginx)
```bash
docker-compose -f docker-compose.production.yml up
```

## Architecture

```
frontend/  (React SPA, react-router-dom)
backend/
  api/            Django app — auth, conversations, messages, ratings, document serving
  rag_system/     RAG pipeline — document processing, embeddings, vector store, Drive sync
  core/           Django project — settings, URLs, WSGI/ASGI
nginx/            Reverse proxy config (production)
docs/             Architecture, deployment, and troubleshooting docs
```

### Request flow

1. React frontend authenticates via JWT (`/api/token/`).
2. Chat messages POST to `/api/chat/` → `api/views.py` → `rag_system`.
3. RAG pipeline: embed query → vector search (ChromaDB or pgvector) → retrieve top-k chunks → call LLM with context → return answer + source references.
4. Frontend renders markdown response and clickable source citations with PDF page-level navigation.

### RAG system internals (`backend/rag_system/`)

| Sub-package | Role |
|---|---|
| `rag_engine/pipeline.py` | Orchestrates the full retrieve → generate flow |
| `document_processing/` | Parsers for PDF (PyPDF2 + pdfplumber), DOCX, PPTX, XLSX, TXT |
| `embeddings/embedding_manager.py` | `all-mpnet-base-v2` sentence-transformers (768-dim) |
| `vector_store/` | Dual backend: ChromaDB (local) / PostgreSQL pgvector (production) |
| `drive_sync/drive_manager.py` | Google Drive polling and document ingestion |
| `config.py` | Single source of truth for LLM provider, chunking strategy, embedding model |

### LLM providers

Configured in `backend/rag_system/config.py` and `.env`. Supported:
- **Gemini 2.0 Flash** (default, via `google-generativeai`)
- OpenRouter
- Groq

### Database strategy

- **Local dev**: MySQL (via `docker-compose.yml`)
- **Production**: PostgreSQL + pgvector extension (via `docker-compose.production.yml` or Railway/DigitalOcean)
- `core/settings.py` auto-detects the database from environment variables.

### Authentication

JWT (`djangorestframework-simplejwt`). Access + refresh token pair. Frontend stores tokens in `localStorage` and attaches them as `Authorization: Bearer <token>` headers via `frontend/src/services/api.js`.

### Frontend routing

React Router v7 with real URL paths (`/chat`, `/admin`, `/conversation/:id`). `vercel.json` and `Procfile` rewrite all paths to `index.html` for SPA support.

## Key Environment Variables

Backend `.env`:
```
SECRET_KEY, DEBUG, ALLOWED_HOSTS
DATABASE_URL  (or DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT)
GOOGLE_API_KEY            # Gemini
GOOGLE_DRIVE_FOLDER_ID    # optional Drive sync
GOOGLE_CREDENTIALS_JSON   # service account JSON
CORS_ALLOWED_ORIGINS
```

Frontend `.env`:
```
REACT_APP_API_URL   # e.g. http://localhost:8000
```

## Admin Panel

The React admin panel (`/admin`) calls dedicated API endpoints to:
- Ingest / re-embed documents
- Browse vector store chunks
- View system metrics and RAGAS evaluation results
- Trigger Google Drive sync

The Django admin (`/django-admin/`) is separate and handles low-level model management.

## Document Serving

Uploaded documents are stored via `PostgresFileStore` (binary in DB). Served at `/api/documents/<slug>/` with a random public slug. The frontend renders PDFs in an iframe and can deep-link to a specific page using the chunk's `page_number` metadata.
