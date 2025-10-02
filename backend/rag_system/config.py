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
GOOGLE_DRIVE_CONFIG = {
    "credentials_file": BASE_DIR / "credentials.json",
    "credentials_path": str(BASE_DIR / "credentials.json"),  # Ruta completa para compatibilidad
    "token_file": DATA_DIR / "token.json",
    "scopes": ["https://www.googleapis.com/auth/drive.readonly"],
    "sync_folder_name": "Prueba RAG",  # Carpeta en Drive del administrador
    "folder_id": os.getenv("GOOGLE_DRIVE_FOLDER_ID", ""),  # ID de la carpeta en Drive
    "download_path": str(DOCUMENTS_DIR),  # Directorio local para descargas
    "supported_formats": [".pdf", ".txt", ".docx", ".doc", ".pptx", ".xlsx"],  # Formatos soportados
    "sync_interval": 300,  # 5 minutos
    "max_file_size": 50 * 1024 * 1024,  # 50MB máximo
}

# ===== PROCESAMIENTO DE DOCUMENTOS =====
DOCUMENT_PROCESSING_CONFIG = {
    "supported_formats": [".pdf", ".txt", ".docx", ".doc", ".pptx", ".xlsx"],
    "chunk_size": 1000,      # Tamaño de chunk para procesadores
    "max_chunk_size": 1000,  # Tokens por chunk
    "chunk_overlap": 200,    # Overlap entre chunks
    "min_chunk_size": 100,   # Mínimo tamaño de chunk
    "extract_metadata": True,  # Extraer metadatos de documentos
    "preserve_structure": True,  # Mantener estructura de documentos
    "clean_text": True,     # Limpiar texto extraído
}

# ===== APIs GRATUITAS CONFIGURACIÓN =====
API_CONFIG = {
    "google_api_key": os.getenv("GOOGLE_API_KEY", ""),  # API key para Gemini
    "gemini": {
        "api_key_env": "GOOGLE_API_KEY",
        "model_name": "gemini-1.5-flash",  # Modelo gratuito
        "chat_model_name": "gemini-1.5-flash",  # Modelo para chat
        "embedding_model": "models/embedding-001",
        "max_tokens": 8192,
        "temperature": 0.7,
        "requests_per_minute": 15,  # Límite gratuito
    },
    "huggingface": {
        "model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  # Modelo multilingüe optimizado
        "device": "cpu",  # Cambiar a "cuda" si tienes GPU
        "max_seq_length": 512,
    },
    "fallback_embedding": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
}

# ===== CHROMADB CONFIGURACIÓN =====
CHROMA_CONFIG = {
    "persist_directory": str(CHROMA_DIR),
    "collection_name": "rag_documents",
    "distance_function": "cosine",  # cosine, l2, ip
    "embedding_dimension": 768,     # Para all-MiniLM-L6-v2
}

# ===== RAG ENGINE CONFIGURACIÓN =====
RAG_CONFIG = {
    "retrieval": {
        "top_k": 5,              # Documentos a recuperar
        "similarity_threshold": 0.7,  # Umbral de similitud
        "rerank": True,          # Re-ranking de resultados
        "max_context_length": 4000,   # Máximo contexto para LLM
    },
    "generation": {
        "system_prompt": """Eres un asistente inteligente que responde preguntas basándote únicamente en el contexto proporcionado. 

Instrucciones:
1. Usa SOLO la información del contexto para responder
2. Si la información no está en el contexto, di que no tienes esa información
3. Sé preciso y conciso
4. Mantén un tono profesional y amigable
5. Cita las fuentes cuando sea relevante

Contexto: {context}

Pregunta: {question}

Respuesta:""",
        "max_response_tokens": 1000,
        "temperature": 0.3,
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
    """Validar que la configuración esté completa"""
    status = {
        "directories": True,
        "google_credentials": False,
        "api_keys": False,
    }
    
    # Validar directorios
    try:
        ensure_directories()
        status["directories"] = True
    except Exception:
        status["directories"] = False
    
    # Validar credenciales de Google
    status["google_credentials"] = GOOGLE_DRIVE_CONFIG["credentials_file"].exists()
    
    # Validar API keys
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