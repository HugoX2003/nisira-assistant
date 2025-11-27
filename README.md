# 🤖 Nisira Assistant

Sistema RAG (Retrieval-Augmented Generation) inteligente para consultas sobre documentos académicos y técnicos.

## 🎯 ¿Qué es Nisira Assistant?

Nisira Assistant es un asistente virtual que permite realizar consultas inteligentes sobre una colección de documentos. El sistema:

- 📥 Sincroniza automáticamente documentos desde Google Drive
- 🧠 Convierte documentos a embeddings vectoriales (768 dimensiones)
- 🔍 Realiza búsquedas semánticas híbridas
- 💬 Genera respuestas contextuales con modelos de lenguaje (LLM)

## 📚 Documentación

### 🚀 Empezar Rápido
Para comenzar a usar y entender el sistema:

1. **[INDICE_DOCUMENTACION_BACKEND.md](./INDICE_DOCUMENTACION_BACKEND.md)** - **EMPIEZA AQUÍ**
   - Índice maestro de toda la documentación
   - Guía de navegación por caso de uso
   - Quick start y primeros pasos

### 📖 Documentación Técnica

2. **[ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md)** - Documentación Completa
   - Arquitectura detallada del sistema RAG
   - Componentes principales con ejemplos
   - Flujo completo: Google Drive → Embeddings → Respuesta
   - Sistema de embeddings explicado
   - Base de datos vectorial ChromaDB
   - APIs y endpoints

3. **[GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md)** - Referencia Rápida
   - Comandos esenciales
   - Ubicación de componentes
   - Ejemplos de código para cada módulo
   - Debug y troubleshooting
   - Configuraciones clave

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    NISIRA ASSISTANT                             │
│                 Sistema RAG Completo                            │
└─────────────────────────────────────────────────────────────────┘

    📁 Google Drive                    👤 Usuario
         │                                  │
         │ (Sincronización)                 │ (Consulta)
         ↓                                  ↓
    💾 Documentos Locales            🔍 Pregunta
         │                                  │
         │ (Procesamiento)                  │ (Embedding)
         ↓                                  ↓
    📄 Chunks de Texto               🧠 Vector (768D)
         │                                  │
         │ (Embeddings)                     │ (Búsqueda)
         ↓                                  ↓
    🧠 Vectores (768D)         ←──────  💾 ChromaDB
         │                                  │
         │ (Almacenamiento)                 │ (Top-K Docs)
         ↓                                  ↓
    💾 ChromaDB                      📊 Documentos Relevantes
                                            │
                                            │ (Generación)
                                            ↓
                                     💬 Respuesta con LLM
```

## 🚀 Quick Start

### 1. Instalación

```bash
# Clonar repositorio
git clone https://github.com/HugoX2003/nisira-assistant.git
cd nisira-assistant

# Instalar dependencias
cd backend
pip install -r requirements.txt

# Configurar base de datos
python manage.py migrate
python manage.py createsuperuser
```

### 2. Configuración

```bash
# Configurar variables de entorno
export GOOGLE_DRIVE_FOLDER_ID="tu_folder_id"
export GOOGLE_API_KEY="tu_api_key"
export ENABLE_GOOGLE_DRIVE="true"

# Colocar credenciales de Google Drive
cp credentials.json backend/
```

### 3. Primera Sincronización

```bash
cd backend
python manage.py sync_drive_full
python manage.py rag_manage --status
```

### 4. Iniciar Servidor

```bash
python manage.py runserver
```

### 5. Hacer Primera Consulta

**Opción A: Python**
```python
from rag_system.rag_engine.pipeline import RAGPipeline

pipeline = RAGPipeline()
result = pipeline.query("¿Qué es la democracia?")
print(result['answer'])
```

**Opción B: API REST**
```bash
curl -X POST http://localhost:8000/api/rag/query/ \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué es la democracia?", "top_k": 5}'
```

## 🧩 Componentes Principales

| Componente | Ubicación | Función |
|-----------|-----------|---------|
| **RAG Pipeline** | `/backend/rag_system/rag_engine/pipeline.py` | Orquestación completa |
| **Embeddings** | `/backend/rag_system/embeddings/embedding_manager.py` | Vectorización (768D) |
| **Google Drive** | `/backend/rag_system/drive_sync/drive_manager.py` | Sincronización |
| **Procesador PDF** | `/backend/rag_system/document_processing/pdf_processor.py` | Extracción y chunking |
| **ChromaDB** | `/backend/rag_system/vector_store/chroma_manager.py` | Base de datos vectorial |
| **Configuración** | `/backend/rag_system/config.py` | Configuración central |
| **API REST** | `/backend/api/views.py` | Endpoints HTTP |

## 🛠️ Tecnologías

### Backend
- **Framework**: Django 4.2 + Django REST Framework
- **RAG System**: LangChain
- **Embeddings**: Hugging Face (sentence-transformers/all-mpnet-base-v2)
- **Vector DB**: ChromaDB
- **LLM**: OpenRouter (Gemma-2-9b), Groq (Llama-3.3-70b), Google Gemini
- **Document Processing**: PyPDF, python-docx, pdfplumber

### Integrations
- **Google Drive API**: Sincronización automática
- **OAuth 2.0**: Autenticación
- **JWT**: Tokens de sesión

## 📊 Capacidades del Sistema

| Métrica | Valor |
|---------|-------|
| **Dimensión de embeddings** | 768 (all-mpnet-base-v2) |
| **Formatos soportados** | PDF, TXT, DOCX, DOC, PPTX, XLSX |
| **Tamaño de chunk** | 1300 caracteres |
| **Overlap de chunks** | 260 caracteres |
| **Documentos por búsqueda** | Top-15 con re-ranking |
| **Tiempo de consulta** | 2-5 segundos |
| **Tiempo de procesamiento (20 págs)** | ~45 segundos |

## 🌐 API Endpoints

### Estado del Sistema
```http
GET /api/rag/status/
```

### Consulta RAG
```http
POST /api/rag/query/
Content-Type: application/json

{
    "question": "¿Qué es la democracia?",
    "top_k": 5
}
```

### Chat Conversacional
```http
POST /api/rag/chat/
Content-Type: application/json

{
    "message": "Explícame el concepto",
    "conversation_id": "uuid"
}
```

### Sincronización Manual
```http
POST /api/rag/sync/
```

## 🔧 Comandos Útiles

```bash
# Ver estado del sistema
python manage.py rag_manage --status

# Sincronizar Google Drive
python manage.py sync_drive_full

# Procesar documentos
python manage.py rag_manage --process

# Resetear sistema (⚠️ elimina embeddings)
python manage.py rag_manage --reset

# Ver logs en tiempo real
tail -f backend/data/rag_system.log
```

## 📂 Estructura del Proyecto

```
nisira-assistant/
├── backend/
│   ├── rag_system/              # 🎯 Sistema RAG Principal
│   │   ├── config.py            # Configuración central
│   │   ├── embeddings/          # Sistema de embeddings
│   │   ├── drive_sync/          # Sincronización Google Drive
│   │   ├── document_processing/ # Procesamiento de documentos
│   │   ├── vector_store/        # ChromaDB
│   │   └── rag_engine/          # Pipeline RAG
│   │
│   ├── api/                     # API REST
│   ├── core/                    # Configuración Django
│   ├── data/                    # Datos persistentes
│   ├── chroma_db/              # Base de datos vectorial
│   └── manage.py                # CLI Django
│
├── frontend/                    # Frontend React (si aplica)
│
├── INDICE_DOCUMENTACION_BACKEND.md      # 📚 Índice maestro
├── ARQUITECTURA_BACKEND_RAG.md          # 📖 Documentación técnica
├── GUIA_RAPIDA_BACKEND.md               # 🚀 Referencia rápida
└── README.md                             # Este archivo
```

## 🔐 Variables de Entorno

```bash
# Google Drive
GOOGLE_DRIVE_FOLDER_ID="1wAYnaln3Dg-MnFy6rNhwqPlh7Ouc4EP8"
GOOGLE_CREDENTIALS_JSON="{...}"
ENABLE_GOOGLE_DRIVE="true"

# API Keys
GOOGLE_API_KEY="your_google_api_key"
OPENROUTER_API_KEY="your_openrouter_key"
GROQ_API_KEY="your_groq_key"

# Base de datos
DATABASE_URL="mysql://user:pass@host:3306/nisira"
```

## 🐛 Troubleshooting

### ChromaDB no inicializa
```bash
rm -rf backend/chroma_db/
python manage.py rag_manage --reset
```

### Google Drive no autentica
```bash
# Verificar credentials.json
# Ejecutar flujo OAuth manualmente
python manage.py sync_drive_full
```

### Embeddings muy lentos
```bash
# Verificar que usa Hugging Face local
python -c "from rag_system.embeddings.embedding_manager import EmbeddingManager; m=EmbeddingManager(); print(m.current_provider)"
# Debe mostrar: huggingface
```

## 📈 Métricas de Rendimiento

| Operación | Tiempo Promedio |
|-----------|----------------|
| Sincronizar 10 PDFs | ~30 segundos |
| Procesar 1 PDF (20 páginas) | ~45 segundos |
| Generar 1 embedding | ~50 ms |
| Búsqueda vectorial | ~300 ms |
| Consulta RAG completa | ~3-5 segundos |

## 🎓 Recursos de Aprendizaje

### Documentación Interna
1. **[INDICE_DOCUMENTACION_BACKEND.md](./INDICE_DOCUMENTACION_BACKEND.md)** - Empieza aquí
2. **[ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md)** - Referencia técnica
3. **[GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md)** - Comandos y ejemplos

### Documentación Externa
- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [Google Drive API](https://developers.google.com/drive)

## 🤝 Contribuir

Para contribuir al proyecto:

1. Lee la documentación completa
2. Familiarízate con la arquitectura
3. Abre un issue para discutir cambios
4. Crea un Pull Request con tus cambios

## 📄 Licencia

Ver archivo [LICENSE](./LICENSE)

## 👥 Equipo

- **Desarrollo Principal**: HugoX2003
- **Repositorio**: https://github.com/HugoX2003/nisira-assistant

## 📞 Soporte

- **Issues**: https://github.com/HugoX2003/nisira-assistant/issues
- **Documentación**: Ver archivos de documentación en el repositorio

---

**Versión**: 1.0.0  
**Última actualización**: Noviembre 2025

---

## ⭐ Características Destacadas

- ✅ Sincronización automática con Google Drive
- ✅ Procesamiento inteligente de múltiples formatos
- ✅ Embeddings de alta calidad (768D)
- ✅ Búsqueda híbrida (semántica + metadatos + expansión)
- ✅ Generación de respuestas contextuales
- ✅ API REST completa
- ✅ Sistema modular y extensible
- ✅ Documentación exhaustiva en español

---

**¿Nuevo en el proyecto?** → Comienza con [INDICE_DOCUMENTACION_BACKEND.md](./INDICE_DOCUMENTACION_BACKEND.md)
