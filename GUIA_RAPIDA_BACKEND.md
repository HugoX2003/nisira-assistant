# 🚀 Guía Rápida del Backend - Nisira Assistant

## 📍 Ubicación Rápida de Componentes

### 🎯 ¿Qué estás buscando?

| Componente | Ubicación | Descripción |
|-----------|-----------|-------------|
| **Modelo RAG Principal** | `/backend/rag_system/rag_engine/pipeline.py` | Orquestación completa del sistema RAG |
| **Generación de Embeddings** | `/backend/rag_system/embeddings/embedding_manager.py` | Convierte texto a vectores (768D) |
| **Procesamiento de PDFs** | `/backend/rag_system/document_processing/pdf_processor.py` | Extrae y divide documentos PDF |
| **Sincronización Google Drive** | `/backend/rag_system/drive_sync/drive_manager.py` | Descarga documentos desde Drive |
| **Base de Datos Vectorial** | `/backend/rag_system/vector_store/chroma_manager.py` | Almacena y busca embeddings |
| **Configuración Central** | `/backend/rag_system/config.py` | Toda la configuración del sistema |
| **API REST** | `/backend/api/views.py` | Endpoints HTTP para el frontend |

---

## 🔄 Flujo Visual Simplificado

```
📁 Google Drive
    │
    │ (GoogleDriveManager)
    ↓
💾 Descarga Local (/backend/data/documents/)
    │
    │ (PDFProcessor)
    ↓
📄 Extracción de Texto + Chunking
    │
    │ (EmbeddingManager)
    ↓
🧠 Embeddings (768 dimensiones)
    │
    │ (ChromaManager)
    ↓
🗄️ ChromaDB (/backend/chroma_db/)
    │
    │ (RAGPipeline.query)
    ↓
🔍 Búsqueda por Similitud
    │
    │ (LLM: OpenRouter/Groq/Gemini)
    ↓
💬 Respuesta Generada
```

---

## 🎯 Comandos Esenciales

### Ver Estado del Sistema
```bash
cd /backend
python manage.py rag_manage --status
```

### Sincronizar Google Drive Manualmente
```bash
python manage.py sync_drive_full
```

### Procesar Documentos
```bash
python manage.py rag_manage --process
```

### Resetear Sistema (⚠️ Elimina todos los embeddings)
```bash
python manage.py rag_manage --reset
```

---

## 📊 Archivos de Datos

| Directorio/Archivo | Contenido | Tamaño Típico |
|-------------------|-----------|---------------|
| `/backend/data/documents/` | PDFs descargados de Drive | Variable (100MB - 5GB) |
| `/backend/chroma_db/` | Base de datos vectorial | ~50MB por 1000 documentos |
| `/backend/data/token.json` | Token OAuth de Google Drive | 2KB |
| `/backend/credentials.json` | Credenciales Google API | 2KB |
| `/backend/data/rag_system.log` | Logs del sistema | Variable |

---

## 🔑 Variables de Entorno Importantes

```bash
# Google Drive
GOOGLE_CREDENTIALS_JSON="{...}"
GOOGLE_DRIVE_FOLDER_ID="1wAYnaln3Dg-MnFy6rNhwqPlh7Ouc4EP8"
ENABLE_GOOGLE_DRIVE="true"

# API Keys para LLM
GOOGLE_API_KEY="your_google_api_key"
OPENROUTER_API_KEY="your_openrouter_key"
GROQ_API_KEY="your_groq_key"

# Base de datos
DATABASE_URL="mysql://user:pass@host:3306/nisira"
```

---

## 🧩 Módulos Independientes

### 1. Sistema de Embeddings (Independiente)
```python
from rag_system.embeddings.embedding_manager import EmbeddingManager

manager = EmbeddingManager()
embedding = manager.create_embedding("texto de ejemplo")
# Retorna: [0.023, -0.145, ..., 0.234]  # 768 dimensiones
```

### 2. Google Drive (Independiente)
```python
from rag_system.drive_sync.drive_manager import GoogleDriveManager

drive = GoogleDriveManager()
files = drive.list_files()
drive.download_file(file_id="abc123", file_name="documento.pdf")
```

### 3. Procesador PDF (Independiente)
```python
from rag_system.document_processing.pdf_processor import PDFProcessor

processor = PDFProcessor()
result = processor.process_pdf("/path/to/document.pdf")
# Retorna chunks de texto con metadatos
```

### 4. ChromaDB (Independiente)
```python
from rag_system.vector_store.chroma_manager import ChromaManager

chroma = ChromaManager()
results = chroma.search_similar(query_embedding, n_results=5)
```

### 5. Pipeline RAG Completo (Orquesta todo)
```python
from rag_system.rag_engine.pipeline import RAGPipeline

pipeline = RAGPipeline()
result = pipeline.query("¿Qué es la democracia?")
```

---

## 🎨 Configuraciones Clave

### Chunking de Documentos
```python
# config.py - DOCUMENT_PROCESSING_CONFIG
{
    ".pdf": {
        "chunk_size": 1300,      # Caracteres por chunk
        "chunk_overlap": 260,    # Overlap entre chunks
        "min_chunk_size": 180,   # Mínimo para no descartar
    }
}
```

### Búsqueda RAG
```python
# config.py - RAG_CONFIG
{
    "retrieval": {
        "top_k": 15,                      # Documentos a recuperar
        "similarity_threshold": 0.005,    # Threshold muy bajo
        "semantic_weight": 0.6,           # Peso búsqueda semántica
        "lexical_weight": 0.4,            # Peso búsqueda lexical
        "max_per_source": 3,              # Chunks por documento
    }
}
```

### Modelo de Embeddings
```python
# config.py - API_CONFIG
{
    "huggingface": {
        "model_name": "sentence-transformers/all-mpnet-base-v2",
        "device": "cpu",
        "normalize_embeddings": True,
    }
}
```

---

## 🐛 Debug y Troubleshooting

### Ver Logs en Tiempo Real
```bash
tail -f /backend/data/rag_system.log
```

### Verificar Estado de ChromaDB
```python
from rag_system.vector_store.chroma_manager import ChromaManager

chroma = ChromaManager()
stats = chroma.get_collection_stats()
print(f"Total documentos: {stats['total_documents']}")
```

### Probar Embeddings
```python
from rag_system.embeddings.embedding_manager import EmbeddingManager

manager = EmbeddingManager()
print(f"Sistema listo: {manager.is_ready()}")
print(f"Proveedor actual: {manager.current_provider}")
print(f"Dimensión: {manager.get_embedding_dimension()}")

# Crear embedding de prueba
test_embedding = manager.create_embedding("texto de prueba")
print(f"Embedding creado con {len(test_embedding)} dimensiones")
```

### Verificar Google Drive
```python
from rag_system.drive_sync.drive_manager import GoogleDriveManager

drive = GoogleDriveManager()
print(f"Autenticado: {drive.is_authenticated()}")
print(f"Archivos en Drive: {len(drive.list_files())}")
```

---

## 📈 Métricas y Rendimiento

### Tiempos Típicos

| Operación | Tiempo | Notas |
|-----------|--------|-------|
| Sincronizar 10 PDFs | ~30 seg | Depende del tamaño |
| Procesar 1 PDF (20 pág) | ~45 seg | Incluye embeddings |
| Generar 1 embedding | ~50 ms | Hugging Face local |
| Búsqueda vectorial | ~300 ms | 1500 documentos |
| Consulta RAG completa | ~3-5 seg | Incluye generación LLM |

### Capacidad

| Métrica | Valor | Límite |
|---------|-------|--------|
| Documentos totales | Sin límite | Depende de disco |
| Chunks en ChromaDB | ~10,000 | Recomendado < 50,000 |
| Tamaño de chunk | 1300 chars | Configurable |
| Dimensión embedding | 768 | Fijo (all-mpnet-base-v2) |

---

## 🔐 Seguridad

### Archivos Sensibles (NO COMMITEAR)
```
/backend/credentials.json         # Credenciales Google
/backend/data/token.json          # Token OAuth
.env                              # Variables de entorno
/backend/chroma_db/              # Base de datos vectorial
/backend/data/documents/         # Documentos descargados
```

### Ya en .gitignore
- `credentials.json`
- `token.json`
- `chroma_db/`
- `data/documents/`
- `.env`

---

## 🚦 Endpoints API Principales

### Estado del Sistema
```bash
curl http://localhost:8000/api/rag/status/
```

### Consulta RAG
```bash
curl -X POST http://localhost:8000/api/rag/query/ \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué es la democracia?", "top_k": 5}'
```

### Sincronización Manual
```bash
curl -X POST http://localhost:8000/api/rag/sync/
```

---

## 📚 Dependencias Principales

```txt
# Core
django==4.2
djangorestframework==3.14
langchain==0.1.0
langchain-community==0.0.10

# Embeddings
sentence-transformers==2.2.2
langchain-google-genai==0.0.6

# Procesamiento
pypdf==3.17.0
python-docx==1.1.0
pdfplumber==0.10.0

# Base de datos vectorial
chromadb==0.4.18

# Google Drive
google-api-python-client==2.108.0
google-auth-httplib2==0.1.1
google-auth-oauthlib==1.1.0
```

---

## 🎓 Para Desarrolladores

### Estructura de un Chunk Procesado
```python
{
    'text': 'Contenido del chunk...',
    'metadata': {
        'source': 'documento.pdf',
        'page': 5,
        'chunk_id': 12,
        'chunk_size': 1280,
        'word_count': 195,
        'document': 'documento.pdf',
        'chunk_type': 'page_content',
        'added_at': '2025-01-15T10:30:00',
        'doc_id': 'uuid-123-456'
    }
}
```

### Estructura de Resultado de Búsqueda
```python
{
    'rank': 1,
    'document': 'Texto del chunk...',
    'metadata': {...},
    'similarity_score': 0.89,
    'distance': 0.11,
    'id': 'uuid-123',
    'search_type': 'semantic'  # o 'metadata', 'expansion'
}
```

### Extender el Sistema

#### Agregar Nuevo Tipo de Documento
1. Crear procesador en `/backend/rag_system/document_processing/`
2. Implementar método `process_document(file_path)`
3. Registrar en `config.py` → `DOCUMENT_PROCESSING_CONFIG`
4. Actualizar `supported_formats`

#### Agregar Nuevo Proveedor de Embeddings
1. Modificar `EmbeddingManager` en `embedding_manager.py`
2. Agregar configuración en `config.py` → `API_CONFIG`
3. Implementar método `_initialize_[provider]_llm()`

---

## 🎯 Quick Start para Testing

### 1. Inicializar Sistema
```bash
cd /backend
python manage.py migrate
python manage.py createsuperuser
```

### 2. Configurar Google Drive
```bash
# Colocar credentials.json en /backend/
export GOOGLE_DRIVE_FOLDER_ID="tu_folder_id"
export ENABLE_GOOGLE_DRIVE="true"
```

### 3. Primera Sincronización
```bash
python manage.py sync_drive_full
```

### 4. Verificar Estado
```bash
python manage.py rag_manage --status
```

### 5. Hacer Primera Consulta
```python
from rag_system.rag_engine.pipeline import RAGPipeline

pipeline = RAGPipeline()
result = pipeline.query("Dame un resumen de los documentos")
print(result['answer'])
```

---

## 📞 Ayuda y Recursos

### Documentación Completa
Ver `ARQUITECTURA_BACKEND_RAG.md` para documentación detallada.

### Issues Comunes

**Error: ChromaDB no inicializa**
- Solución: Eliminar `/backend/chroma_db/` y reiniciar

**Error: Google Drive no autentica**
- Solución: Verificar `credentials.json` y ejecutar flujo OAuth

**Error: Embeddings muy lentos**
- Solución: Verificar que usa Hugging Face local, no Google API

**Error: Out of memory**
- Solución: Reducir `batch_size` en `embedding_manager.py`

---

**Última Actualización**: Noviembre 2025
**Versión**: 1.0.0
