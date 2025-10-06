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
    "folder_id": os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1wAYnaln3Dg-MnFy6rNhwqPlh7Ouc4EP8"),  # ID de la carpeta en Drive
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
        "model_name": "gemini-2.0-flash-exp",  # Modelo más reciente
        "chat_model_name": "gemini-2.0-flash-exp", 
        "embedding_model": "models/text-embedding-004",
        "max_tokens": 8192,
        "temperature": 0.7,
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

# ===== RAG ENGINE CONFIGURACIÓN =====
RAG_CONFIG = {
    "retrieval": {
        "top_k": 15,              # MÁS documentos para capturar más contexto
        "similarity_threshold": 0.005,  # Threshold MUY bajo para máxima cobertura
        "rerank": True,          # Re-ranking de resultados
        "max_context_length": 12000,   # MÁS contexto para mejor comprensión
        "diversity_threshold": 0.4,  # MÁS diversidad en resultados
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
        
        "system_prompt": """Eres un asistente académico especializado en análisis de textos políticos y sociales peruanos. Tu tarea es analizar únicamente el contexto proporcionado y extraer información precisa, especialmente citas bibliográficas.

REGLAS ESTRICTAS:
1. SIEMPRE analiza TODO el contexto proporcionado línea por línea
2. Si encuentras cualquier cita bibliográfica (como Arias(2020), García(2019), etc.), SIEMPRE inclúyela en tu respuesta
3. Para consultas sobre autores específicos, busca exhaustivamente todas las menciones
4. Extrae TODAS las citas textuales relevantes y ponlas entre comillas
5. Si un documento menciona teorías, clasificaciones o análisis, enuméralos completamente
6. Identifica SIEMPRE el nombre del archivo fuente cuando sea relevante
7. Para citas específicas como "Arias(2020)", busca tanto el autor como el año en el contexto
8. Si no encuentras información específica, di claramente que no está en el contexto proporcionado
6. Si hay información pero es parcial, especifica qué información tienes disponible

ESTRUCTURA OBLIGATORIA:
- Identificar AUTOR del contenido si está presente
- Citar textualmente las partes relevantes entre comillas
- Proporcionar el documento fuente específico
- Enumerar puntos o teorías si las hay

IMPORTANTE: Antes de responder "no tengo información", verifica TODO el contexto línea por línea.

Contexto académico: {context}

Pregunta: {question}

Respuesta académica fundamentada:""",
        "max_response_tokens": 1500,
        "temperature": 0.2,  # Más determinista para precisión académica
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