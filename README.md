<div align="center">

# NISIRA Assistant

**Chat RAG con citas verificables sobre la documentación de NISIRA**

*Pregunta en lenguaje natural, recibe respuestas ancladas a la fuente exacta — página, chunk y documento.*

[![Django](https://img.shields.io/badge/Django-REST_Framework-092E20?style=flat-square&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![React](https://img.shields.io/badge/React_18-React_Router_7-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-local_dev-FF6F00?style=flat-square)](https://www.trychroma.com/)
[![Sentence Transformers](https://img.shields.io/badge/Embeddings-all--mpnet--base--v2-FFB000?style=flat-square)](https://www.sbert.net/)
[![Gemini](https://img.shields.io/badge/LLM-Gemini_·_OpenRouter_·_Groq-8E75B2?style=flat-square)](https://ai.google.dev/)
[![Docker](https://img.shields.io/badge/Docker_Compose-dev_+_prod-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docs.docker.com/compose)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

📖 **[Documentación completa](https://mintlify.wiki/HugoX2003/nisira-assistant/introduction)**

</div>

---

## ¿Qué es NISIRA Assistant?

NISIRA Assistant es una **aplicación RAG (Retrieval-Augmented Generation) full-stack** construida específicamente para la documentación interna de **NISIRA**, que permite a sus usuarios consultarla de forma conversacional en vez de buscar manualmente en manuales, políticas y demás documentos en PDF, Word o Excel.

El usuario escribe una pregunta en español, el sistema recupera los fragmentos más relevantes de los documentos de NISIRA ya indexados, se los pasa a un LLM y devuelve una respuesta con **citas en línea** que enlazan directamente a la página exacta del documento fuente.

> **El problema que resuelve:** buscar información dentro de la documentación de NISIRA de forma manual es lento y propenso a citar la fuente equivocada. El sistema combina búsqueda semántica y léxica con filtrado por identificador de documento para que una pregunta sobre "ISO 27001" no traiga resultados de "ISO 31000".

---

## ✨ Características

- 🔎 **Búsqueda híbrida:** combina similitud semántica por embeddings (60%) con coincidencia léxica de palabras clave (40%), con filtrado adicional por identificador de documento para evitar confundir normas o versiones similares.
- 🔀 **Multi-proveedor LLM:** cambia entre **Gemini 2.0 Flash**, **OpenRouter** y **Groq** con una sola variable de entorno (`LLM_PROVIDER`); si no hay API key configurada, el sistema cae a modo *retrieval-only*.
- 💬 **Reformulación de consultas:** resuelve preguntas de seguimiento usando el historial reciente de la conversación (p. ej. "¿Cómo se instala?" se reformula usando el tema del turno anterior).
- 🎯 **Retrieval adaptativo:** consultas de cita (p. ej. "Arias (2020)") reducen automáticamente el top-k a 3 resultados para precisión; consultas temáticas amplias recuperan más contexto.
- 📊 **Evaluación y monitoreo (RAGAS):** el panel de administración calcula latencia, Precision@k, Recall@k, *faithfulness*, tasa de alucinación y Word Error Rate; los usuarios pueden calificar respuestas y reportar problemas.
- 📁 **Sincronización con Google Drive:** ingesta automática opcional que descarga archivos nuevos o modificados, los procesa y los agrega al vector store.
- 📄 **Visor de PDF con deep-link:** las citas son clicables y abren el documento en la página exacta del chunk citado.
- 🔐 **Autenticación JWT:** access + refresh tokens, con panel de administración separado del `django-admin`.

---

## Arquitectura del Sistema

```
┌──────────────────────────────────────────────────────────────────┐
│                     Navegador del usuario                          │
│      React 18 · React Router 7 · react-markdown · visor PDF        │
└───────────────────────────────┬────────────────────────────────────┘
                        REST + JWT │
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                    backend (Django REST Framework)                 │
│   api/            auth · conversaciones · mensajes · ratings ·     │
│                    servido de documentos (slug aleatorio)          │
└───────────────────────────────┬────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                     rag_system (pipeline RAG)                      │
│  document_processing/  → PDF (PyPDF2 + pdfplumber), DOCX,          │
│                           PPTX, XLSX, TXT                          │
│  embeddings/            → all-mpnet-base-v2 (768-dim)              │
│  vector_store/          → ChromaDB (local) / pgvector (producción) │
│  rag_engine/pipeline.py → orquesta retrieve → generate             │
│  drive_sync/            → polling e ingesta desde Google Drive     │
└───────────────────────────────┬────────────────────────────────────┘
                                   │
                                   ▼
                    Gemini 2.0 Flash · OpenRouter · Groq
```

---

## Stack Tecnológico

| Capa | Tecnología | Rol |
|------|-----------|-----|
| **Frontend** | React 18 + React Router v7 | SPA, rutas reales (`/chat`, `/admin`, `/conversation/:id`) |
| **Renderizado** | react-markdown + rehype-raw + remark-gfm | Respuestas en Markdown con soporte GFM |
| **Backend** | Django REST Framework | API `/api/`, JWT, persistencia de conversaciones |
| **Auth** | djangorestframework-simplejwt | Access + refresh tokens vía `Authorization: Bearer` |
| **Embeddings** | sentence-transformers `all-mpnet-base-v2` | Vectores de 768 dimensiones |
| **Vector store (dev)** | ChromaDB | Backend local, sin infraestructura adicional |
| **Vector store (prod)** | PostgreSQL + pgvector | Backend de producción |
| **LLM** | Gemini 2.0 Flash / OpenRouter / Groq | Generación, configurable por variable de entorno |
| **Base de datos (dev)** | MySQL | Vía `docker-compose.yml` |
| **Base de datos (prod)** | PostgreSQL | Vía `docker-compose.production.yml` / Railway / DigitalOcean |
| **Proxy (prod)** | Nginx | Reverse proxy en `docker-compose.production.yml` |
| **Sync documental** | Google Drive API | Ingesta automática opcional |

---

## Flujo de una consulta

```
 Usuario                Frontend               Backend (Django)          RAG Pipeline              LLM
   │  Escribe pregunta   │                         │                          │                     │
   │────────────────────▶│  POST /api/chat/ (JWT)  │                          │                     │
   │                     │────────────────────────▶│  RAGPipeline.query() ──▶│                     │
   │                     │                         │                         │ 1. Reformular query │
   │                     │                         │                         │    (historial)       │
   │                     │                         │                         │ 2. Embed pregunta    │
   │                     │                         │                         │ 3. Búsqueda híbrida  │
   │                     │                         │                         │    (semántica+léxica)│
   │                     │                         │                         │ 4. Filtrar por doc ID│
   │                     │                         │                         │ 5. Top-k chunks ────▶│ Generar respuesta
   │                     │                         │  Respuesta + fuentes ◀──│◀──────────────────── │  con citas
   │  Ve respuesta +     │◀────────────────────────│  (persistida en BD)     │                      │
   │  citas clicables    │                         │                          │                     │
   │──── click en cita ─▶│  Abre PDF en la página exacta del chunk citado                            │
```

---

## Prerrequisitos

- Python 3.11+ y Node.js 18+ (desarrollo sin Docker)
- Docker + Docker Compose (recomendado para desarrollo y producción)
- API key de al menos un proveedor LLM: Gemini, OpenRouter o Groq
- (Opcional) credenciales de cuenta de servicio de Google Drive para sincronización documental

---

## Instalación y Despliegue

### 1. Clonar

```bash
git clone https://github.com/HugoX2003/nisira-assistant.git
cd nisira-assistant
```

### 2. Backend (Django)

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver          # dev server en :8000
```

### 3. Frontend (React)

```bash
cd frontend
npm install
npm start                           # dev server en :3000
```

### 4. Con Docker (desarrollo — MySQL)

```bash
docker-compose up                   # levanta db + backend + frontend
docker-compose exec backend python manage.py migrate
```

### 5. Con Docker (producción — PostgreSQL + pgvector + Nginx)

```bash
docker-compose -f docker-compose.production.yml up
```

---

## Variables de Entorno

**Backend (`backend/.env`):**

```dotenv
SECRET_KEY, DEBUG, ALLOWED_HOSTS
DATABASE_URL                 # o DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT

LLM_PROVIDER                 # gemini | openrouter | groq
GOOGLE_API_KEY                # Gemini
GOOGLE_DRIVE_FOLDER_ID        # sync opcional
GOOGLE_CREDENTIALS_JSON       # JSON de cuenta de servicio

CORS_ALLOWED_ORIGINS
```

**Frontend (`frontend/.env`):**

```dotenv
REACT_APP_API_URL             # p. ej. http://localhost:8000
```

Todos los parámetros del pipeline (proveedor de LLM, pesos de búsqueda híbrida, estrategia de chunking, umbrales de similitud, top-k adaptativo) se centralizan en `backend/rag_system/config.py`.

---

## Panel de Administración

El panel React (`/admin`) llama a endpoints dedicados para:

- Ingestar / re-indexar documentos
- Explorar los chunks del vector store
- Ver métricas del sistema y resultados de evaluación RAGAS
- Disparar sincronización con Google Drive

El `django-admin` (`/django-admin/`) es independiente y gestiona los modelos a bajo nivel.

---

## Servido de Documentos

Los documentos subidos se almacenan vía `PostgresFileStore` (binario en base de datos) y se sirven en `/api/documents/<slug>/` con un slug público aleatorio. El frontend renderiza los PDFs en un iframe y puede saltar directamente a la página correspondiente usando el metadato `page_number` del chunk citado.

---

## Comandos útiles

```bash
# Backend
python manage.py test                # todos los tests
python manage.py test api             # tests de una app específica

# Frontend
npm run build                         # build de producción
npm test                              # tests

# Docker
docker-compose down
docker-compose exec backend python manage.py migrate
```

---

## Documentación adicional

El directorio [`docs/`](docs/) contiene guías detalladas de arquitectura, despliegue (Docker, Railway, DigitalOcean, Heroku) y troubleshooting. Para una referencia navegable, consulta la **[documentación en Mintlify](https://mintlify.wiki/HugoX2003/nisira-assistant/introduction)**.

---

## Licencia

```
MIT License — Copyright (c) 2025 Hugo Márquez Diestra
```

---

<div align="center">

**NISIRA Assistant** — *De la pregunta a la fuente exacta, con cita incluida.*

</div>
