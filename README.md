# 🤖 Nisira Assistant

Sistema inteligente de asistencia conversacional con **RAG (Retrieval-Augmented Generation)** para consultas sobre documentos académicos y políticos. Combina un frontend React moderno con un backend Django REST API, sistema de embeddings multilingües y base de datos vectorial.

---

## 📋 Tabla de Contenidos

- [Características Principales](#-características-principales)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Stack Tecnológico](#-stack-tecnológico)
- [Prerequisitos](#-prerequisitos)
- [Instalación y Configuración](#-instalación-y-configuración)
- [Uso del Sistema](#-uso-del-sistema)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Componentes Principales](#-componentes-principales)
- [API Endpoints](#-api-endpoints)
- [Sistema RAG](#-sistema-rag)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Características Principales

### 🎯 Funcionalidades Core
- **Chat Inteligente con RAG**: Respuestas contextualizadas basadas en documentos indexados
- **Búsqueda Semántica**: Recuperación de documentos relevantes usando embeddings multilingües
- **Sincronización Google Drive**: Importación automática de documentos desde carpetas de Drive
- **Autenticación JWT**: Sistema seguro de usuarios con sesiones persistentes (24h)
- **Gestión de Conversaciones**: Historial completo de chats con contexto
- **Procesamiento de Documentos**: Soporte para PDF con chunking inteligente
- **Base de Datos Vectorial**: ChromaDB para almacenamiento y búsqueda eficiente
- **UI Moderna**: Interfaz dark theme con referencias de fuentes estilizadas

### 🔧 Características Técnicas
- **Embeddings Locales**: HuggingFace paraphrase-multilingual-MiniLM-L12-v2 (gratis)
- **Generación con IA**: Google Gemini 2.0 Flash para respuestas naturales
- **Auto-configuración**: Bootstrap automático de base de datos y superusuario
- **CORS Habilitado**: Permite conexiones cross-origin para desarrollo
- **Timeouts Optimizados**: 180s para consultas RAG complejas

---

## 🏗️ Arquitectura del Sistema

### Diagrama de Alto Nivel (Nivel 1 - Contexto)

```
┌─────────────────┐
│                 │
│     Usuario     │
│                 │
└────────┬────────┘
         │
         │ HTTPS
         ▼
┌─────────────────────────────────────────────────────┐
│                                                     │
│            Nisira Assistant System                  │
│                                                     │
│  ┌──────────────┐          ┌──────────────────┐   │
│  │   Frontend   │◄────────►│     Backend      │   │
│  │    React     │   API    │  Django + RAG    │   │
│  └──────────────┘          └──────────────────┘   │
│                                                     │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │   Google Gemini API   │
            │   (Text Generation)   │
            └───────────────────────┘
```

### Arquitectura de Componentes (Nivel 2 - Contenedores)

```
┌────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │    Login     │  │     Chat     │  │   API Service    │    │
│  │  Component   │  │  Component   │  │  (axios+JWT)     │    │
│  └──────────────┘  └──────────────┘  └──────────────────┘    │
│         │                 │                    │               │
└─────────┼─────────────────┼────────────────────┼───────────────┘
          │                 │                    │
          └─────────────────┴────────────────────┘
                            │
                    HTTP/JSON + JWT
                            │
┌───────────────────────────┴─────────────────────────────────────┐
│                         BACKEND                                 │
│  ┌────────────────┐              ┌─────────────────────────┐   │
│  │   API Views    │              │      RAG System         │   │
│  │  - auth/token  │              │                         │   │
│  │  - /api/rag/   │◄────────────►│  ┌──────────────────┐  │   │
│  │  - /api/conv/  │              │  │  RAG Pipeline    │  │   │
│  └────────────────┘              │  └──────────────────┘  │   │
│          │                       │           │             │   │
│          │                       │  ┌────────▼─────────┐  │   │
│  ┌───────▼────────┐              │  │  Embedding Mgr   │  │   │
│  │   MySQL DB     │              │  │  (HuggingFace)   │  │   │
│  │  - Users       │              │  └──────────────────┘  │   │
│  │  - Convs       │              │           │             │   │
│  │  - Messages    │              │  ┌────────▼─────────┐  │   │
│  └────────────────┘              │  │   ChromaDB       │  │   │
│                                  │  │ (Vector Store)   │  │   │
│                                  │  └──────────────────┘  │   │
│                                  └─────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Google Gemini API   │
                    │   (LLM Generation)    │
                    └───────────────────────┘
```

### Flujo de Datos RAG (Nivel 3 - Componentes)

```
1. Usuario hace pregunta
        │
        ▼
2. Frontend → POST /api/rag/chat/
        │
        ▼
3. Backend RAG Pipeline:
   ├── Genera embedding de pregunta (HuggingFace local)
   ├── Búsqueda en ChromaDB (similarity >= 0.15)
   ├── Recupera top 5 documentos relevantes
   ├── Construye prompt con contexto
   └── Llama a Gemini API para generar respuesta
        │
        ▼
4. Respuesta con fuentes → Frontend
        │
        ▼
5. UI muestra respuesta + referencias estilizadas
```

---

## 💻 Stack Tecnológico

### Frontend
| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **React** | 18.x | Framework UI |
| **Axios** | 1.x | Cliente HTTP con interceptores JWT |
| **CSS3** | - | Estilos personalizados (dark theme) |

### Backend
| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Django** | 5.2.6 | Framework web principal |
| **Django REST Framework** | 3.15.2 | API REST |
| **djangorestframework-simplejwt** | 5.4.0 | Autenticación JWT |
| **MySQL** | 8.x | Base de datos relacional |
| **mysqlclient** | 2.2.4 | Conector Python-MySQL |

### Sistema RAG
| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **LangChain** | 0.3.13 | Orquestación RAG |
| **langchain-google-genai** | 2.0.8 | Integración Gemini |
| **ChromaDB** | 0.5.23 | Base de datos vectorial |
| **Sentence Transformers** | 3.3.1 | Embeddings multilingües |
| **PyPDF2** | 3.0.1 | Procesamiento de PDFs |

### Modelos de IA
| Modelo | Dimensiones | Uso |
|--------|-------------|-----|
| **paraphrase-multilingual-MiniLM-L12-v2** | 384 | Embeddings (local, gratis) |
| **Google Gemini 2.0 Flash** | - | Generación de respuestas (API) |

---

## 📦 Prerequisitos

### Software Requerido
- **Python**: 3.10 o superior
- **Node.js**: 16.x o superior
- **npm**: 8.x o superior
- **MySQL**: 8.0 o superior

### Credenciales y API Keys
- **Google Gemini API Key**: Obtener en [Google AI Studio](https://makersuite.google.com/app/apikey)
- **MySQL Database**: Base de datos `rag_asistente` con usuario configurado

---

## 🚀 Instalación y Configuración

### 1️⃣ Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/nisira-assistant.git
cd nisira-assistant
```

### 2️⃣ Configurar Backend

#### a) Crear y Activar Entorno Virtual

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### b) Instalar Dependencias

```bash
pip install -r requirements.txt
```

#### c) Configurar Variables de Entorno

Crear archivo `backend/.env`:

```env
# Django
SECRET_KEY=tu-secret-key-aqui
DEBUG=True

# MySQL Database
DB_NAME=rag_asistente
DB_USER=root
DB_PASSWORD=tu-password
DB_HOST=localhost
DB_PORT=3306

# Google Gemini API
GOOGLE_API_KEY=tu-api-key-de-gemini

# RAG Configuration
SIMILARITY_THRESHOLD=0.15
MAX_RESULTS=5
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

#### d) Crear Base de Datos MySQL

```sql
CREATE DATABASE rag_asistente CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### e) Aplicar Migraciones

```bash
python manage.py migrate
```

El sistema tiene **auto-configuración** que creará automáticamente:
- ✅ Superusuario: `admin` / `admin`
- ✅ Tablas necesarias
- ✅ Configuración inicial

#### f) Configurar Google Drive (Opcional)

Si deseas sincronizar documentos automáticamente desde Google Drive:

1. Coloca tu archivo `credentials.json` en `backend/`
2. Configura el `folder_id` de Google Drive en `backend/rag_system/config.py`
3. Ejecuta la sincronización:

```bash
python manage.py rag_manage sync
```

**Alternativa Manual**: Coloca tus PDFs directamente en `backend/data/documents/`

#### g) Indexar Documentos

Procesa y genera embeddings de todos los documentos:

```bash
python manage.py rag_manage reindex
```

Esto procesará todos los PDFs (desde Google Drive o carpeta local) y generará embeddings con el modelo multilingüe.

#### h) Iniciar Servidor Backend

```bash
python manage.py runserver 8000
```

Servidor disponible en: `http://localhost:8000`

### 3️⃣ Configurar Frontend

#### a) Instalar Dependencias

```bash
cd frontend
npm install
```

#### b) Configurar Variables de Entorno (Opcional)

Crear archivo `frontend/.env`:

```env
REACT_APP_API_BASE=http://localhost:8000
```

Por defecto usa `http://localhost:8000` automáticamente.

#### c) Iniciar Servidor Frontend

```bash
npm start
```

Frontend disponible en: `http://localhost:3000`

---

## 🎮 Uso del Sistema

### Registro y Login

1. **Registro de Usuario**:
   - Navega a `http://localhost:3000`
   - Haz clic en "Registrarse"
   - Completa el formulario (username, email, password)

2. **Iniciar Sesión**:
   - Usa tu username y password
   - El token JWT tiene duración de **24 horas**
   - La sesión persiste incluso con F5 (refresh)

### Chat con RAG

1. **Nueva Conversación**:
   - Haz clic en "Nueva conversación"
   - Escribe tu pregunta en español

2. **Consultas Soportadas**:
   ```
   "¿Qué dice el documento sobre juventud?"
   "Explica las políticas económicas mencionadas"
   "Resume los puntos principales sobre democracia"
   ```

3. **Ver Referencias**:
   - Cada respuesta incluye las fuentes utilizadas
   - Muestra: título del documento, página y score de similitud
   - Diseño estilizado con gradientes y hover effects

### Gestión de Conversaciones

- **Cambiar de conversación**: Haz clic en el historial lateral
- **Eliminar conversación**: Botón 🗑️ en cada conversación
- **Ver mensajes anteriores**: Se cargan automáticamente al seleccionar

---

## 📁 Estructura del Proyecto

```
nisira-assistant/
│
├── backend/
│   ├── api/                          # API REST endpoints
│   │   ├── views.py                  # Vistas principales (auth, rag, convs)
│   │   ├── urls.py                   # Rutas de la API
│   │   ├── models.py                 # Modelos de Conversation y Message
│   │   └── management/commands/
│   │       └── rag_manage.py         # Comando gestión RAG
│   │
│   ├── core/                         # Configuración Django
│   │   ├── settings.py               # Settings principales + JWT config
│   │   ├── urls.py                   # URLs raíz
│   │   └── wsgi.py                   # WSGI para deploy
│   │
│   ├── rag_system/                   # Sistema RAG modular
│   │   ├── config.py                 # Configuración RAG
│   │   ├── document_processing/
│   │   │   └── pdf_processor.py      # Procesa PDFs a chunks
│   │   ├── embeddings/
│   │   │   └── embedding_manager.py  # HuggingFace embeddings
│   │   ├── vector_store/
│   │   │   └── chroma_manager.py     # Interfaz ChromaDB
│   │   └── rag_engine/
│   │       └── pipeline.py           # Pipeline RAG completo
│   │
│   ├── bootstrap/                    # Auto-configuración
│   │   ├── apps.py                   # Bootstrap app
│   │   └── auto_config.py            # Crea DB y superuser
│   │
│   ├── data/
│   │   └── documents/                # PDFs a indexar (*.pdf ignorados)
│   │
│   ├── chroma_db/                    # Base datos vectorial (ignorada)
│   │
│   ├── manage.py                     # CLI Django
│   ├── requirements.txt              # Dependencias Python
│   └── .env                          # Variables de entorno (ignorado)
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Login.js              # Componente login
│   │   │   ├── Register.js           # Componente registro
│   │   │   └── Chat.js               # Componente chat principal
│   │   │
│   │   ├── services/
│   │   │   └── api.js                # Axios + TokenManager
│   │   │
│   │   ├── styles/
│   │   │   ├── Login.css
│   │   │   ├── Register.css
│   │   │   └── Chat.css              # Estilos mejorados con gradientes
│   │   │
│   │   ├── App.js                    # Componente raíz con auth check
│   │   └── index.js                  # Entry point React
│   │
│   ├── public/
│   │   └── index.html                # HTML base
│   │
│   ├── package.json                  # Dependencias npm
│   └── .env                          # Variables entorno (opcional)
│
├── .gitignore                        # Archivos ignorados
├── LICENSE                           # Licencia del proyecto
└── README.md                         # Este archivo
```

---

## 🧩 Componentes Principales

### Backend Components

#### 1. **RAG Pipeline** (`rag_system/rag_engine/pipeline.py`)
Orquesta el flujo completo de RAG:
```python
def query(self, question: str, conversation_id: int) -> dict:
    # 1. Genera embedding de pregunta
    # 2. Busca en ChromaDB (similarity >= 0.15)
    # 3. Construye prompt con contexto
    # 4. Llama a Gemini para generar respuesta
    # 5. Guarda en DB y retorna resultado
```

**Input**: Pregunta del usuario + ID conversación  
**Output**: Respuesta generada + fuentes + metadata

#### 2. **Embedding Manager** (`rag_system/embeddings/embedding_manager.py`)
Gestiona embeddings multilingües:
```python
class EmbeddingManager:
    # Usa HuggingFace paraphrase-multilingual-MiniLM-L12-v2
    # Genera vectores de 384 dimensiones
    # Soporta español, inglés y otros idiomas
```

**Provider**: HuggingFace (local, gratis)  
**Modelo**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`  
**Dimensiones**: 384

#### 3. **ChromaDB Manager** (`rag_system/vector_store/chroma_manager.py`)
Interfaz con base de datos vectorial:
```python
class ChromaManager:
    def search_similar(self, query_embedding, n_results=10, 
                      similarity_threshold=0.15):
        # Busca documentos similares
        # Filtra por threshold
        # Retorna con metadata (página, título, score)
```

**Database**: ChromaDB (persistente)  
**Similarity Metric**: Cosine similarity  
**Threshold**: 0.15 (balanceado para español)

#### 4. **PDF Processor** (`rag_system/document_processing/pdf_processor.py`)
Procesa PDFs a chunks:
```python
class PDFProcessor:
    # Extrae texto de PDFs
    # Divide en chunks de 1000 chars (overlap 200)
    # Preserva metadata (página, archivo)
```

**Chunking**: 1000 caracteres con overlap de 200  
**Metadata**: Nombre archivo, número de página

#### 5. **API Views** (`api/views.py`)
Endpoints principales:
- `POST /auth/token/` - Login JWT
- `POST /auth/refresh/` - Renovar token
- `POST /api/rag/chat/` - Consulta RAG
- `GET /api/conversations/` - Listar conversaciones
- `GET /api/conversations/{id}/messages/` - Mensajes de conversación

### Frontend Components

#### 1. **TokenManager** (`services/api.js`)
Gestiona tokens JWT:
```javascript
class TokenManager {
    setTokens(access, refresh)      // Guarda en localStorage
    getAccessToken()                 // Recupera token activo
    refreshAccessToken()             // Renueva token expirado
    clearTokens()                    // Limpia sesión
}
```

**Persistencia**: localStorage  
**Auto-refresh**: Interceptor axios en 401

#### 2. **Chat Component** (`components/Chat.js`)
Componente principal de conversación:
- Gestión de mensajes en tiempo real
- Carga de historial de conversaciones
- Envío de consultas RAG con timeout 180s
- Renderizado de referencias con estilos mejorados

#### 3. **App Component** (`App.js`)
Componente raíz con:
- Verificación de autenticación al montar
- Redirección automática según estado de sesión
- Manejo de vistas (Login/Register/Chat)

---

## 🔌 API Endpoints

### Autenticación

#### `POST /auth/token/`
Obtener tokens JWT.

**Request**:
```json
{
  "username": "admin",
  "password": "admin"
}
```

**Response**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Token Lifetime**:
- Access: 24 horas
- Refresh: 7 días

#### `POST /auth/refresh/`
Renovar access token.

**Request**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### RAG System

#### `POST /api/rag/chat/`
Consulta RAG con generación de respuesta.

**Request**:
```json
{
  "question": "¿Qué dice el documento sobre juventud?",
  "conversation_id": 123
}
```

**Response**:
```json
{
  "answer": "Según los documentos analizados, la juventud...",
  "sources": [
    {
      "content": "Fragmento del documento...",
      "metadata": {
        "source": "documento.pdf",
        "page": 15
      },
      "similarity_score": 0.85
    }
  ],
  "conversation_id": 123,
  "message_id": 456
}
```

**Timeout**: 180 segundos (3 minutos)

### Conversaciones

#### `GET /api/conversations/`
Listar conversaciones del usuario.

**Response**:
```json
[
  {
    "id": 123,
    "title": "Consulta sobre políticas",
    "created_at": "2025-10-01T20:30:00Z",
    "updated_at": "2025-10-01T21:00:00Z"
  }
]
```

#### `GET /api/conversations/{id}/messages/`
Obtener mensajes de una conversación.

**Response**:
```json
{
  "conversation_id": 123,
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "¿Qué dice sobre juventud?",
      "timestamp": "2025-10-01T20:30:00Z"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Según los documentos...",
      "sources": [...],
      "timestamp": "2025-10-01T20:30:15Z"
    }
  ]
}
```

#### `DELETE /api/conversations/{id}/`
Eliminar conversación.

**Response**: `204 No Content`

---

## 🔍 Sistema RAG

### Configuración RAG

Archivo: `backend/rag_system/config.py`

```python
RAG_CONFIG = {
    'embedding': {
        'provider': 'huggingface',
        'model': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
        'dimension': 384
    },
    'generation': {
        'provider': 'google',
        'model': 'gemini-2.0-flash-exp',
        'temperature': 0.7
    },
    'retrieval': {
        'similarity_threshold': 0.15,
        'max_results': 5
    },
    'chunking': {
        'chunk_size': 1000,
        'chunk_overlap': 200
    }
}
```

### Comando de Gestión RAG

```bash
# Reindexar todos los documentos
python manage.py rag_manage reindex

# Ver estadísticas
python manage.py rag_manage stats

# Limpiar base vectorial
python manage.py rag_manage clear
```

### Optimización de Embeddings

**¿Por qué paraphrase-multilingual-MiniLM-L12-v2?**

1. **Multilingüe**: Optimizado para español e inglés
2. **Tamaño**: 118 MB (ligero para ejecución local)
3. **Dimensiones**: 384 (balance entre precisión y velocidad)
4. **Rendimiento**: Mejor que all-MiniLM-L6-v2 en español
5. **Costo**: $0 (ejecuta localmente)

**Comparación de modelos**:

| Modelo | Dims | Tamaño | Español | Costo |
|--------|------|--------|---------|-------|
| all-MiniLM-L6-v2 | 384 | 80MB | ⚠️ Regular | $0 |
| paraphrase-multilingual-MiniLM-L12-v2 | 384 | 118MB | ✅ Excelente | $0 |
| text-embedding-004 (Google) | 768 | API | ✅ Excelente | $$$ |

### Threshold de Similitud

**Configurado en 0.15** (bajo para español):

- `0.7-1.0`: Coincidencia casi exacta (muy restrictivo)
- `0.5-0.7`: Coincidencia alta (buen balance para inglés)
- `0.3-0.5`: Coincidencia media (recomendado para español)
- `0.15-0.3`: Coincidencia baja (captura relaciones semánticas)
- `0-0.15`: Ruido (descartado)

**Razón del threshold bajo**:
- Documentos en español tienen variaciones lingüísticas
- Queremos capturar relaciones semánticas amplias
- Gemini filtra la información irrelevante en la generación

---

## � Monitoreo y Disponibilidad

- **Endpoint principal:** `GET /status/` (sin autenticación) expone la salud de la API, worker de Drive, base de datos y vector DB junto con metadatos de build.
- **Objetivo de uptime:** `uptime_slo_target` indica la meta ≥ 95 % usada en monitors externos.
- **Runbook:** consulta `backend/docs/availability_runbook.md` para procedimientos de incidentes, mantenimiento y caos testing.
- **Chaos tests:** `python manage.py test api.tests.ChaosHealthChecksTests` simula caídas de base de datos y vector DB para validar la respuesta del endpoint.

---

## �🐛 Troubleshooting

### Backend

#### Error: "No module named 'MySQLdb'"
```bash
pip install mysqlclient
```

#### Error: "Access denied for user 'root'@'localhost'"
Verifica credenciales en `backend/.env`:
```env
DB_USER=root
DB_PASSWORD=tu-password
```

#### Error: "Table 'rag_asistente.api_conversation' doesn't exist"
```bash
python manage.py migrate
```

#### Error: ChromaDB "Dimensionality mismatch"
Reindexar con modelo correcto:
```bash
python manage.py rag_manage clear
python manage.py rag_manage reindex
```

#### Warning: "Accessing the database during app initialization"
Es un warning esperado del bootstrap automático. No afecta funcionalidad.

### Frontend

#### Error: "Failed to fetch" en Login
- Verifica que backend esté corriendo en puerto 8000
- Revisa CORS en `backend/core/settings.py`:
```python
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
```

#### Error: "Network Error" en consultas RAG
- Aumenta timeout del navegador (ya configurado en 180s)
- Verifica que el modelo Gemini no haya excedido cuota
- Revisa la API key en `backend/.env`

#### Sesión se pierde al refrescar (F5)
- Verifica que TokenManager esté exportado en `api.js`
- Revisa la consola del navegador: debe decir "✅ Token cargado"
- Confirma que el token tenga 24h de duración en `settings.py`:
```python
'ACCESS_TOKEN_LIFETIME': timedelta(hours=24)
```

### RAG System

#### No encuentra documentos relevantes
1. Verifica que los PDFs estén indexados:
```bash
python manage.py rag_manage stats
```

2. Baja el threshold si es necesario:
```python
# En backend/rag_system/config.py
'similarity_threshold': 0.10  # Más permisivo
```

3. Revisa la calidad de los PDFs (no escaneados)

#### Respuestas en inglés (debería ser español)
Asegúrate de que el prompt en `rag_engine/pipeline.py` especifique español:
```python
prompt = f"""Responde en ESPAÑOL basándote en el siguiente contexto...
```

#### Error: "Quota exceeded" de Gemini
- Has excedido la cuota diaria de Gemini API (50 requests/día en free tier)
- Espera 24 horas o actualiza a plan de pago
- Considera usar otro modelo (ej: GPT-3.5, Claude)

---

## 📊 Información para Diagramas C4

### Contexto del Sistema (Nivel 1)

**Actores**:
- **Usuario Final**: Persona que consulta documentos
- **Administrador**: Gestiona documentos y usuarios

**Sistemas Externos**:
- **Google Gemini API**: Servicio de generación de texto IA
- **HuggingFace Models**: Modelos de embeddings (descargados localmente)

**Sistema Principal**:
- **Nisira Assistant**: Sistema RAG de consulta de documentos

### Contenedores (Nivel 2)

1. **Frontend React SPA**
   - Puerto: 3000
   - Tecnología: React 18 + Axios
   - Responsabilidad: UI/UX, autenticación, visualización

2. **Backend Django API**
   - Puerto: 8000
   - Tecnología: Django 5.2.6 + DRF
   - Responsabilidad: API REST, autenticación JWT, orquestación RAG

3. **MySQL Database**
   - Puerto: 3306
   - Tecnología: MySQL 8.x
   - Responsabilidad: Usuarios, conversaciones, mensajes

4. **ChromaDB Vector Store**
   - Tecnología: ChromaDB (persistente)
   - Responsabilidad: Almacenamiento y búsqueda vectorial

5. **RAG System**
   - Componente: Módulo Python
   - Responsabilidad: Procesamiento docs, embeddings, retrieval

### Componentes (Nivel 3)

**Frontend**:
- `App.js`: Router y autenticación
- `Login.js`: Autenticación
- `Chat.js`: Interfaz conversacional
- `TokenManager`: Gestión JWT
- `api.js`: Cliente HTTP

**Backend API**:
- `auth/views`: Login, refresh, register
- `api/views`: RAG chat, conversaciones
- `api/models`: Conversation, Message
- `middleware`: JWT authentication

**RAG System**:
- `rag_engine/pipeline.py`: Orquestador principal
- `embeddings/embedding_manager.py`: HuggingFace embeddings
- `vector_store/chroma_manager.py`: Interfaz ChromaDB
- `document_processing/pdf_processor.py`: Procesamiento PDFs

### Datos (Nivel 4)

**Flujo de Datos RAG**:
1. Usuario → Pregunta → Frontend
2. Frontend → POST /api/rag/chat/ → Backend API
3. Backend → query() → RAG Pipeline
4. RAG → create_embedding() → Embedding Manager
5. Embedding Manager → vector → ChromaDB
6. ChromaDB → search_similar() → Documentos relevantes
7. RAG → prompt + contexto → Gemini API
8. Gemini → respuesta generada → RAG
9. RAG → save_message() → MySQL
10. Backend → JSON response → Frontend
11. Frontend → renderiza respuesta + fuentes

**Flujo de Autenticación**:
1. Usuario → credentials → Login
2. Login → POST /auth/token/ → Backend
3. Backend → valida → MySQL
4. Backend → genera JWT → Frontend
5. Frontend → guarda token → localStorage
6. Frontend → agrega header → todas las requests
7. Backend → verifica JWT → autoriza

---

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

---

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## 📧 Contacto

Para preguntas o soporte, contacta a través de GitHub Issues.

---

## 🗺️ Roadmap

### Funcionalidades Implementadas

- [x] Sistema RAG con embeddings multilingües
- [x] Sincronización con Google Drive
- [x] Chat con historial de conversaciones
- [x] Autenticación JWT persistente (24h)
- [x] Referencias de fuentes estilizadas

### Próximas Funcionalidades

- [ ] Soporte para más formatos (DOCX, TXT, Markdown)
- [ ] Sistema de etiquetas para documentos
- [ ] Exportación de conversaciones a PDF
- [ ] Modo offline para embeddings
- [ ] Interfaz de administración mejorada
- [ ] Métricas y analytics de uso
- [ ] Multi-tenancy para organizaciones
- [ ] Integración con más LLMs (GPT-4, Claude)
- [ ] Búsqueda avanzada con filtros
- [ ] Modo de carga incremental de documentos

---

## 📚 Referencias

- [Django Documentation](https://docs.djangoproject.com/)
- [React Documentation](https://react.dev/)
- [LangChain Docs](https://python.langchain.com/)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Google Gemini API](https://ai.google.dev/)
- [Sentence Transformers](https://www.sbert.net/)
- [JWT Authentication](https://jwt.io/)

---

**Hecho con ❤️ para la consulta inteligente de documentos académicos y políticos**
