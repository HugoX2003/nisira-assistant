# 📚 Índice de Documentación del Backend

## 🎯 Bienvenida

Esta es la documentación completa del sistema backend de **Nisira Assistant**, un sistema RAG (Retrieval-Augmented Generation) que permite consultas inteligentes sobre documentos.

---

## 📖 Guías Disponibles

### 1. 📘 [ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md)
**Documentación Técnica Completa**

Documentación detallada y exhaustiva del sistema backend. Ideal para:
- ✅ Desarrolladores que necesitan entender el sistema completo
- ✅ Arquitectos evaluando el diseño
- ✅ Nuevos miembros del equipo
- ✅ Documentación de referencia técnica

**Contenido:**
- Visión general del sistema
- Componentes principales con código de ejemplo
- Flujo completo de procesamiento
- Ubicación detallada de archivos
- Proceso paso a paso: Google Drive → Embeddings
- Sistema de embeddings explicado
- Base de datos vectorial ChromaDB
- Pipeline RAG completo
- APIs y endpoints

**Tiempo de lectura**: ~30-45 minutos

---

### 2. 🚀 [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md)
**Guía de Referencia Rápida**

Guía práctica con comandos y ejemplos listos para usar. Ideal para:
- ✅ Desarrolladores buscando comandos específicos
- ✅ Debugging y troubleshooting
- ✅ Referencia rápida de componentes
- ✅ Quick start para testing

**Contenido:**
- Ubicación rápida de componentes (tabla de referencia)
- Flujo visual simplificado
- Comandos esenciales
- Variables de entorno
- Ejemplos de código para cada módulo
- Configuraciones clave
- Debug y troubleshooting
- Métricas y rendimiento
- Quick start para testing

**Tiempo de lectura**: ~10-15 minutos

---

## 🗺️ ¿Por Dónde Empezar?

### Si eres nuevo en el proyecto:
1. **Comienza con**: [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md)
   - Lee la sección "Ubicación Rápida de Componentes"
   - Revisa el "Flujo Visual Simplificado"
   - Familiarízate con los comandos esenciales

2. **Luego continúa con**: [ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md)
   - Lee la "Visión General"
   - Revisa los "Componentes Principales"
   - Estudia el "Flujo de Procesamiento"

### Si necesitas implementar algo específico:
1. **Consulta**: [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md)
   - Busca el componente en la tabla de ubicación
   - Revisa los ejemplos de código independientes
   - Usa los comandos de debug

2. **Para detalles técnicos**: [ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md)
   - Busca la sección del componente específico
   - Revisa el código de ejemplo
   - Estudia las configuraciones relacionadas

### Si tienes un problema:
1. **Primero**: [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md) → Sección "Debug y Troubleshooting"
2. **Luego**: [ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md) → Sección del componente afectado

---

## 🎓 Temas Específicos - Guía de Navegación

### 🧠 Sistema de Embeddings
**¿Dónde está?**
- **Código**: `/backend/rag_system/embeddings/embedding_manager.py`
- **Documentación Completa**: [ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md) → Sección "Sistema de Embeddings"
- **Referencia Rápida**: [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md) → "Módulos Independientes" → "Sistema de Embeddings"

**¿Qué hace?**
- Convierte texto a vectores de 768 dimensiones
- Usa Hugging Face `sentence-transformers/all-mpnet-base-v2`
- Procesa en batches de 4 chunks
- Caché automático de embeddings

---

### ☁️ Sincronización Google Drive
**¿Dónde está?**
- **Código**: `/backend/rag_system/drive_sync/drive_manager.py`
- **Documentación Completa**: [ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md) → Sección "Sincronización con Google Drive"
- **Referencia Rápida**: [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md) → "Módulos Independientes" → "Google Drive"

**¿Qué hace?**
- Descarga documentos desde Google Drive
- Solo descarga archivos nuevos o modificados
- Convierte Google Docs a PDF automáticamente
- Almacena en `/backend/data/documents/`

**Comandos útiles:**
```bash
# Sincronizar manualmente
python manage.py sync_drive_full

# Verificar estado
python manage.py rag_manage --status
```

---

### 📄 Procesamiento de Documentos
**¿Dónde está?**
- **PDFs**: `/backend/rag_system/document_processing/pdf_processor.py`
- **Textos**: `/backend/rag_system/document_processing/text_processor.py`
- **Documentación Completa**: [ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md) → Sección "Procesamiento de Documentos"
- **Referencia Rápida**: [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md) → "Módulos Independientes" → "Procesador PDF"

**¿Qué hace?**
- Extrae texto de PDFs, DOCX, TXT
- Divide en chunks de ~1300 caracteres
- Preserva estructura y citas bibliográficas
- Genera metadatos enriquecidos

**Ejemplo de uso:**
```python
from rag_system.document_processing.pdf_processor import PDFProcessor

processor = PDFProcessor()
result = processor.process_pdf("/path/to/document.pdf")
print(f"Generados {result['stats']['total_chunks']} chunks")
```

---

### 💾 Base de Datos Vectorial (ChromaDB)
**¿Dónde está?**
- **Código**: `/backend/rag_system/vector_store/chroma_manager.py`
- **Datos**: `/backend/chroma_db/`
- **Documentación Completa**: [ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md) → Sección "Base de Datos Vectorial"
- **Referencia Rápida**: [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md) → "Módulos Independientes" → "ChromaDB"

**¿Qué hace?**
- Almacena embeddings de 768 dimensiones
- Búsqueda por similitud coseno
- Persistencia en disco
- Puede manejar miles de documentos

**Operaciones comunes:**
```python
from rag_system.vector_store.chroma_manager import ChromaManager

chroma = ChromaManager()
stats = chroma.get_collection_stats()
print(f"Total documentos: {stats['total_documents']}")
```

---

### 🚀 Pipeline RAG Completo
**¿Dónde está?**
- **Código**: `/backend/rag_system/rag_engine/pipeline.py`
- **Documentación Completa**: [ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md) → Sección "Pipeline RAG Completo"
- **Referencia Rápida**: [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md) → "Módulos Independientes" → "Pipeline RAG Completo"

**¿Qué hace?**
- Orquesta todos los componentes
- Sincroniza → Procesa → Embedings → Almacena → Consulta → Genera
- Búsqueda híbrida (semántica + metadatos + expansión)
- Genera respuestas con LLM

**Uso básico:**
```python
from rag_system.rag_engine.pipeline import RAGPipeline

pipeline = RAGPipeline()

# Sincronizar y procesar
pipeline.sync_and_process_documents()

# Consultar
result = pipeline.query("¿Qué es la democracia?")
print(result['answer'])
```

---

### ⚙️ Configuración Central
**¿Dónde está?**
- **Código**: `/backend/rag_system/config.py`
- **Documentación Completa**: [ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md) → Sección "Configuración Central"
- **Referencia Rápida**: [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md) → "Configuraciones Clave"

**¿Qué contiene?**
- Rutas y directorios
- Configuración de Google Drive
- Parámetros de chunking
- Configuración de embeddings
- Configuración del motor RAG
- API keys y proveedores

**Variables de entorno importantes:**
```bash
GOOGLE_DRIVE_FOLDER_ID="..."
GOOGLE_API_KEY="..."
OPENROUTER_API_KEY="..."
ENABLE_GOOGLE_DRIVE="true"
```

---

### 🌐 API REST
**¿Dónde está?**
- **Código**: `/backend/api/views.py`
- **URLs**: `/backend/api/urls.py`
- **Documentación Completa**: [ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md) → Sección "APIs y Endpoints"
- **Referencia Rápida**: [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md) → "Endpoints API Principales"

**Endpoints principales:**
- `GET /api/rag/status/` - Estado del sistema
- `POST /api/rag/query/` - Consulta RAG
- `POST /api/rag/chat/` - Chat conversacional
- `POST /api/rag/sync/` - Sincronización manual

**Ejemplo:**
```bash
curl -X POST http://localhost:8000/api/rag/query/ \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué es la democracia?", "top_k": 5}'
```

---

## 🔍 Búsqueda Rápida por Caso de Uso

### "Quiero sincronizar documentos desde Google Drive"
1. **Configurar**: Variables de entorno (ver [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md) → "Variables de Entorno")
2. **Ejecutar**: `python manage.py sync_drive_full`
3. **Detalles**: [ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md) → "Sincronización con Google Drive"

### "Quiero entender cómo se generan los embeddings"
1. **Quick view**: [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md) → "Módulos Independientes" → "Sistema de Embeddings"
2. **Detalles completos**: [ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md) → "Sistema de Embeddings"

### "Quiero hacer una consulta RAG"
1. **Ejemplo rápido**: [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md) → "Módulos Independientes" → "Pipeline RAG Completo"
2. **API HTTP**: [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md) → "Endpoints API Principales"
3. **Flujo completo**: [ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md) → "Pipeline RAG Completo"

### "Quiero procesar un PDF manualmente"
1. **Código de ejemplo**: [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md) → "Módulos Independientes" → "Procesador PDF"
2. **Detalles técnicos**: [ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md) → "Procesamiento de Documentos"

### "El sistema no funciona, necesito debug"
1. **Troubleshooting**: [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md) → "Debug y Troubleshooting"
2. **Logs**: `tail -f /backend/data/rag_system.log`
3. **Estado**: `python manage.py rag_manage --status`

### "Quiero agregar soporte para un nuevo tipo de documento"
1. **Pasos**: [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md) → "Extender el Sistema" → "Agregar Nuevo Tipo de Documento"
2. **Arquitectura**: [ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md) → "Procesamiento de Documentos"

---

## 📊 Métricas de la Documentación

| Documento | Páginas | Secciones | Ejemplos de Código | Tiempo de Lectura |
|-----------|---------|-----------|---------------------|-------------------|
| ARQUITECTURA_BACKEND_RAG.md | ~25 | 9 principales | 20+ | 30-45 min |
| GUIA_RAPIDA_BACKEND.md | ~12 | 15 principales | 15+ | 10-15 min |
| **Total** | ~37 | 24 | 35+ | 40-60 min |

---

## 🎯 Resumen Ejecutivo

### Tres Puntos Clave del Sistema

1. **Sistema RAG Modular**
   - Componentes independientes pero integrados
   - Cada módulo puede usarse por separado
   - Pipeline central orquesta todo

2. **Flujo: Drive → Embeddings → Búsqueda**
   - Google Drive descarga documentos
   - PDFProcessor extrae y divide texto
   - EmbeddingManager crea vectores (768D)
   - ChromaDB almacena y busca
   - LLM genera respuestas

3. **Configuración Centralizada**
   - Todo en `/backend/rag_system/config.py`
   - Variables de entorno para producción
   - Fácil de personalizar

---

## 🚀 Primeros Pasos

### Setup Básico (5 minutos)
```bash
# 1. Navegar al backend
cd /backend

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar base de datos
python manage.py migrate

# 4. Crear superusuario
python manage.py createsuperuser

# 5. Verificar estado
python manage.py rag_manage --status
```

### Primera Sincronización (2 minutos)
```bash
# 1. Configurar Google Drive
export GOOGLE_DRIVE_FOLDER_ID="tu_folder_id"
export ENABLE_GOOGLE_DRIVE="true"

# 2. Sincronizar
python manage.py sync_drive_full

# 3. Verificar
python manage.py rag_manage --status
```

### Primera Consulta (1 minuto)
```python
from rag_system.rag_engine.pipeline import RAGPipeline

pipeline = RAGPipeline()
result = pipeline.query("Dame un resumen de los documentos")
print(result['answer'])
```

---

## 📞 Soporte y Recursos

### Documentación del Proyecto
- [ARQUITECTURA_BACKEND_RAG.md](./ARQUITECTURA_BACKEND_RAG.md) - Documentación técnica completa
- [GUIA_RAPIDA_BACKEND.md](./GUIA_RAPIDA_BACKEND.md) - Guía de referencia rápida

### Enlaces Externos
- **LangChain**: https://python.langchain.com/
- **ChromaDB**: https://docs.trychroma.com/
- **Sentence Transformers**: https://www.sbert.net/
- **Google Drive API**: https://developers.google.com/drive

### Repositorio
- **GitHub**: https://github.com/HugoX2003/nisira-assistant

---

## 🔄 Actualizaciones

**Última actualización**: Noviembre 2025
**Versión de la documentación**: 1.0.0
**Versión del sistema**: 1.0.0

---

## ✅ Checklist de Lectura

Para asegurarte de que entiendes el sistema completo:

- [ ] He leído el "Resumen Ejecutivo" de este índice
- [ ] He revisado la "Ubicación Rápida de Componentes" en GUIA_RAPIDA_BACKEND.md
- [ ] He entendido el "Flujo Visual Simplificado" en GUIA_RAPIDA_BACKEND.md
- [ ] He leído la "Visión General" en ARQUITECTURA_BACKEND_RAG.md
- [ ] He revisado los "Componentes Principales" en ARQUITECTURA_BACKEND_RAG.md
- [ ] He entendido el "Flujo de Procesamiento" completo
- [ ] He probado el "Quick Start para Testing" en GUIA_RAPIDA_BACKEND.md
- [ ] Sé dónde buscar cuando tengo un problema específico

---

**¡Bienvenido al equipo de Nisira Assistant!** 🎉

Si tienes preguntas o sugerencias sobre esta documentación, por favor abre un issue en el repositorio.
