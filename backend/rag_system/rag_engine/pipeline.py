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
import re
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import asyncio
from pathlib import Path
from time import perf_counter
from dotenv import load_dotenv

# Cargar variables de entorno al importar el módulo
load_dotenv()

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
        """Inicializar modelo de lenguaje con soporte multi-proveedor"""
        from ..config import RAG_CONFIG
        
        provider = RAG_CONFIG["generation"]["provider"]
        logger.info(f"🤖 Inicializando LLM con proveedor: {provider}")
        
        try:
            if provider == "openrouter":
                self._initialize_openrouter_llm()
            elif provider == "groq":
                self._initialize_groq_llm()
            elif provider == "google":
                self._initialize_google_llm()
            else:
                logger.error(f"❌ Proveedor no soportado: {provider}")
                return
                
        except Exception as e:
            logger.error(f"❌ Error inicializando LLM {provider}: {e}")
            # Fallback a modo solo búsqueda
            self.llm = None
    
    def _initialize_openrouter_llm(self):
        """Inicializar OpenRouter LLM"""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            logger.error("❌ langchain_openai no disponible. Instalar con: pip install langchain-openai")
            return
            
        from ..config import RAG_CONFIG
        
        config = RAG_CONFIG["generation"]["openrouter"]
        api_key = config["api_key"]
        
        if not api_key or api_key == "your_openrouter_api_key_here":
            logger.warning("❌ API key de OpenRouter no configurada")
            return
        
        self.llm = ChatOpenAI(
            model=config["model"],
            openai_api_key=api_key,
            openai_api_base=config["base_url"],
            temperature=0.7,
            max_tokens=2048
        )
        logger.info(f"✅ LLM OpenRouter inicializado: {config['model']}")
    
    def _initialize_groq_llm(self):
        """Inicializar Groq LLM"""
        try:
            from langchain_groq import ChatGroq
        except ImportError:
            logger.error("❌ langchain_groq no disponible. Instalar con: pip install langchain-groq")
            return
            
        from ..config import RAG_CONFIG
        
        config = RAG_CONFIG["generation"]["groq"]
        api_key = config["api_key"]
        
        if not api_key or api_key == "your_groq_api_key_here":
            logger.warning("❌ API key de Groq no configurada")
            return
        
        self.llm = ChatGroq(
            model=config["model"],
            groq_api_key=api_key,
            temperature=0.7,
            max_tokens=2048
        )
        logger.info(f"✅ LLM Groq inicializado: {config['model']}")
    
    def _initialize_google_llm(self):
        """Inicializar Google Gemini LLM (método original)"""
        if not LANGCHAIN_GOOGLE_AVAILABLE:
            logger.warning("❌ LangChain Google no disponible")
            return

        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            logger.warning("❌ API key de Google no configurada")
            return

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=api_key,
            temperature=0.7,
            max_tokens=1024
        )
        logger.info("✅ LLM Google Gemini inicializado")
    
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
                # Crear processor específico para PDF
                pdf_processor = PDFProcessor(file_extension=file_ext)
                if not pdf_processor.is_available():
                    return {
                        "success": False,
                        "error": "Procesador PDF no disponible"
                    }
                result = pdf_processor.process_pdf(file_path)
            
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
    
    def query(
        self,
        question: str,
        top_k: int = 5,
        include_generation: bool = True,
        collect_metrics: bool = False
    ) -> Dict[str, Any]:
        """Realizar consulta RAG completa con optimización para citas"""
        logger.info(f"Procesando consulta: {question[:100]}...")
        
        if not question.strip():
            return {
                "success": False,
                "error": "Pregunta vacía"
            }
        
        # Preparar estructura opcional de métricas
        metrics_payload: Dict[str, Any] = {
            "latency_ms": {
                "total": None,
                "embedding": None,
                "retrieval": None,
                "context": None,
                "generation": None,
                "ttft": None
            },
            "counts": {
                "requested_top_k": top_k,
                "retrieved_documents": 0
            },
            "timestamp": datetime.now().isoformat()
        }

        overall_start = perf_counter()

        try:
            # 1. Detectar si es una consulta sobre citas específicas
            is_citation_query, enhanced_query = self._enhance_citation_query(question)
            
            # 2. Usar la consulta mejorada para embeddings
            search_query = enhanced_query if is_citation_query else question
            embedding_start = perf_counter()
            query_embedding = self.embedding_manager.create_embedding(search_query)
            metrics_payload["latency_ms"]["embedding"] = round((perf_counter() - embedding_start) * 1000, 3)
            
            if query_embedding is None:
                metrics_payload["latency_ms"]["total"] = round((perf_counter() - overall_start) * 1000, 3)
                return {
                    "success": False,
                    "error": "No se pudo crear embedding de la consulta",
                    "metrics": metrics_payload if collect_metrics else None
                }
            
            # 2. BÚSQUEDA HÍBRIDA SÚPER AGRESIVA
            retrieval_start = perf_counter()
            relevant_docs = self._hybrid_search(question, enhanced_query, query_embedding, top_k)
            retrieval_end = perf_counter()
            metrics_payload["latency_ms"]["retrieval"] = round((retrieval_end - retrieval_start) * 1000, 3)
            
            if not relevant_docs:
                metrics_payload["counts"]["retrieved_documents"] = 0
                metrics_payload["latency_ms"]["total"] = round((perf_counter() - overall_start) * 1000, 3)
                return {
                    "success": True,
                    "question": question,
                    "relevant_documents": [],
                    "answer": "No se encontraron documentos relevantes para responder la pregunta.",
                    "sources": [],
                    "metrics": metrics_payload if collect_metrics else None
                }
            
            # 3. Preparar contexto
            context_start = perf_counter()
            context_parts = []
            sources = []
            
            for i, doc in enumerate(relevant_docs):
                metadata = doc['metadata']
                file_name = metadata.get('source', metadata.get('document', metadata.get('file_name', f'Documento {i+1}')))
                content_text = doc.get('content', doc.get('document', ''))
                context_parts.append(f"Fuente: {file_name}\\n{content_text}")
                
                preview_text = content_text[:200] + "..." if len(content_text) > 200 else content_text
                source_info = {
                    "rank": doc.get('rank', i + 1),
                    "similarity_score": doc.get('similarity_score', 0),
                    "file_name": metadata.get('source', metadata.get('document', metadata.get('file_name', 'unknown'))),
                    "chunk_id": metadata.get('chunk_id', 0),
                    "content": content_text,
                    "preview": preview_text
                }
                
                if 'page' in metadata:
                    source_info['page'] = metadata['page']
                
                sources.append(source_info)
            
            context = "\\n\\n".join(context_parts)
            metrics_payload["counts"]["retrieved_documents"] = len(relevant_docs)
            metrics_payload["latency_ms"]["context"] = round((perf_counter() - context_start) * 1000, 3)
            
            # 4. Generar respuesta si está habilitado
            answer = None
            
            if include_generation and self.llm:
                try:
                    generation_start = perf_counter()
                    prompt = self._create_rag_prompt(question, context)
                    ttft_ms: Optional[float] = None
                    answer_parts: List[str] = []
                    used_streaming = False

                    def _chunk_to_text(chunk: Any) -> Optional[str]:
                        content = getattr(chunk, "content", None)
                        if isinstance(content, list):
                            content = "".join(str(part) for part in content if part)
                        if not content and hasattr(chunk, "message"):
                            message_content = getattr(chunk.message, "content", None)
                            if isinstance(message_content, list):
                                message_content = "".join(str(part) for part in message_content if part)
                            if message_content:
                                content = message_content
                        if not content and hasattr(chunk, "delta"):
                            delta = getattr(chunk, "delta")
                            delta_content = getattr(delta, "content", None)
                            if isinstance(delta_content, list):
                                pieces = []
                                for item in delta_content:
                                    if isinstance(item, str):
                                        pieces.append(item)
                                    elif hasattr(item, "text"):
                                        piece = getattr(item, "text")
                                        pieces.append(piece() if callable(piece) else str(piece))
                                    else:
                                        pieces.append(str(item))
                                content = "".join(pieces)
                            elif delta_content:
                                content = delta_content
                        if not content:
                            text_attr = getattr(chunk, "text", None)
                            if callable(text_attr):
                                try:
                                    content = text_attr()
                                except TypeError:
                                    content = None
                            elif isinstance(text_attr, str) and text_attr:
                                content = text_attr
                        if isinstance(content, list):
                            content = "".join(str(part) for part in content if part)
                        return str(content) if content else None

                    if collect_metrics and hasattr(self.llm, "stream"):
                        from contextlib import nullcontext

                        stream_obj = None
                        try:
                            stream_obj = self.llm.stream(prompt)
                            context = stream_obj if hasattr(stream_obj, "__enter__") else nullcontext(stream_obj)
                            used_streaming = True
                            with context as active_stream:  # type: ignore[arg-type]
                                for chunk in active_stream:
                                    chunk_text = _chunk_to_text(chunk)
                                    if chunk_text:
                                        if ttft_ms is None:
                                            ttft_ms = round((perf_counter() - generation_start) * 1000, 3)
                                        answer_parts.append(chunk_text)
                        except Exception as stream_error:  # pragma: no cover - depende del backend
                            used_streaming = False
                            logger.warning("Streaming LLM falló, usando invoke estándar: %s", stream_error)
                        finally:
                            if stream_obj and hasattr(stream_obj, "close"):
                                try:
                                    stream_obj.close()
                                except Exception:  # pragma: no cover - best effort
                                    pass

                    if used_streaming and answer_parts:
                        answer = "".join(answer_parts).strip() or None
                    else:
                        response = self.llm.invoke(prompt)
                        answer = response.content if hasattr(response, 'content') else str(response)
                        ttft_ms = ttft_ms or None
                        used_streaming = False

                    generation_end = perf_counter()
                    metrics_payload["latency_ms"]["generation"] = round((generation_end - generation_start) * 1000, 3)
                    metrics_payload["latency_ms"]["ttft"] = ttft_ms or metrics_payload["latency_ms"]["generation"]
                    
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
            
            metrics_payload["latency_ms"]["total"] = round((perf_counter() - overall_start) * 1000, 3)
            if collect_metrics:
                result["metrics"] = metrics_payload
            
            logger.info(f"Consulta procesada: {len(relevant_docs)} documentos encontrados")
            
            return result
            
        except Exception as e:
            logger.error(f"Error en consulta RAG: {e}")
            metrics_payload["latency_ms"]["total"] = round((perf_counter() - overall_start) * 1000, 3)
            return {
                "success": False,
                "error": str(e),
                "question": question,
                "metrics": metrics_payload if collect_metrics else None
            }
    
    def _create_rag_prompt(self, question: str, context: str) -> str:
        """Crear prompt para generación RAG con formato Markdown mejorado"""
        prompt = f"""Eres un asistente académico especializado en análisis de textos y documentos peruanos. Tu trabajo es encontrar y explicar información relevante basándote en los documentos proporcionados.

CONTEXTO DE DOCUMENTOS:
{context}

PREGUNTA DEL USUARIO: {question}

INSTRUCCIONES:
1. Analiza profundamente el contenido buscando conceptos e ideas relacionadas
2. Sé interpretativo: relaciona conceptualmente información aunque no use palabras exactas
3. Explora conexiones entre diferentes documentos y partes del texto
4. Cita específicamente las fuentes y documentos consultados
5. Combina información de múltiples fuentes cuando sea relevante

FORMATO DE RESPUESTA - USA MARKDOWN ESTRUCTURADO:

Explica la información encontrada de manera clara y detallada.

**Conceptos clave:** Usa negrita para términos importantes

*Énfasis específico:* Usa cursiva para ideas relevantes  

`Fuentes`: Usa código para nombres de documentos

Cuando enumeres múltiples puntos, usa listas numeradas con espacio apropiado:

1. **Primera idea importante:** Explicación detallada de la primera idea encontrada en los documentos.

2. **Segunda idea relevante:** Más información específica sobre el segundo punto identificado.

3. **Conexiones encontradas:** Relaciones entre conceptos y su significado en el contexto académico.

> Si hay citas textuales importantes, ponlas en formato de cita

**Fuentes consultadas:**
- `[nombre del archivo]`: Información específica encontrada
- `[nombre del archivo]`: Datos relevantes identificados

---

Responde de manera académica, bien estructurada y con espaciado apropiado para facilitar la lectura:"""
        
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
    
    def _enhance_citation_query(self, question: str) -> Tuple[bool, str]:
        """
        Detectar y mejorar consultas sobre citas bibliográficas específicas
        
        Returns:
            Tuple[bool, str]: (is_citation_query, enhanced_query)
        """
        import re
        
        # Patrones para detectar consultas sobre citas
        citation_patterns = [
            r'([A-Z][a-záéíóúñü]+)\s*\(\s*(\d{4})\s*\)',  # Arias(2020)
            r'([A-Z][a-záéíóúñü]+)\s+(\d{4})',           # Arias 2020
            r'([A-Z][a-záéíóúñü]+)\s+et\s+al\.\s*\(\s*(\d{4})\s*\)'  # Arias et al.(2020)
        ]
        
        enhanced_query = question
        is_citation_query = False
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, question, re.IGNORECASE)
            if matches:
                is_citation_query = True
                for match in matches:
                    if len(match) == 2:  # (autor, año)
                        author, year = match
                        # Añadir contexto para mejorar la búsqueda
                        enhanced_query += f" {author} {year} según menciona dice refiere cita bibliográfica investigación estudio análisis variables definición teoría"
                
        return is_citation_query, enhanced_query
    
    def _hybrid_search(self, original_query: str, enhanced_query: str, query_embedding, top_k: int) -> List[Dict[str, Any]]:
        """
        BÚSQUEDA HÍBRIDA MEJORADA
        Combina múltiples estrategias con pesos optimizados para máxima precisión
        """
        all_results = []
        seen_ids = set()
        
        logger.info(f"🔍 Iniciando búsqueda híbrida optimizada para: '{original_query}'")
        
        # Obtener configuración de pesos
        config = self.config.get("retrieval", {})
        semantic_weight = config.get("semantic_weight", 0.6)
        lexical_weight = config.get("lexical_weight", 0.4)
        max_results = config.get("top_k", 15)
        
        # 1. BÚSQUEDA SEMÁNTICA MEJORADA
        try:
            semantic_docs = self.chroma_manager.search_similar(
                query_embedding, 
                n_results=max_results,
                similarity_threshold=config.get("similarity_threshold", 0.005)
            )
            for i, doc in enumerate(semantic_docs):
                # Usar doc_id del metadata como ID único
                doc_id = doc.get('metadata', {}).get('doc_id', f"semantic_{len(all_results)}")
                if doc_id not in seen_ids:
                    # Aplicar peso semántico y boost por posición
                    position_boost = 1.0 - (i * 0.05)  # Reduce 5% por posición
                    weighted_score = doc.get('similarity_score', 0) * semantic_weight * position_boost
                    
                    doc['id'] = doc_id
                    doc['search_type'] = 'semantic'
                    doc['weighted_score'] = weighted_score
                    doc['original_score'] = doc.get('similarity_score', 0)
                    all_results.append(doc)
                    seen_ids.add(doc_id)
            logger.info(f"📊 Búsqueda semántica: {len(semantic_docs)} documentos (peso: {semantic_weight})")
        except Exception as e:
            logger.warning(f"Error en búsqueda semántica: {e}")
        
        # 2. BÚSQUEDA ADICIONAL (DESHABILITADA TEMPORALMENTE)
        # La búsqueda por texto tiene conflicto de dimensiones
        try:
            pass  # Placeholder - búsqueda lexical deshabilitada temporalmente
        except Exception as e:
            logger.warning(f"Error en búsqueda lexical: {e}")
        
        # 3. BÚSQUEDA POR METADATOS (nombres de archivos y fuentes)
        try:
            metadata_docs = self._enhanced_metadata_search(original_query, max_results // 2)
            for doc in metadata_docs:
                if doc['id'] not in seen_ids:
                    # Metadata tiene peso fijo alto para coincidencias exactas
                    doc['search_type'] = 'metadata'
                    doc['weighted_score'] = doc.get('similarity_score', 1.0)  # Score alto para metadata
                    doc['original_score'] = doc.get('similarity_score', 1.0)
                    all_results.append(doc)
                    seen_ids.add(doc['id'])
            logger.info(f"📊 Búsqueda por metadatos: {len(metadata_docs)} documentos")
        except Exception as e:
            logger.warning(f"Error en búsqueda por metadatos: {e}")
        
        # 4. BÚSQUEDA DE EXPANSIÓN (si pocos resultados)
        if len(all_results) < top_k:
            logger.info("[expand] Expandiendo búsqueda con términos relacionados...")
            try:
                expanded_docs = self._expansion_search(original_query, top_k)
                for doc in expanded_docs:
                    if doc['id'] not in seen_ids:
                        doc['search_type'] = 'expansion'
                        doc['weighted_score'] = doc.get('similarity_score', 0) * 0.3  # Peso bajo
                        doc['original_score'] = doc.get('similarity_score', 0)
                        all_results.append(doc)
                        seen_ids.add(doc['id'])
                logger.info(f"📊 Búsqueda expandida: {len(expanded_docs)} documentos adicionales")
            except Exception as e:
                logger.warning(f"Error en búsqueda expandida: {e}")
        
        # 5. ORDENAR POR WEIGHTED SCORE
        all_results.sort(key=lambda x: x.get('weighted_score', 0), reverse=True)
        
        # 6. DIVERSIFICACIÓN (evitar documentos muy similares, pero respetar max_per_source)
        diverse_results = self._diversify_results(
            all_results,
            config.get("diversity_threshold", 0.4),
            config.get("max_per_source")
        )
        
        logger.info(f"✅ Búsqueda híbrida completada: {len(diverse_results)} documentos únicos (de {len(all_results)} totales)")
        
        return diverse_results[:top_k]
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extraer palabras clave de la consulta"""
        import re
        
        # Limpiar y extraer palabras
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Filtrar stopwords comunes
        stopwords = {'el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 
                    'da', 'su', 'por', 'son', 'con', 'para', 'como', 'las', 'del', 'los', 'una', 
                    'está', 'qué', 'dice', 'sobre', 'quién', 'cómo', 'cuál', 'dónde'}
        
        keywords = [word for word in words if len(word) > 2 and word not in stopwords]
        
        return keywords
    
    def _search_by_filename(self, keywords: List[str], top_k: int) -> List[Dict[str, Any]]:
        """Buscar por coincidencias en nombres de archivos"""
        results = []
        
        try:
            collection = self.chroma_manager.collection
            all_data = collection.get()
            
            ids = all_data.get('ids', [])
            documents = all_data.get('documents', [])
            metadatas = all_data.get('metadatas', [])
            
            for i, metadata in enumerate(metadatas):
                if i >= len(ids) or i >= len(documents):
                    continue
                    
                source = metadata.get('source', '').lower()
                
                # Calcular score basado en coincidencias de palabras clave
                score = 0
                for keyword in keywords:
                    if keyword in source:
                        score += 1
                
                if score > 0:
                    results.append({
                        'id': ids[i],
                        'document': documents[i],
                        'metadata': metadata,
                        'similarity_score': score / len(keywords),  # Normalizar score
                        'rank': len(results) + 1
                    })
            
            # Ordenar por score descendente
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error en búsqueda por filename: {e}")
        
        return results[:top_k]
    
    def _lexical_search(self, keywords: List[str], top_k: int) -> List[Dict[str, Any]]:
        """Búsqueda lexical en el contenido de los documentos"""
        results = []
        
        try:
            collection = self.chroma_manager.collection
            all_data = collection.get()
            
            ids = all_data.get('ids', [])
            documents = all_data.get('documents', [])
            metadatas = all_data.get('metadatas', [])
            
            for i, document in enumerate(documents):
                if i >= len(ids) or i >= len(metadatas):
                    continue
                    
                content = document.lower()
                
                # Calcular score basado en frecuencia de palabras clave
                score = 0
                for keyword in keywords:
                    score += content.count(keyword)
                
                if score > 0:
                    results.append({
                        'id': ids[i],
                        'document': document,
                        'metadata': metadatas[i],
                        'similarity_score': min(score / 10, 1.0),  # Normalizar y limitar a 1.0
                        'rank': len(results) + 1
                    })
            
            # Ordenar por score descendente
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error en búsqueda lexical: {e}")
        
        return results[:top_k]
    
    def _smart_lexical_search(self, keywords: List[str], original_query: str, top_k: int) -> List[Dict[str, Any]]:
        """Búsqueda lexical inteligente con coincidencias parciales y fuzzy matching"""
        results = []
        
        try:
            collection = self.chroma_manager.collection
            all_data = collection.get(include=['documents', 'metadatas'])
            
            documents = all_data.get('documents', [])
            metadatas = all_data.get('metadatas', [])
            ids = all_data.get('ids', [])
            
            # Expandir keywords con variaciones
            expanded_keywords = set(keywords)
            for kw in keywords:
                # Agregar plurales y singulares básicos
                if kw.endswith('s'):
                    expanded_keywords.add(kw[:-1])
                else:
                    expanded_keywords.add(kw + 's')
                    
                # Agregar variaciones de capitalización
                expanded_keywords.add(kw.upper())
                expanded_keywords.add(kw.capitalize())
            
            for i, document in enumerate(documents):
                if i >= len(ids) or i >= len(metadatas):
                    continue
                
                doc_lower = document.lower()
                score = 0
                matches = 0
                
                # Calcular score basado en coincidencias
                for keyword in expanded_keywords:
                    kw_lower = keyword.lower()
                    if kw_lower in doc_lower:
                        # Boost para coincidencias exactas
                        count = doc_lower.count(kw_lower)
                        score += count * (0.2 if keyword in keywords else 0.1)
                        matches += count
                
                # Boost adicional si el documento contiene la frase completa
                if original_query.lower() in doc_lower:
                    score += 0.5
                    matches += 1
                
                if score > 0:
                    results.append({
                        'id': ids[i],
                        'content': document,
                        'metadata': metadatas[i],
                        'similarity_score': min(score, 1.0),  # Normalizar a máximo 1.0
                        'match_count': matches
                    })
            
            # Ordenar por score y luego por número de matches
            results.sort(key=lambda x: (x['similarity_score'], x['match_count']), reverse=True)
            
        except Exception as e:
            logger.error(f"Error en búsqueda lexical inteligente: {e}")
        
        return results[:top_k]
    
    def _enhanced_metadata_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Búsqueda mejorada en metadatos y nombres de archivos"""
        results = []
        
        try:
            collection = self.chroma_manager.collection
            all_data = collection.get(include=['documents', 'metadatas'])
            
            documents = all_data.get('documents', [])
            metadatas = all_data.get('metadatas', [])
            ids = all_data.get('ids', [])

            query_words = set(re.findall(r'\b\w+\b', query.lower()))
            stopwords = {
                'el', 'la', 'los', 'las', 'de', 'del', 'y', 'en', 'un', 'una', 'que', 'se', 'con', 'por',
                'para', 'como', 'al', 'lo', 'su', 'sus', 'es', 'son', 'o', 'u', 'a', 'e', 'i', 'sobre',
                'entre', 'sin', 'más', 'menos', 'donde', 'cuando', 'qué', 'cual', 'cuál', 'cuales',
                'cuáles', 'quién', 'quienes', 'quiénes', 'de', 'la', 'el', 'las', 'los'
            }
            filtered_query_words = {w for w in query_words if len(w) > 2 and w not in stopwords}
            if not filtered_query_words:
                filtered_query_words = query_words
            
            for i, metadata in enumerate(metadatas):
                if i >= len(ids):
                    continue
                
                score = 0
                source_words: set[str] = set()
                
                # Buscar en source/filename
                source = metadata.get('source', '').lower()
                if source:
                    source_words = {
                        w for w in re.findall(r'\b\w+\b', source)
                        if len(w) > 2 and w not in stopwords
                    }
                    common_words = filtered_query_words.intersection(source_words)
                    if common_words:
                        score += len(common_words) / max(len(filtered_query_words), 1) * 0.9
                
                # Buscar en document field
                document_field = metadata.get('document', '').lower()
                if document_field:
                    doc_words = {
                        w for w in re.findall(r'\b\w+\b', document_field)
                        if len(w) > 2 and w not in stopwords
                    }
                    common_words = filtered_query_words.intersection(doc_words)
                    if common_words:
                        score += len(common_words) / max(len(filtered_query_words), 1) * 0.7
                
                # Búsqueda exacta en títulos/fuentes
                if query.lower() in source or query.lower() in document_field:
                    score += 0.9
                else:
                    # Boost si todos los términos clave aparecen dispersos
                    if filtered_query_words and filtered_query_words.issubset(source_words or set()):
                        score += 0.5
                
                if score > 0:
                    results.append({
                        'id': ids[i],
                        'content': documents[i] if i < len(documents) else '',
                        'metadata': metadata,
                        'similarity_score': min(score, 1.0)
                    })
            
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error en búsqueda de metadatos: {e}")
        
        return results[:top_k]
    
    def _expansion_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Búsqueda con expansión de términos y conceptos relacionados"""
        results = []
        
        # Diccionario de expansión de términos académicos
        expansion_dict = {
            'derecho': ['derechos', 'legal', 'jurídico', 'justicia', 'normativo'],
            'mugre': ['suciedad', 'contaminación', 'higiene', 'limpieza', 'sanitario'],
            'satán': ['diablo', 'demonio', 'mal', 'infernal', 'diabólico'],
            'crucificado': ['crucifixión', 'cruz', 'crucificar', 'martirio'],
            'democracia': ['democrático', 'democratización', 'participación', 'electoral'],
            'política': ['político', 'gobierno', 'estado', 'poder', 'gestión'],
            'regionalización': ['regional', 'descentralización', 'territorio', 'local'],
            'racismo': ['racial', 'discriminación', 'étnico', 'prejuicio'],
            'violencia': ['violento', 'agresión', 'conflicto', 'guerra']
        }
        
        try:
            # Extraer términos clave de la consulta
            query_terms = re.findall(r'\b\w+\b', query.lower())
            expanded_terms = set(query_terms)
            
            # Expandir con términos relacionados
            for term in query_terms:
                if term in expansion_dict:
                    expanded_terms.update(expansion_dict[term])
            
            # Buscar con términos expandidos
            collection = self.chroma_manager.collection
            all_data = collection.get(include=['documents', 'metadatas'])
            
            documents = all_data.get('documents', [])
            metadatas = all_data.get('metadatas', [])
            ids = all_data.get('ids', [])
            
            for i, document in enumerate(documents):
                if i >= len(ids) or i >= len(metadatas):
                    continue
                
                doc_lower = document.lower()
                score = 0
                
                # Calcular relevancia basada en términos expandidos
                for term in expanded_terms:
                    if term in doc_lower:
                        # Términos originales tienen más peso
                        weight = 0.3 if term in query_terms else 0.1
                        count = doc_lower.count(term)
                        score += count * weight
                
                if score > 0:
                    results.append({
                        'id': ids[i],
                        'content': document,
                        'metadata': metadatas[i],
                        'similarity_score': min(score / len(expanded_terms), 1.0)
                    })
            
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error en búsqueda expandida: {e}")
        
        return results[:top_k]
    
    def _diversify_results(
        self,
        results: List[Dict[str, Any]],
        diversity_threshold: float,
        max_per_source: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Diversificar resultados permitiendo múltiples chunks del mismo documento."""
        if not results:
            return results

        diverse_results = []
        source_counts: Dict[str, int] = {}

        for result in results:
            metadata = result.get('metadata') or {}
            source_name = metadata.get('source')

            if source_name:
                current_count = source_counts.get(source_name, 0)
                if max_per_source is not None and current_count >= max_per_source:
                    continue

            if not diverse_results:
                diverse_results.append(result)
                if source_name:
                    source_counts[source_name] = source_counts.get(source_name, 0) + 1
                continue

            is_diverse = True
            result_content = result.get('content', '').lower()
            
            for existing in diverse_results:
                existing_content = existing.get('content', '').lower()
                
                # Calcular similitud simple basada en palabras comunes
                result_words = set(re.findall(r'\b\w+\b', result_content))
                existing_words = set(re.findall(r'\b\w+\b', existing_content))
                
                if result_words and existing_words:
                    similarity = len(result_words.intersection(existing_words)) / len(result_words.union(existing_words))
                    if similarity > diversity_threshold:
                        is_diverse = False
                        break
            
            if is_diverse:
                diverse_results.append(result)
                if source_name:
                    source_counts[source_name] = source_counts.get(source_name, 0) + 1
        
        return diverse_results
    
    def _desperate_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Búsqueda desesperada - devuelve cualquier contenido relacionado"""
        results = []
        
        try:
            collection = self.chroma_manager.collection
            all_data = collection.get()
            
            ids = all_data.get('ids', [])
            documents = all_data.get('documents', [])
            metadatas = all_data.get('metadatas', [])
            
            query_words = set(re.findall(r'\b\w+\b', query.lower()))
            
            for i, document in enumerate(documents):
                if i >= len(ids) or i >= len(metadatas):
                    continue
                    
                doc_words = set(re.findall(r'\b\w+\b', document.lower()))
                
                # Calcular intersección de palabras
                common_words = query_words.intersection(doc_words)
                
                if common_words:
                    score = len(common_words) / len(query_words)
                    results.append({
                        'id': ids[i],
                        'document': document,
                        'metadata': metadatas[i],
                        'similarity_score': score,
                        'rank': len(results) + 1
                    })
            
            # Ordenar por score descendente
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error en búsqueda desesperada: {e}")
        
        return results[:top_k]
    
    def _rank_hybrid_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Reordenar resultados híbridos por relevancia total"""
        
        # Asignar pesos por tipo de búsqueda
        type_weights = {
            'semantic': 1.0,
            'metadata': 0.8,
            'lexical': 0.6,
            'desperate': 0.3
        }
        
        for result in results:
            search_type = result.get('search_type', 'desperate')
            original_score = result.get('similarity_score', 0)
            weight = type_weights.get(search_type, 0.3)
            
            # Calcular score final ponderado
            result['final_score'] = original_score * weight
        
        # Ordenar por score final
        results.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        return results