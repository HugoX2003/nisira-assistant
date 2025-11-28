"""
Configuración del Sistema RAG
============================

Configuración centralizada para todos los módulos del sistema RAG
- Google Drive API
- Procesamiento de documentos
- Embeddings y APIs
- ChromaDB
- Motor RAG
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import logging

# ===== PATHS Y DIRECTORIOS =====
BASE_DIR = Path(__file__).parent.parent
RAG_DIR = BASE_DIR / "rag_system"
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
PROCESSED_DIR = DATA_DIR / "processed"
CHROMA_DIR = BASE_DIR / "chroma_db"

# ===== GOOGLE DRIVE CONFIGURACIÓN =====
# Intentar usar credenciales desde variable de entorno primero (para deployment)
import json
_credentials_json_env = os.getenv("GOOGLE_CREDENTIALS_JSON")
_credentials_file_path = BASE_DIR / "credentials.json"

# Si hay credenciales en env var y no existe el archivo, crearlo temporalmente
if _credentials_json_env and not _credentials_file_path.exists():
    try:
        _creds_data = json.loads(_credentials_json_env)
        _credentials_file_path.write_text(json.dumps(_creds_data, indent=2))
    except Exception as e:
        logging.warning(f"No se pudo crear credentials.json desde env var: {e}")

# Configuración de Token (OAuth2 User Credentials)
_token_json_env = os.getenv("GOOGLE_TOKEN_JSON")
_token_file_path = DATA_DIR / "token.json"

if _token_json_env and not _token_file_path.exists():
    try:
        _token_data = json.loads(_token_json_env)
        _token_file_path.write_text(json.dumps(_token_data, indent=2))
        logging.info("✅ token.json creado desde variable de entorno")
    except Exception as e:
        logging.warning(f"No se pudo crear token.json desde env var: {e}")

GOOGLE_DRIVE_CONFIG = {
    "credentials_file": _credentials_file_path,
    "credentials_path": str(_credentials_file_path),  # Ruta completa para compatibilidad
    "token_file": DATA_DIR / "token.json",
    "scopes": [
        "https://www.googleapis.com/auth/drive",  # Acceso completo a Drive (necesario para ver archivos existentes)
    ],
    "sync_folder_name": os.getenv("GOOGLE_DRIVE_FOLDER_NAME", "Prueba RAG"),  # Permitir override
    "folder_id": os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1wAYnaln3Dg-MnFy6rNhwqPlh7Ouc4EP8"),  # ID de la carpeta en Drive
    "download_path": str(DOCUMENTS_DIR),  # Directorio local para descargas
    "supported_formats": [".pdf", ".txt", ".docx", ".doc", ".pptx", ".xlsx"],  # Formatos soportados
    "sync_interval": int(os.getenv("GOOGLE_DRIVE_SYNC_INTERVAL", "300")),  # Override via env
    "max_file_size": 50 * 1024 * 1024,  # 50MB máximo
    "enabled": os.getenv("ENABLE_GOOGLE_DRIVE", "false").lower() == "true",  # Nuevo flag para desactivar Drive en prod
}

# ===== PROCESAMIENTO DE DOCUMENTOS =====
DOCUMENT_PROCESSING_CONFIG = {
    "supported_formats": [".pdf", ".txt", ".docx", ".doc", ".pptx", ".xlsx"],
    
    # Configuración de chunking por tipo de documento
    "chunk_config": {
        ".pdf": {
            "chunk_size": 1300,      # Chunks más cortos capturan detalles finos
            "chunk_overlap": 260,    # Overlap proporcional para no perder contexto
            "min_chunk_size": 180,   # Evita fragmentos diminutos
        },
        ".txt": {
            "chunk_size": 1100,      # Ajustado para textos continuos
            "chunk_overlap": 220,    
            "min_chunk_size": 150,   
        },
        ".docx": {
            "chunk_size": 1300,      # DOCX suelen tener secciones mixtas
            "chunk_overlap": 260,    
            "min_chunk_size": 180,   
        },
        "default": {
            "chunk_size": 1000,      # Fallback para otros formatos
            "chunk_overlap": 200,    
            "min_chunk_size": 100,   
        }
    },
    
    # Configuración general (mantener compatibilidad)
    "chunk_size": 1000,      # Valor por defecto (deprecado)
    "max_chunk_size": 1000,  # Tokens por chunk
    "chunk_overlap": 200,    # Overlap entre chunks (deprecado)
    "min_chunk_size": 100,   # Mínimo tamaño de chunk (deprecado)
    "extract_metadata": True,  # Extraer metadatos de documentos
    "preserve_structure": True,  # Mantener estructura de documentos
    "clean_text": True,     # Limpiar texto extraído
}

# ===== APIs GRATUITAS CONFIGURACIÓN =====
API_CONFIG = {
    "google_api_key": os.getenv("GOOGLE_API_KEY", ""),  # API key para Gemini
    "gemini": {
        "api_key_env": "GOOGLE_API_KEY",
        "model_name": "gemini-2.0-flash-exp",  # Modelo más reciente
        "chat_model_name": "gemini-2.0-flash-exp", 
        "embedding_model": "models/text-embedding-004",
        "max_tokens": 8192,
    # NOTE: For RAG responses we prefer to use the RAG-specific
    # temperature defined in the RAG configuration (see RAG_PROMPT_CONFIG
    # below). To avoid accidental divergence between general model
    # defaults and RAG behaviour, leave the model-level temperature as
    # None so it won't override RAG prompt settings.
    "temperature": None,
        "requests_per_minute": 15,  # Límite gratuito
    },
    "huggingface": {
        "model_name": "sentence-transformers/all-mpnet-base-v2",  # EL MEJOR MODELO - 768 dimensiones
        "device": "cpu",  # Cambiar a "cuda" si tienes GPU
        "max_seq_length": 512,  # Máxima calidad
        "normalize_embeddings": True,  # Normalizar para mejor similitud coseno
    },
    "fallback_embedding": "sentence-transformers/all-mpnet-base-v2"
}

# ===== CHROMADB CONFIGURACIÓN =====
CHROMA_CONFIG = {
    "persist_directory": str(CHROMA_DIR),
    "collection_name": "rag_documents",
    "distance_function": "cosine",  # cosine, l2, ip
    "embedding_dimension": 768,     # Para all-mpnet-base-v2 (MÁXIMA CALIDAD - 768 dimensiones)
}

# ===== VECTOR STORE CONFIGURACIÓN =====
VECTOR_STORE_CONFIG = {
    'backend': os.getenv('VECTOR_STORE_BACKEND', 'postgres'),  # 'postgres' o 'chroma'
    'database_url': os.getenv('DATABASE_URL'),
}

# ===== RAG ENGINE CONFIGURACIÓN =====
RAG_CONFIG = {
    "retrieval": {
        "top_k": 15,              # MÁS documentos para capturar más contexto
        "similarity_threshold": 0.005,  # Threshold MUY bajo para máxima cobertura
        "rerank": True,          # Re-ranking de resultados
        "max_context_length": 12000,   # MÁS contexto para mejor comprensión
        "diversity_threshold": 0.4,  # MÁS diversidad en resultados
        "max_per_source": 3,        # Permite múltiples chunks por documento antes de diversificar
        "citation_boost": True,   # Boost especial para chunks con citas
        "semantic_weight": 0.6,   # Peso de búsqueda semántica (60%)
        "lexical_weight": 0.4,    # Peso de búsqueda lexical (40%)
    },
    "generation": {
        # CONFIGURACIÓN MULTI-PROVEEDOR LLM
        "provider": "openrouter",  # Cambiar entre: "google", "openrouter", "groq", "together"
        
        # Google Gemini (LÍMITES ESTRICTOS)
        "google": {
            "model": "gemini-2.0-flash-exp",
            "api_key": os.getenv("GOOGLE_API_KEY"),
        },
        
        # OpenRouter (RECOMENDADO - MEJORES LÍMITES)
        "openrouter": {
            "model": "google/gemma-2-9b-it",  # Modelo más rápido y excelente calidad
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "base_url": "https://openrouter.ai/api/v1",
        },
        
        # Groq (ALTERNATIVA RÁPIDA)
        "groq": {
            "model": "llama-3.3-70b-versatile",
            "api_key": os.getenv("GROQ_API_KEY"),
            "base_url": "https://api.groq.com/openai/v1",
        },
        
        "system_prompt": """Eres un asistente académico especializado en documentación técnica. Responde de forma clara, directa y concisa.

IDIOMA: Responde SIEMPRE en ESPAÑOL. Si los documentos están en inglés, tradúcelos naturalmente manteniendo términos técnicos comunes en inglés (ej: "framework", "API", "machine learning").

FORMATO DE RESPUESTA:
- Sé directo y conciso, evita listas largas innecesarias
- Usa párrafos cortos y fluidos en lugar de muchas viñetas
- Solo usa listas cuando sea realmente necesario para claridad
- Integra las citas en el texto de forma natural: Según el documento, "..." (fuente.pdf)
- No uses títulos o secciones a menos que la respuesta sea muy larga

REGLAS:
1. Analiza TODO el contexto proporcionado antes de responder
2. Incluye citas bibliográficas si las encuentras (Autor(año))
3. Cita textualmente entre comillas las partes relevantes
4. Identifica el archivo fuente cuando sea útil
5. Si no encuentras información, dilo claramente

Contexto: {context}

Pregunta: {question}

Respuesta en español (directa y concisa):""",
        "max_response_tokens": 1500,
        "temperature": 0.3,  # Más determinista para precisión académica
    }
}

# ===== LOGGING CONFIGURACIÓN =====
LOGGING_CONFIG = {
    "level": logging.INFO,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "handlers": [
        {
            "type": "console",
            "level": logging.INFO,
        },
        {
            "type": "file",
            "level": logging.DEBUG,
            "filename": DATA_DIR / "rag_system.log",
            "max_bytes": 10 * 1024 * 1024,  # 10MB
            "backup_count": 5,
        }
    ]
}

# ===== UTILIDADES =====
def ensure_directories():
    """Crear directorios necesarios si no existen"""
    directories = [
        DATA_DIR,
        DOCUMENTS_DIR,
        PROCESSED_DIR,
        CHROMA_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        
def get_api_key(api_name: str) -> Optional[str]:
    """Obtener API key desde variables de entorno"""
    if api_name == "gemini":
        return os.getenv(API_CONFIG["gemini"]["api_key_env"])
    return None

def validate_configuration() -> Dict[str, bool]:
    """Validar que la configuración esté completa. Incluye flag para Drive"""
    status = {
        "directories": True,
        "google_credentials": False,
        "api_keys": False,
        "drive_enabled": GOOGLE_DRIVE_CONFIG.get("enabled", False),
    }

    try:
        ensure_directories()
        status["directories"] = True
    except Exception:
        status["directories"] = False

    # Credenciales solo cuentan si Drive está habilitado
    if status["drive_enabled"]:
        status["google_credentials"] = GOOGLE_DRIVE_CONFIG["credentials_file"].exists()
    else:
        status["google_credentials"] = False

    status["api_keys"] = get_api_key("gemini") is not None
    return status

# ===== CONFIGURACIÓN DJANGO INTEGRATION =====
DJANGO_INTEGRATION = {
    "app_name": "rag_system",
    "models": ["Document", "ProcessedChunk", "EmbeddingTask"],
    "middleware": ["rag_system.middleware.RAGMiddleware"],
    "api_endpoints": [
        "/api/rag/query/",
        "/api/rag/documents/",
        "/api/rag/sync/",
        "/api/rag/status/",
    ]
}

# Inicializar directorios al importar
ensure_directories()