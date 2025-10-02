"""
Sistema RAG Modular
==================

Sistema completo de Retrieval-Augmented Generation que incluye:
- Sincronización con Google Drive
- Procesamiento avanzado de documentos
- Embeddings con LangChain y APIs gratuitas
- Base de datos vectorial ChromaDB
- Motor RAG completo

Autor: Nisira Assistant Team
Versión: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Nisira Assistant Team"

from .config import (
    GOOGLE_DRIVE_CONFIG,
    DOCUMENT_PROCESSING_CONFIG,
    API_CONFIG,
    CHROMA_CONFIG,
    RAG_CONFIG,
    validate_configuration
)

# Importaciones principales de cada módulo
try:
    from .drive_sync.drive_manager import GoogleDriveManager
    from .document_processing.pdf_processor import PDFProcessor
    from .document_processing.text_processor import TextProcessor
    from .embeddings.embedding_manager import EmbeddingManager
    from .vector_store.chroma_manager import ChromaManager
    from .rag_engine.pipeline import RAGPipeline
    
    RAG_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Algunos módulos RAG no están disponibles: {e}")
    print("📦 Instala las dependencias con: pip install -r requirements.txt")
    RAG_MODULES_AVAILABLE = False

def initialize_rag_system():
    """
    Inicializar el sistema RAG completo
    
    Returns:
        dict: Estado de inicialización de cada componente
    """
    if not RAG_MODULES_AVAILABLE:
        return {
            "success": False,
            "error": "Módulos RAG no disponibles. Instalar dependencias."
        }
    
    # Validar configuración
    config_status = validate_configuration()
    
    if not all(config_status.values()):
        return {
            "success": False,
            "config_status": config_status,
            "error": "Configuración incompleta"
        }
    
    try:
        # Inicializar componentes principales
        drive_manager = GoogleDriveManager()
        embedding_manager = EmbeddingManager()
        chroma_manager = ChromaManager()
        rag_pipeline = RAGPipeline()
        
        return {
            "success": True,
            "components": {
                "drive_manager": True,
                "embedding_manager": True,
                "chroma_manager": True,
                "rag_pipeline": True
            },
            "config_status": config_status
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "config_status": config_status
        }

def get_rag_status():
    """
    Obtener estado actual del sistema RAG
    
    Returns:
        dict: Estado detallado del sistema
    """
    status = {
        "version": __version__,
        "modules_available": RAG_MODULES_AVAILABLE,
        "configuration": validate_configuration()
    }
    
    if RAG_MODULES_AVAILABLE:
        try:
            # Verificar estado de componentes
            status["components"] = {
                "google_drive": GoogleDriveManager().is_authenticated(),
                "embeddings": EmbeddingManager().is_ready(),
                "vector_store": ChromaManager().is_ready(),
            }
        except Exception as e:
            status["components_error"] = str(e)
    
    return status

# Funciones de conveniencia para Django
def process_document(file_path: str):
    """Procesar un documento individual"""
    if not RAG_MODULES_AVAILABLE:
        raise ImportError("Módulos RAG no disponibles")
    
    pipeline = RAGPipeline()
    return pipeline.process_document(file_path)

def query_rag(question: str, top_k: int = 5):
    """Realizar consulta RAG"""
    if not RAG_MODULES_AVAILABLE:
        raise ImportError("Módulos RAG no disponibles")
    
    pipeline = RAGPipeline()
    return pipeline.query(question, top_k=top_k)

def sync_drive_documents():
    """Sincronizar documentos desde Google Drive"""
    if not RAG_MODULES_AVAILABLE:
        raise ImportError("Módulos RAG no disponibles")
    
    drive_manager = GoogleDriveManager()
    return drive_manager.sync_documents()

# Información del módulo
__all__ = [
    "initialize_rag_system",
    "get_rag_status", 
    "process_document",
    "query_rag",
    "sync_drive_documents",
    "RAG_MODULES_AVAILABLE",
    "GOOGLE_DRIVE_CONFIG",
    "DOCUMENT_PROCESSING_CONFIG",
    "API_CONFIG",
    "CHROMA_CONFIG",
    "RAG_CONFIG"
]