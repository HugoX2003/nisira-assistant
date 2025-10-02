"""
RAG Pipeline
===========

Pipeline principal que coordina todos los componentes del sistema RAG:
- Sincronización con Google Drive
- Procesamiento de documentos
- Generación de embeddings
- Almacenamiento en ChromaDB
- Búsqueda y generación de respuestas
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import asyncio
from pathlib import Path

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    LANGCHAIN_GOOGLE_AVAILABLE = True
except ImportError:
    LANGCHAIN_GOOGLE_AVAILABLE = False

from ..config import RAG_CONFIG, API_CONFIG
from ..drive_sync.drive_manager import GoogleDriveManager
from ..document_processing.pdf_processor import PDFProcessor
from ..document_processing.text_processor import TextProcessor
from ..embeddings.embedding_manager import EmbeddingManager
from ..vector_store.chroma_manager import ChromaManager

logger = logging.getLogger(__name__)

class RAGPipeline:
    """
    Pipeline principal del sistema RAG
    """
    
    def __init__(self):
        self.config = RAG_CONFIG
        
        # Inicializar componentes
        self.drive_manager = GoogleDriveManager()
        self.pdf_processor = PDFProcessor()
        self.text_processor = TextProcessor()
        self.embedding_manager = EmbeddingManager()
        self.chroma_manager = ChromaManager()
        
        # Configurar LLM para generación
        self.llm = None
        self._initialize_llm()
        
        # Estadísticas de procesamiento
        self.stats = {
            'documents_processed': 0,
            'chunks_created': 0,
            'embeddings_generated': 0,
            'last_sync': None,
            'last_processing': None
        }
    
    def _initialize_llm(self):
        """Inicializar modelo de lenguaje para generación"""
        if not LANGCHAIN_GOOGLE_AVAILABLE:
            logger.warning("LangChain Google no disponible, solo búsqueda disponible")
            return
        
        if not API_CONFIG['google_api_key']:
            logger.warning("API key de Google no configurada")
            return
        
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=API_CONFIG['google_api_key'],
                temperature=0.7,
                max_tokens=1024
            )
            logger.info("LLM Google Gemini inicializado")
        except Exception as e:
            logger.error(f"Error inicializando LLM: {e}")
    
    def is_ready(self) -> Dict[str, bool]:
        """Verificar estado de todos los componentes"""
        return {
            'drive_manager': self.drive_manager.is_authenticated(),
            'pdf_processor': self.pdf_processor.is_available(),
            'text_processor': self.text_processor.is_available(),
            'embedding_manager': self.embedding_manager.is_ready(),
            'chroma_manager': self.chroma_manager.is_ready(),
            'llm_available': self.llm is not None
        }
    
    def sync_and_process_documents(self, force_reprocess: bool = False) -> Dict[str, Any]:
        """Sincronizar documentos desde Google Drive y procesarlos"""
        logger.info("Iniciando sincronización y procesamiento de documentos")
        
        readiness = self.is_ready()
        
        if not readiness['drive_manager']:
            return {
                "success": False,
                "error": "Google Drive no está configurado correctamente"
            }
        
        if not readiness['embedding_manager'] or not readiness['chroma_manager']:
            return {
                "success": False,
                "error": "Sistema de embeddings o ChromaDB no está listo"
            }
        
        try:
            # 1. Sincronizar documentos desde Google Drive
            logger.info("Sincronizando documentos desde Google Drive...")
            sync_result = self.drive_manager.sync_documents()
            
            if not sync_result['success']:
                return {
                    "success": False,
                    "error": f"Error en sincronización: {sync_result.get('error', 'Unknown')}"
                }
            
            self.stats['last_sync'] = datetime.now().isoformat()
            
            # 2. Procesar documentos
            documents_to_process = []
            
            if force_reprocess:
                download_path = self.drive_manager.download_path
                if os.path.exists(download_path):
                    for file_name in os.listdir(download_path):
                        file_path = os.path.join(download_path, file_name)
                        if os.path.isfile(file_path):
                            documents_to_process.append(file_path)
            else:
                for file_info in sync_result.get('downloaded_files', []):
                    documents_to_process.append(file_info['path'])
            
            if not documents_to_process:
                logger.info("No hay documentos nuevos para procesar")
                return {
                    "success": True,
                    "message": "No hay documentos nuevos para procesar",
                    "sync_result": sync_result,
                    "processed_documents": 0
                }
            
            # 3. Procesar cada documento
            logger.info(f"Procesando {len(documents_to_process)} documentos...")
            
            all_chunks = []
            processing_results = []
            
            for doc_path in documents_to_process:
                try:
                    result = self.process_document(doc_path)
                    processing_results.append(result)
                    
                    if result['success']:
                        all_chunks.extend(result['chunks'])
                        self.stats['documents_processed'] += 1
                        logger.info(f"Procesado: {os.path.basename(doc_path)}")
                    else:
                        logger.error(f"Error procesando {os.path.basename(doc_path)}: {result.get('error', 'Unknown')}")
                        
                except Exception as e:
                    logger.error(f"Error inesperado procesando {doc_path}: {e}")
                    processing_results.append({
                        "success": False,
                        "file_path": doc_path,
                        "error": str(e)
                    })
            
            # 4. Generar embeddings
            if all_chunks:
                logger.info(f"Generando embeddings para {len(all_chunks)} chunks...")
                
                chunk_texts = [chunk['text'] for chunk in all_chunks]
                embeddings = self.embedding_manager.create_embeddings_batch(chunk_texts)
                
                valid_chunks = []
                valid_embeddings = []
                
                for chunk, embedding in zip(all_chunks, embeddings):
                    if embedding is not None:
                        valid_chunks.append(chunk)
                        valid_embeddings.append(embedding)
                
                self.stats['chunks_created'] += len(valid_chunks)
                self.stats['embeddings_generated'] += len(valid_embeddings)
                
                # 5. Almacenar en ChromaDB
                if valid_chunks:
                    logger.info(f"Almacenando {len(valid_chunks)} chunks en ChromaDB...")
                    
                    storage_success = self.chroma_manager.add_documents(
                        valid_chunks, 
                        valid_embeddings
                    )
                    
                    if not storage_success:
                        logger.error("Error almacenando en ChromaDB")
                        return {
                            "success": False,
                            "error": "Error almacenando documentos en base de datos vectorial"
                        }
            
            self.stats['last_processing'] = datetime.now().isoformat()
            
            successful_docs = len([r for r in processing_results if r['success']])
            failed_docs = len(processing_results) - successful_docs
            
            result = {
                "success": True,
                "sync_result": sync_result,
                "processing_summary": {
                    "total_documents": len(documents_to_process),
                    "successful": successful_docs,
                    "failed": failed_docs,
                    "total_chunks": len(all_chunks),
                    "valid_chunks": len(valid_chunks) if all_chunks else 0
                },
                "processing_results": processing_results,
                "stats": self.stats
            }
            
            logger.info(f"Procesamiento completado: {successful_docs}/{len(documents_to_process)} documentos exitosos")
            
            return result
            
        except Exception as e:
            logger.error(f"Error en sincronización y procesamiento: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Procesar un documento individual"""
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"Archivo no encontrado: {file_path}"
            }
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.pdf':
                if not self.pdf_processor.is_available():
                    return {
                        "success": False,
                        "error": "Procesador PDF no disponible"
                    }
                result = self.pdf_processor.process_pdf(file_path)
            
            elif file_ext in self.text_processor.get_supported_formats():
                result = self.text_processor.process_document(file_path)
            
            else:
                return {
                    "success": False,
                    "error": f"Formato no soportado: {file_ext}"
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error procesando documento {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    def query(self, question: str, top_k: int = 5, include_generation: bool = True) -> Dict[str, Any]:
        """Realizar consulta RAG completa"""
        logger.info(f"Procesando consulta: {question[:100]}...")
        
        if not question.strip():
            return {
                "success": False,
                "error": "Pregunta vacía"
            }
        
        try:
            # 1. Crear embedding de la pregunta
            query_embedding = self.embedding_manager.create_embedding(question)
            
            if query_embedding is None:
                return {
                    "success": False,
                    "error": "No se pudo crear embedding de la consulta"
                }
            
            # 2. Buscar documentos relevantes con threshold más bajo
            relevant_docs = self.chroma_manager.search_similar(
                query_embedding, 
                n_results=top_k,
                similarity_threshold=0.15  # Threshold bajo para no filtrar demasiado
            )
            
            if not relevant_docs:
                return {
                    "success": True,
                    "question": question,
                    "relevant_documents": [],
                    "answer": "No se encontraron documentos relevantes para responder la pregunta.",
                    "sources": []
                }
            
            # 3. Preparar contexto
            context_parts = []
            sources = []
            
            for i, doc in enumerate(relevant_docs):
                context_parts.append(f"Documento {i+1}:\\n{doc['document']}")
                
                metadata = doc['metadata']
                source_info = {
                    "rank": doc['rank'],
                    "similarity_score": doc['similarity_score'],
                    "file_name": metadata.get('file_name', 'unknown'),
                    "chunk_id": metadata.get('chunk_id', 0)
                }
                
                if 'page' in metadata:
                    source_info['page'] = metadata['page']
                
                sources.append(source_info)
            
            context = "\\n\\n".join(context_parts)
            
            # 4. Generar respuesta si está habilitado
            answer = None
            
            if include_generation and self.llm:
                try:
                    prompt = self._create_rag_prompt(question, context)
                    response = self.llm.invoke(prompt)
                    answer = response.content if hasattr(response, 'content') else str(response)
                    
                except Exception as e:
                    logger.error(f"Error generando respuesta: {e}")
                    answer = f"Error generando respuesta automática: {e}"
            
            result = {
                "success": True,
                "question": question,
                "relevant_documents": relevant_docs,
                "context": context,
                "sources": sources,
                "answer": answer,
                "generation_used": answer is not None
            }
            
            logger.info(f"Consulta procesada: {len(relevant_docs)} documentos encontrados")
            
            return result
            
        except Exception as e:
            logger.error(f"Error en consulta RAG: {e}")
            return {
                "success": False,
                "error": str(e),
                "question": question
            }
    
    def _create_rag_prompt(self, question: str, context: str) -> str:
        """Crear prompt para generación RAG"""
        prompt = f"""Eres un asistente inteligente que responde preguntas basándose en documentos específicos.

Contexto de documentos relevantes:
{context}

Pregunta: {question}

Instrucciones:
1. Responde únicamente basándote en la información proporcionada en el contexto
2. Si la información no está en el contexto, indica que no tienes esa información
3. Sé preciso y cita información específica cuando sea relevante
4. Mantén un tono profesional y útil
5. Si hay múltiples documentos, puedes combinar información de ellos

Respuesta:"""
        
        return prompt
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema RAG"""
        return {
            "readiness": self.is_ready(),
            "stats": self.stats,
            "drive_status": self.drive_manager.get_sync_status(),
            "embedding_stats": self.embedding_manager.get_stats(),
            "chroma_stats": self.chroma_manager.get_collection_stats(),
            "supported_formats": {
                "pdf": self.pdf_processor.get_supported_formats(),
                "text": self.text_processor.get_supported_formats()
            }
        }
    
    def reset_system(self) -> Dict[str, Any]:
        """Resetear completamente el sistema"""
        logger.warning("Iniciando reset completo del sistema RAG")
        
        try:
            chroma_reset = self.chroma_manager.reset_collection()
            self.embedding_manager.clear_cache()
            
            self.stats = {
                'documents_processed': 0,
                'chunks_created': 0,
                'embeddings_generated': 0,
                'last_sync': None,
                'last_processing': None
            }
            
            result = {
                "success": chroma_reset,
                "chroma_reset": chroma_reset,
                "cache_cleared": True,
                "stats_reset": True
            }
            
            if chroma_reset:
                logger.info("Sistema RAG reseteado completamente")
            else:
                logger.error("Error reseteando sistema RAG")
            
            return result
            
        except Exception as e:
            logger.error(f"Error en reset del sistema: {e}")
            return {
                "success": False,
                "error": str(e)
            }