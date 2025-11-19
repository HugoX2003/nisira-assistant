# Arquitectura del Backend - Sistema RAG de Nisira Assistant

## 📋 Índice
1. [Visión General](#visión-general)
2. [Componentes Principales del Sistema RAG](#componentes-principales-del-sistema-rag)
3. [Flujo de Procesamiento de Documentos](#flujo-de-procesamiento-de-documentos)
4. [Ubicación de Archivos Importantes](#ubicación-de-archivos-importantes)
5. [Proceso Detallado: Google Drive → Embeddings](#proceso-detallado-google-drive--embeddings)
6. [Sistema de Embeddings](#sistema-de-embeddings)
7. [Base de Datos Vectorial (ChromaDB)](#base-de-datos-vectorial-chromadb)
8. [Pipeline RAG Completo](#pipeline-rag-completo)
9. [APIs y Endpoints](#apis-y-endpoints)

---

## 🎯 Visión General

El sistema **Nisira Assistant** es una aplicación RAG (Retrieval-Augmented Generation) que permite realizar consultas inteligentes sobre documentos almacenados en Google Drive. El backend está construido con Django y utiliza LangChain para el procesamiento de documentos.

### Tecnologías Clave
- **Framework Backend**: Django + Django REST Framework
- **Sistema RAG**: LangChain
- **Embeddings**: Hugging Face (sentence-transformers/all-mpnet-base-v2) y Google Gemini
- **Base de Datos Vectorial**: ChromaDB
- **LLM**: OpenRouter (Gemma-2-9b-it), Groq (Llama-3.3-70b), Google Gemini
- **Sincronización**: Google Drive API

---

## 🧩 Componentes Principales del Sistema RAG

El sistema RAG se encuentra en el directorio `/backend/rag_system/` y está organizado en módulos especializados:

### 1. **Configuración Central** (`/backend/rag_system/config.py`)
**Ubicación**: `/backend/rag_system/config.py`

Este es el corazón de la configuración del sistema. Define:

- **Rutas y Directorios**:
  - `BASE_DIR`: Directorio base del backend
  - `DATA_DIR`: Almacenamiento de datos (`/backend/data/`)
  - `DOCUMENTS_DIR`: Documentos descargados de Drive
  - `CHROMA_DIR`: Base de datos vectorial ChromaDB

- **Configuración de Google Drive**:
  - `credentials_file`: Credenciales OAuth/Service Account
  - `folder_id`: ID de la carpeta de Google Drive a sincronizar
  - `supported_formats`: [.pdf, .txt, .docx, .doc, .pptx, .xlsx]
  - `sync_interval`: Intervalo de sincronización (300 segundos por defecto)

- **Configuración de Procesamiento de Documentos**:
  - Estrategias de chunking por tipo de archivo:
    - PDF: chunk_size=1300, overlap=260
    - TXT: chunk_size=1100, overlap=220
    - DOCX: chunk_size=1300, overlap=260

- **Configuración de Embeddings**:
  - **Hugging Face**: `sentence-transformers/all-mpnet-base-v2` (768 dimensiones)
  - **Google Gemini**: `models/text-embedding-004`
  - Prioridad: Hugging Face (local, sin límites) → Google (fallback)

- **Configuración del Motor RAG**:
  - `top_k`: 15 documentos por búsqueda
  - `similarity_threshold`: 0.005 (muy bajo para máxima cobertura)
  - `max_context_length`: 12000 caracteres
  - Proveedores LLM: OpenRouter, Groq, Google

### 2. **Gestor de Embeddings** (`/backend/rag_system/embeddings/embedding_manager.py`)
**Ubicación**: `/backend/rag_system/embeddings/embedding_manager.py`

**Responsabilidades**:
- Crear embeddings vectoriales de texto
- Gestión de múltiples proveedores (Hugging Face, Google Gemini)
- Caché de embeddings para optimización
- Procesamiento por lotes (batch processing)

**Características Clave**:
```python
class EmbeddingManager:
    - create_embedding(text)              # Embedding individual
    - create_embeddings_batch(texts)      # Procesamiento en lotes
    - get_embedding_dimension()           # Dimensión del vector (768D)
    - calculate_similarity(emb1, emb2)    # Similitud coseno
```

**Modelo Principal**: 
- `sentence-transformers/all-mpnet-base-v2` (768 dimensiones)
- Procesamiento local, sin límites de API
- Normalización automática de vectores

### 3. **Sincronización con Google Drive** (`/backend/rag_system/drive_sync/drive_manager.py`)
**Ubicación**: `/backend/rag_system/drive_sync/drive_manager.py`

**Responsabilidades**:
- Autenticación con Google Drive (OAuth o Service Account)
- Listado de archivos en carpeta configurada
- Descarga de documentos nuevos o modificados
- Comparación de fechas de modificación
- Exportación de Google Docs a PDF

**Métodos Principales**:
```python
class GoogleDriveManager:
    - is_authenticated()           # Verificar autenticación
    - list_files(folder_id)        # Listar archivos en carpeta
    - download_file(file_id)       # Descargar archivo específico
    - sync_documents()             # Sincronización completa
    - get_sync_status()            # Estado de sincronización
```

**Formatos Soportados**:
- Nativos: PDF, TXT, DOCX, DOC, PPTX, XLSX
- Google Workspace: Se exportan automáticamente a PDF

### 4. **Procesamiento de Documentos**

#### a) **Procesador PDF** (`/backend/rag_system/document_processing/pdf_processor.py`)
**Ubicación**: `/backend/rag_system/document_processing/pdf_processor.py`

**Características**:
- Extracción de texto con LangChain (PyPDFLoader)
- Múltiples métodos de extracción (PyPDF, pdfplumber, PyPDF2)
- Chunking inteligente con RecursiveCharacterTextSplitter
- Preservación de estructura académica
- Detección y preservación de citas bibliográficas
- Limpieza avanzada de texto

**Estrategia de Chunking**:
```python
separators = [
    "\n\n\n",  # Separadores de sección
    "\n\n",    # Párrafos
    "\n",      # Líneas
    ". ",      # Oraciones
    ".",       # Puntos
    " ",       # Espacios
    ""         # Caracteres
]
```

#### b) **Procesador de Texto** (`/backend/rag_system/document_processing/text_processor.py`)
**Ubicación**: `/backend/rag_system/document_processing/text_processor.py`

**Responsabilidades**:
- Procesamiento de archivos TXT, MD, DOCX
- Chunking adaptativo por tipo de archivo
- Extracción de metadatos
- Limpieza y normalización de texto

### 5. **Base de Datos Vectorial ChromaDB** (`/backend/rag_system/vector_store/chroma_manager.py`)
**Ubicación**: `/backend/rag_system/vector_store/chroma_manager.py`

**Responsabilidades**:
- Almacenamiento persistente de embeddings
- Búsqueda por similitud vectorial
- Gestión de colecciones
- Backup y restauración

**Métodos Principales**:
```python
class ChromaManager:
    - add_documents(docs, embeddings)     # Agregar documentos
    - search_similar(embedding, n=5)      # Búsqueda vectorial
    - get_collection_stats()              # Estadísticas
    - reset_collection()                  # Limpiar colección
    - backup_collection(path)             # Respaldo
```

**Configuración**:
- Función de distancia: Coseno
- Dimensión: 768 (para all-mpnet-base-v2)
- Persistencia: `/backend/chroma_db/`

### 6. **Pipeline RAG Principal** (`/backend/rag_system/rag_engine/pipeline.py`)
**Ubicación**: `/backend/rag_system/rag_engine/pipeline.py`

**Responsabilidades**:
- Orquestación de todos los componentes
- Procesamiento completo de documentos
- Búsqueda híbrida (semántica + metadatos + expansión)
- Generación de respuestas con LLM

**Métodos Principales**:
```python
class RAGPipeline:
    - sync_and_process_documents()        # Sincronizar y procesar
    - process_document(file_path)         # Procesar documento individual
    - query(question)                     # Consulta RAG completa
    - get_system_status()                 # Estado del sistema
```

---

## 🔄 Flujo de Procesamiento de Documentos

### Flujo Completo: Google Drive → Respuesta

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. SINCRONIZACIÓN                            │
│  Google Drive → GoogleDriveManager → Descarga local             │
│  Ubicación: /backend/data/documents/                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    2. PROCESAMIENTO                             │
│  PDFProcessor / TextProcessor → Extracción de texto             │
│  • Limpieza de texto                                            │
│  • Chunking inteligente                                         │
│  • Extracción de metadatos                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    3. GENERACIÓN DE EMBEDDINGS                  │
│  EmbeddingManager → Vectorización                               │
│  • Modelo: all-mpnet-base-v2 (768D)                            │
│  • Procesamiento en batches de 4 chunks                         │
│  • Normalización de vectores                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    4. ALMACENAMIENTO VECTORIAL                  │
│  ChromaManager → Persistencia en ChromaDB                       │
│  • Índice vectorial optimizado                                  │
│  • Metadatos asociados                                          │
│  • Búsqueda por similitud coseno                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    5. CONSULTA (QUERY)                          │
│  Usuario → Pregunta → Embedding de consulta                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    6. BÚSQUEDA HÍBRIDA                          │
│  • Búsqueda semántica (similitud vectorial)                     │
│  • Búsqueda por metadatos (nombres de archivo)                  │
│  • Búsqueda expandida (términos relacionados)                   │
│  • Re-ranking por relevancia                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    7. GENERACIÓN DE RESPUESTA                   │
│  LLM (OpenRouter/Groq/Gemini) → Respuesta contextual           │
│  • Contexto de documentos relevantes                            │
│  • Prompt especializado en español                              │
│  • Formato Markdown estructurado                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 Ubicación de Archivos Importantes

### Estructura del Backend

```
/backend/
│
├── rag_system/                          # 🎯 SISTEMA RAG PRINCIPAL
│   ├── config.py                        # ⭐ Configuración central
│   │
│   ├── embeddings/                      # 🧠 SISTEMA DE EMBEDDINGS
│   │   ├── embedding_manager.py         # ⭐ Gestor de embeddings
│   │   └── __init__.py
│   │
│   ├── drive_sync/                      # ☁️ SINCRONIZACIÓN GOOGLE DRIVE
│   │   ├── drive_manager.py             # ⭐ Gestor de Drive API
│   │   └── __init__.py
│   │
│   ├── document_processing/             # 📄 PROCESAMIENTO DE DOCUMENTOS
│   │   ├── pdf_processor.py             # ⭐ Procesador PDF (LangChain)
│   │   ├── text_processor.py            # ⭐ Procesador TXT/DOCX
│   │   └── __init__.py
│   │
│   ├── vector_store/                    # 💾 BASE DE DATOS VECTORIAL
│   │   ├── chroma_manager.py            # ⭐ Gestor ChromaDB
│   │   └── __init__.py
│   │
│   ├── rag_engine/                      # 🚀 MOTOR RAG
│   │   ├── pipeline.py                  # ⭐ Pipeline principal RAG
│   │   └── __init__.py
│   │
│   └── __init__.py
│
├── api/                                 # 🌐 API REST
│   ├── views.py                         # ⭐ Endpoints principales
│   ├── urls.py                          # Rutas de la API
│   ├── models.py                        # Modelos de base de datos
│   ├── serializers.py                   # Serializadores DRF
│   ├── ragas_evaluator.py               # Evaluación de calidad
│   ├── metrics_tracker.py               # Métricas de rendimiento
│   │
│   └── management/commands/             # 🛠️ COMANDOS DE GESTIÓN
│       ├── rag_manage.py                # ⭐ Gestión del sistema RAG
│       ├── sync_drive_full.py           # ⭐ Sincronización completa
│       ├── start_drive_sync.py          # Iniciar sincronización
│       ├── initdb.py                    # Inicializar base de datos
│       └── create_admin_user.py         # Crear usuario admin
│
├── data/                                # 💽 DATOS PERSISTENTES
│   ├── documents/                       # 📁 Documentos de Google Drive
│   ├── processed/                       # 📁 Documentos procesados
│   ├── token.json                       # Token OAuth Drive
│   └── rag_system.log                   # Logs del sistema
│
├── chroma_db/                           # 🗄️ BASE DE DATOS VECTORIAL
│   └── [archivos de ChromaDB]          # Colección de embeddings
│
├── core/                                # ⚙️ CONFIGURACIÓN DJANGO
│   ├── settings.py                      # Configuración principal
│   ├── urls.py                          # URLs principales
│   └── wsgi.py                          # WSGI application
│
├── monitoring/                          # 📊 MONITOREO
│   └── health.py                        # Health checks
│
├── credentials.json                     # 🔑 Credenciales Google Drive
├── requirements.txt                     # 📦 Dependencias Python
└── manage.py                            # 🎮 CLI de Django
```

---

## 🔍 Proceso Detallado: Google Drive → Embeddings

### Paso 1: Configuración Inicial

**Archivo**: `/backend/rag_system/config.py`

```python
# Configuración de Google Drive
GOOGLE_DRIVE_CONFIG = {
    "folder_id": "1wAYnaln3Dg-MnFy6rNhwqPlh7Ouc4EP8",
    "download_path": "/backend/data/documents/",
    "supported_formats": [".pdf", ".txt", ".docx", ".doc", ".pptx", ".xlsx"],
    "sync_interval": 300  # 5 minutos
}
```

### Paso 2: Sincronización con Google Drive

**Componente**: `GoogleDriveManager` (`drive_manager.py`)

**Proceso**:
1. **Autenticación**:
   - OAuth 2.0 o Service Account
   - Token almacenado en `/backend/data/token.json`

2. **Listado de Archivos**:
   ```python
   files = drive_manager.list_files(folder_id)
   # Filtra por formatos soportados
   # Paginación automática para carpetas grandes
   ```

3. **Descarga Selectiva**:
   - Compara fechas de modificación
   - Solo descarga archivos nuevos o modificados
   - Convierte Google Docs a PDF automáticamente

4. **Almacenamiento Local**:
   - Directorio: `/backend/data/documents/`
   - Preserva nombres originales

### Paso 3: Procesamiento de Documentos

**Componente**: `PDFProcessor` / `TextProcessor`

**Flujo para PDF**:

1. **Extracción de Texto**:
   ```python
   # Usa LangChain PyPDFLoader
   loader = PyPDFLoader(pdf_path)
   documents = loader.load()
   ```

2. **Limpieza de Texto**:
   - Normalización de espacios
   - Corrección de puntuación
   - Preservación de citas bibliográficas (Arias(2020))
   - Detección de secciones especiales

3. **Chunking Inteligente**:
   ```python
   text_splitter = RecursiveCharacterTextSplitter(
       chunk_size=1300,        # Caracteres por chunk
       chunk_overlap=260,      # Overlap para contexto
       separators=["\n\n\n", "\n\n", "\n", ". ", ".", " ", ""]
   )
   chunks = text_splitter.split_documents(cleaned_docs)
   ```

4. **Enriquecimiento de Metadatos**:
   ```python
   metadata = {
       'source': 'documento.pdf',
       'page': 5,
       'chunk_id': 12,
       'chunk_size': 1280,
       'word_count': 195,
       'document': 'documento.pdf',
       'chunk_type': 'page_content'
   }
   ```

### Paso 4: Generación de Embeddings

**Componente**: `EmbeddingManager` (`embedding_manager.py`)

**Proceso**:

1. **Inicialización del Modelo**:
   ```python
   # Modelo Hugging Face (preferido)
   model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
   # Dimensión: 768
   # Dispositivo: CPU (portátil)
   ```

2. **Procesamiento por Lotes**:
   ```python
   # Batches pequeños para all-mpnet-base-v2 (modelo pesado)
   batch_size = 4
   
   for i in range(0, len(texts), batch_size):
       batch = texts[i:i + batch_size]
       embeddings = model.encode(batch, normalize_embeddings=True)
       # Normalización para similitud coseno
   ```

3. **Caché de Embeddings**:
   - Hash MD5 del texto como clave
   - Cache en memoria para reutilización
   - Evita recalcular embeddings duplicados

4. **Resultado**:
   ```python
   embedding = [0.023, -0.145, 0.089, ..., 0.234]  # 768 dimensiones
   # Vector normalizado para similitud coseno
   ```

### Paso 5: Almacenamiento en ChromaDB

**Componente**: `ChromaManager` (`chroma_manager.py`)

**Proceso**:

1. **Preparación de Datos**:
   ```python
   for doc, embedding in zip(chunks, embeddings):
       ids.append(str(uuid.uuid4()))
       texts.append(doc['text'])
       metadatas.append(doc['metadata'])
       embeddings_list.append(embedding)
   ```

2. **Inserción en ChromaDB**:
   ```python
   collection.add(
       ids=ids,
       documents=texts,
       metadatas=metadatas,
       embeddings=embeddings_list
   )
   ```

3. **Persistencia**:
   - Directorio: `/backend/chroma_db/`
   - Formato: SQLite + archivos binarios
   - Índice vectorial optimizado para búsqueda

---

## 🧠 Sistema de Embeddings

### Modelos Disponibles

#### 1. **Hugging Face (Preferido)**
- **Modelo**: `sentence-transformers/all-mpnet-base-v2`
- **Dimensiones**: 768
- **Características**:
  - Procesamiento local (sin límites de API)
  - Excelente calidad para español e inglés
  - Normalización automática
  - Sin costos

#### 2. **Google Gemini (Fallback)**
- **Modelo**: `models/text-embedding-004`
- **Características**:
  - API remota (límites de tasa)
  - Alta calidad
  - Requiere API key

### Proceso de Creación de Embeddings

```python
# 1. Truncar texto si es necesario (máx 512 tokens)
processed_text = truncate_text(text, max_tokens=512)

# 2. Crear embedding
embedding = model.encode(processed_text, normalize_embeddings=True)

# 3. Normalizar vector (para similitud coseno)
embedding = embedding / np.linalg.norm(embedding)

# 4. Resultado: vector de 768 dimensiones
# [0.023, -0.145, 0.089, ..., 0.234]
```

### Cálculo de Similitud

```python
def calculate_similarity(embedding1, embedding2):
    # Similitud coseno (0 a 1)
    similarity = np.dot(embedding1, embedding2) / (
        np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
    )
    return similarity
```

---

## 💾 Base de Datos Vectorial (ChromaDB)

### Características

- **Tipo**: Base de datos vectorial embebida
- **Almacenamiento**: Persistente en disco
- **Función de distancia**: Similitud coseno
- **Capacidad**: Miles de documentos

### Operaciones Principales

#### 1. Agregar Documentos
```python
chroma_manager.add_documents(
    documents=[
        {'text': 'contenido...', 'metadata': {...}},
        ...
    ],
    embeddings=[[0.1, 0.2, ...], ...]
)
```

#### 2. Búsqueda por Similitud
```python
results = chroma_manager.search_similar(
    query_embedding=[0.1, 0.2, ...],
    n_results=15,
    similarity_threshold=0.005
)
```

#### 3. Estadísticas
```python
stats = chroma_manager.get_collection_stats()
# {
#     "total_documents": 1523,
#     "collection_name": "rag_documents",
#     "file_types": [".pdf", ".txt", ".docx"]
# }
```

---

## 🚀 Pipeline RAG Completo

### Inicialización

```python
from rag_system.rag_engine.pipeline import RAGPipeline

pipeline = RAGPipeline()

# Verificar componentes
status = pipeline.is_ready()
# {
#     'drive_manager': True,
#     'pdf_processor': True,
#     'embedding_manager': True,
#     'chroma_manager': True,
#     'llm_available': True
# }
```

### Sincronización y Procesamiento

```python
# Sincronizar desde Google Drive y procesar
result = pipeline.sync_and_process_documents(force_reprocess=False)

# {
#     "success": True,
#     "processing_summary": {
#         "total_documents": 25,
#         "successful": 25,
#         "total_chunks": 1523,
#         "valid_chunks": 1523
#     }
# }
```

### Consulta RAG

```python
# Realizar consulta
result = pipeline.query(
    question="¿Qué dice Arias(2020) sobre el derecho?",
    top_k=5,
    include_generation=True
)

# {
#     "success": True,
#     "question": "¿Qué dice Arias(2020) sobre el derecho?",
#     "relevant_documents": [...],  # Top 15 documentos
#     "sources": [...],             # Información de fuentes
#     "answer": "Según Arias (2020)...",  # Respuesta generada
#     "generation_used": True
# }
```

### Búsqueda Híbrida

El sistema utiliza una estrategia de búsqueda híbrida:

1. **Búsqueda Semántica** (peso: 60%)
   - Similitud coseno de embeddings
   - Threshold: 0.005 (muy bajo para máxima cobertura)

2. **Búsqueda por Metadatos** (peso alto para coincidencias exactas)
   - Nombres de archivos
   - Títulos de documentos

3. **Búsqueda Expandida** (peso: 30%)
   - Términos relacionados
   - Sinónimos académicos

4. **Re-ranking**
   - Diversificación de resultados
   - Máximo 3 chunks por documento
   - Ordenamiento por relevancia ponderada

---

## 🌐 APIs y Endpoints

### Estructura de la API

**Base URL**: `/api/`

### Endpoints RAG Principales

#### 1. Estado del Sistema
```http
GET /api/rag/status/
```
Respuesta:
```json
{
    "readiness": {
        "drive_manager": true,
        "embedding_manager": true,
        "chroma_manager": true,
        "llm_available": true
    },
    "stats": {
        "documents_processed": 25,
        "chunks_created": 1523,
        "embeddings_generated": 1523
    },
    "chroma_stats": {
        "total_documents": 1523
    }
}
```

#### 2. Consulta RAG
```http
POST /api/rag/query/
Content-Type: application/json

{
    "question": "¿Qué es la democracia según los documentos?",
    "top_k": 5
}
```

Respuesta:
```json
{
    "success": true,
    "question": "...",
    "relevant_documents": [...],
    "sources": [
        {
            "file_name": "documento.pdf",
            "page": 5,
            "similarity_score": 0.89,
            "content": "..."
        }
    ],
    "answer": "La democracia es...",
    "generation_used": true
}
```

#### 3. Chat Conversacional
```http
POST /api/rag/chat/
Content-Type: application/json

{
    "message": "Explícame el concepto de regionalización",
    "conversation_id": "uuid-123"
}
```

#### 4. Sincronización Manual
```http
POST /api/rag/sync/
```

### Comandos de Gestión Django

#### Sincronización Completa
```bash
python manage.py sync_drive_full
```

#### Gestión del Sistema RAG
```bash
# Ver estado
python manage.py rag_manage --status

# Procesar documentos
python manage.py rag_manage --process

# Resetear sistema
python manage.py rag_manage --reset
```

---

## 📊 Flujo de Datos Detallado

### 1. Configuración Inicial
- Credenciales de Google Drive en `/backend/credentials.json`
- Variables de entorno para API keys (GOOGLE_API_KEY, OPENROUTER_API_KEY)
- Configuración en `/backend/rag_system/config.py`

### 2. Sincronización Automática
- Intervalo: 300 segundos (configurable)
- Proceso en background con Celery (opcional)
- Descarga solo archivos nuevos o modificados

### 3. Procesamiento Pipeline
```
Documento PDF (5 MB)
    ↓
Extracción (PyPDFLoader) → 50 páginas de texto
    ↓
Limpieza y chunking → 250 chunks de ~1300 caracteres
    ↓
Generación de embeddings → 250 vectores de 768 dimensiones
    ↓
Almacenamiento ChromaDB → Índice vectorial
    ↓
Listo para consultas
```

### 4. Tiempo de Procesamiento Típico
- **1 documento PDF (20 páginas)**: ~30-60 segundos
  - Extracción: 5 segundos
  - Chunking: 2 segundos
  - Embeddings: 20-40 segundos (4 chunks por batch)
  - Almacenamiento: 3 segundos

### 5. Consulta en Tiempo Real
- **Tiempo de respuesta**: ~2-5 segundos
  - Embedding de consulta: 0.1 segundos
  - Búsqueda vectorial: 0.3 segundos
  - Generación LLM: 1.5-4 segundos

---

## 🎓 Resumen Ejecutivo

### ¿Dónde está el modelo RAG?
**Pipeline principal**: `/backend/rag_system/rag_engine/pipeline.py`

### ¿Dónde están los embeddings?
- **Generación**: `/backend/rag_system/embeddings/embedding_manager.py`
- **Modelo**: Hugging Face `sentence-transformers/all-mpnet-base-v2` (768D)
- **Almacenamiento**: `/backend/chroma_db/` (ChromaDB)

### ¿Cómo se procesan los documentos de Google Drive?
1. **Sincronización**: `GoogleDriveManager` descarga de Drive
2. **Procesamiento**: `PDFProcessor` extrae y divide texto
3. **Embeddings**: `EmbeddingManager` crea vectores
4. **Almacenamiento**: `ChromaManager` guarda en ChromaDB
5. **Consulta**: `RAGPipeline` coordina búsqueda y generación

### Archivos Críticos
1. `config.py` - Configuración central
2. `pipeline.py` - Orquestación RAG
3. `embedding_manager.py` - Sistema de embeddings
4. `drive_manager.py` - Sincronización Google Drive
5. `pdf_processor.py` - Procesamiento de documentos
6. `chroma_manager.py` - Base de datos vectorial

---

## 🔗 Enlaces y Recursos

- **Documentación LangChain**: https://python.langchain.com/
- **ChromaDB Docs**: https://docs.trychroma.com/
- **Sentence Transformers**: https://www.sbert.net/
- **Google Drive API**: https://developers.google.com/drive

---

**Actualizado**: Noviembre 2025
**Versión del Sistema**: 1.0.0
