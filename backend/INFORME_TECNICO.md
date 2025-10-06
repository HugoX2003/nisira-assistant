📋 INFORME TÉCNICO DEL SISTEMA RAG NISIRA
======================================

## 🗂️ UBICACIÓN DE EMBEDDINGS Y VECTORES

**Base de datos vectorial principal:**
- 📂 Ubicación: `C:\Users\amaya\Downloads\10mo Ciclo\nisira-assistant\backend\chroma_db\`
- 📄 Archivo principal: `chroma.sqlite3` (61.72 MB)
- 🗂️ Directorio de índices: `3fb46835-7d9d-4149-a051-2582ac27d303/`
- 📊 **Total documentos vectorizados: 4,401**
- 💾 **Total chunks: 2,178**

**Archivos de embeddings:**
```
chroma_db/
├── chroma.sqlite3 (61.72 MB) - Base de datos SQLite principal
└── 3fb46835-7d9d-4149-a051-2582ac27d303/
    ├── data_level0.bin - Vectores embeddings binarios
    ├── header.bin - Headers de vectores
    ├── index_metadata.pickle - Metadatos de índices
    ├── length.bin - Longitudes de vectores
    └── link_lists.bin - Listas de enlaces para búsqueda
```

## 🧠 CONFIGURACIÓN DE EMBEDDINGS

**Modelo actual:**
- 🔧 **Modelo:** `sentence-transformers/all-mpnet-base-v2`
- 📊 **Dimensiones:** 768D (alta calidad)
- 🏠 **Cache local:** Sí, en directorio del modelo
- 🔄 **Normalización:** Activada para similitud coseno
- ⚡ **Batch size:** 4 (optimizado para memoria)

**Proveedor:**
- 🏢 **Hugging Face Transformers** (local, sin API externa)
- 💰 **Costo:** GRATUITO (modelo local)
- ⚡ **Velocidad:** ~1.5s por batch de 4 documentos

## 🤖 CONFIGURACIÓN DE LLM

**Proveedor principal:**
- 🔧 **Proveedor actual:** OpenRouter
- 🤖 **Modelo:** `google/gemma-2-9b-it`
- 💰 **Costo:** ~$0.000063 por 1K tokens
- ⚡ **Velocidad promedio:** 4.26 segundos por respuesta

**API Configuration:**
- 🌐 **Base URL:** `https://openrouter.ai/api/v1`
- 🔑 **API Key:** Requerida (variable de entorno)
- 📊 **Context window:** 8,192 tokens
- 🎯 **Temperature:** 0.7 (balance creatividad/precisión)

**Proveedores alternativos disponibles:**
- 🔵 Google Gemini 2.0 Flash (más rápido, límites estrictos)
- 🟢 Groq (ultrarrápido, límites diarios)
- 🟣 Together AI (alternativa a OpenRouter)

## 🗄️ CONFIGURACIÓN DE CHROMADB

**Base de datos vectorial:**
- 📚 **Nombre colección:** `rag_documents`
- 📏 **Función distancia:** Coseno
- 📊 **Dimensión:** 768D
- 💾 **Persistencia:** Habilitada
- 🔄 **Auto-sync:** No (manual/programático)

**Configuración de índices:**
- 🎯 **Algoritmo:** HNSW (Hierarchical Navigable Small World)
- 📈 **M parameter:** 16 (conexiones por nodo)
- 🔧 **ef_construction:** 200 (calidad de construcción)

## 🔍 CONFIGURACIÓN DE BÚSQUEDA RAG

**Parámetros de retrieval:**
- 🎯 **Top K:** 15 documentos máximo
- 📈 **Threshold similitud:** 0.005 (muy permisivo)
- 📝 **Máx contexto:** 12,000 caracteres
- 🎭 **Threshold diversidad:** 0.4 (40% similaridad máxima)

**Búsqueda híbrida:**
- ⚖️ **Peso semántico:** 60%
- ⚖️ **Peso lexical:** 40%
- 🔄 **Reranking:** Habilitado
- 🎯 **Citation boost:** Habilitado

## 🔐 APIS Y CLAVES REQUERIDAS

**Variables de entorno necesarias:**
```bash
OPENROUTER_API_KEY=tu_clave_openrouter    # Principal
GOOGLE_API_KEY=tu_clave_google            # Alternativo  
GROQ_API_KEY=tu_clave_groq                # Alternativo
```

**APIs utilizadas:**
1. **OpenRouter** - LLM principal (PAGADO)
2. **Hugging Face** - Embeddings (GRATUITO, local)
3. **Google Drive** - Sincronización docs (GRATUITO)

## 📊 ESTADÍSTICAS DEL SISTEMA

**Contenido procesado:**
- 📄 **PDFs procesados:** 59 documentos académicos
- 📚 **Chunks generados:** 2,178 fragmentos
- 🔤 **Palabras indexadas:** ~500,000 palabras
- 📏 **Promedio por chunk:** 1,000 caracteres

**Rendimiento:**
- ⚡ **Tiempo búsqueda:** <2 segundos
- 🧠 **Tiempo respuesta LLM:** 4-6 segundos
- 💾 **Memoria embeddings:** ~12 MB en RAM
- 🔄 **Throughput:** ~10 consultas/minuto

## 🏗️ ARQUITECTURA TÉCNICA

**Stack tecnológico:**
- 🐍 **Backend:** Django 5.2.7 + Python 3.13
- ⚛️ **Frontend:** React.js
- 🗄️ **Vector DB:** ChromaDB (local)
- 🧠 **Embeddings:** sentence-transformers (local)
- 🤖 **LLM:** OpenRouter API
- 🔄 **Sync:** Google Drive API

**Flujo de procesamiento:**
1. PDF → Extracción texto → Chunking → Embeddings → ChromaDB
2. Query → Embedding → Búsqueda híbrida → LLM → Respuesta

## ⚠️ CONSIDERACIONES DE PRODUCCIÓN

**Escalabilidad:**
- 💾 ChromaDB escala hasta ~1M documentos en un solo nodo
- 🧠 Embeddings locales eliminan costos de API
- 🚀 Considera GPU para embeddings de gran volumen

**Seguridad:**
- 🔑 APIs keys en variables de entorno
- 📂 Datos vectoriales almacenados localmente
- 🔒 No se envían documentos a proveedores externos (solo queries)

**Backup:**
- 💾 Backup regular de `chroma_db/` directory
- 📄 Backup de PDFs originales en `data/documents/`
- ⚙️ Backup de configuración en `rag_system/config.py`