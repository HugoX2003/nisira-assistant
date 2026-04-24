"""
ChromaDB Manager
===============

Gestor de base de datos vectorial ChromaDB para almacenamiento
y búsqueda eficiente de embeddings de documentos.
"""

import os
import shutil
import logging
from typing import List, Dict, Any, Optional, Tuple
import json
from datetime import datetime
import uuid

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from ..config import CHROMA_CONFIG

logger = logging.getLogger(__name__)

class ChromaManager:
    """
    Gestor de ChromaDB para operaciones vectoriales
    """
    
    def __init__(self):
        self.config = CHROMA_CONFIG
        self.client = None
        self.collection = None
        self.collection_name = self.config['collection_name']
        self.persist_directory = self.config['persist_directory']
        
        # Crear directorio de persistencia
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Inicializar cliente
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializar cliente de ChromaDB"""
        if not CHROMADB_AVAILABLE:
            logger.error("[ERROR] ChromaDB no está disponible")
            return False
        
        try:
            # Usar PersistentClient con la nueva API
            self.client = chromadb.PersistentClient(
                path=self.persist_directory
            )
            
            # Obtener o crear colección
            try:
                self.collection = self.client.get_collection(
                    name=self.collection_name
                )
                logger.info(f"[OK] Colección existente cargada: {self.collection_name}")
            except Exception:
                # Crear nueva colección
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Documentos RAG del sistema Nisira"}
                )
                logger.info(f"[OK] Nueva colección creada: {self.collection_name}")
            
            return True
            
        except Exception as e:
            err_text = str(e)
            logger.error(f"[ERROR] Error inicializando ChromaDB: {err_text}")
            # Si el archivo es un puntero LFS o está corrupto, limpiar y reintentar una vez
            if "file is not a database" in err_text.lower():
                try:
                    logger.warning("[CLEAN] Limpiando directorio de persistencia de ChromaDB y reintentando...")
                    for entry in os.listdir(self.persist_directory):
                        path = os.path.join(self.persist_directory, entry)
                        if os.path.isdir(path):
                            shutil.rmtree(path, ignore_errors=True)
                        else:
                            try:
                                os.remove(path)
                            except FileNotFoundError:
                                pass
                    # Reintentar
                    self.client = chromadb.PersistentClient(path=self.persist_directory)
                    self.collection = self.client.create_collection(
                        name=self.collection_name,
                        metadata={"description": "Documentos RAG del sistema Nisira"}
                    )
                    logger.info("[OK] ChromaDB reinicializado con colección vacía tras limpiar persistencia")
                    return True
                except Exception as e2:
                    logger.error(f"[ERROR] Reintento fallido de ChromaDB tras limpieza: {e2}")
            return False
    
    def is_ready(self) -> bool:
        """Verificar si ChromaDB está listo"""
        return (
            CHROMADB_AVAILABLE and 
            self.client is not None and 
            self.collection is not None
        )
    
    def add_documents(self, documents: List[Dict[str, Any]], 
                     embeddings: List[List[float]], 
                     batch_size: int = 100) -> bool:
        """
        Agregar documentos con embeddings a la colección
        
        Args:
            documents: Lista de documentos con metadatos
            embeddings: Lista de embeddings correspondientes
            batch_size: Tamaño del lote para inserción
        
        Returns:
            True si fue exitoso
        """
        logger.info(f"[INFO] ChromaDB add_documents llamado con {len(documents)} docs, {len(embeddings)} embeddings")
        logger.info(f"[INFO] Client status: {self.client is not None}, Collection: {self.collection_name}")
        
        # Verificar si la colección existe, si no, recrearla
        try:
            if self.client is not None:
                # Intentar obtener la colección
                try:
                    self.collection = self.client.get_collection(name=self.collection_name)
                    logger.info(f"[INFO] Colección '{self.collection_name}' encontrada")
                except Exception:
                    # Si no existe, crearla
                    logger.warning(f"[WARN]  Colección '{self.collection_name}' no existe, creándola...")
                    self.collection = self.client.create_collection(
                        name=self.collection_name,
                        metadata={"description": "Documentos RAG del sistema Nisira"}
                    )
                    logger.info(f"[OK] Colección '{self.collection_name}' creada")
        except Exception as e:
            logger.error(f"[ERROR] Error verificando/creando colección: {e}")
        
        if not self.is_ready():
            logger.error("[ERROR] ChromaDB no está listo")
            logger.error(f"   - CHROMADB_AVAILABLE: {CHROMADB_AVAILABLE}")
            logger.error(f"   - self.client: {self.client}")
            logger.error(f"   - self.collection: {self.collection}")
            return False
        
        if len(documents) != len(embeddings):
            logger.error("[ERROR] Número de documentos y embeddings no coinciden")
            return False
        
        if not documents:
            logger.warning("[WARN]  No hay documentos para agregar")
            return True
        
        try:
            total_docs = len(documents)
            successful = 0
            
            logger.info(f"[NOTE] Agregando {total_docs} documentos a ChromaDB")
            
            # Procesar en lotes
            for i in range(0, total_docs, batch_size):
                batch_docs = documents[i:i + batch_size]
                batch_embeddings = embeddings[i:i + batch_size]
                
                # Preparar datos para ChromaDB
                ids = []
                texts = []
                metadatas = []
                batch_embs = []
                
                for doc, embedding in zip(batch_docs, batch_embeddings):
                    if embedding is None:
                        logger.warning(f"[WARN]  Documento sin embedding saltado: {doc.get('metadata', {}).get('file_name', 'unknown')}")
                        continue
                    
                    # Generar ID único
                    doc_id = str(uuid.uuid4())
                    ids.append(doc_id)
                    
                    # Texto del documento
                    texts.append(doc['text'])
                    
                    # Metadatos (ChromaDB requiere que sean serializables)
                    metadata = doc.get('metadata', {})
                    
                    # Agregar timestamp
                    metadata['added_at'] = datetime.now().isoformat()
                    metadata['doc_id'] = doc_id
                    
                    # Asegurar que todos los valores sean serializables
                    clean_metadata = self._clean_metadata(metadata)
                    metadatas.append(clean_metadata)
                    
                    batch_embs.append(embedding)
                
                if ids:  # Solo si hay documentos válidos en el lote
                    # Agregar a ChromaDB
                    self.collection.add(
                        ids=ids,
                        documents=texts,
                        metadatas=metadatas,
                        embeddings=batch_embs
                    )
                    
                    successful += len(ids)
                    logger.info(f"[STATS] Progreso: {successful}/{total_docs} documentos agregados")
            
            logger.info(f"[OK] {successful} documentos agregados exitosamente a ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error agregando documentos a ChromaDB: {e}")
            return False
    
    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpiar metadatos para que sean compatibles con ChromaDB
        
        Args:
            metadata: Metadatos originales
        
        Returns:
            Metadatos limpios
        """
        clean_metadata = {}
        
        for key, value in metadata.items():
            if value is None:
                continue
            
            # Convertir tipos no soportados
            if isinstance(value, (list, dict)):
                clean_metadata[key] = json.dumps(value)
            elif isinstance(value, (int, float, str, bool)):
                clean_metadata[key] = value
            else:
                clean_metadata[key] = str(value)
        
        return clean_metadata
    
    def search_similar(self, query_embedding: List[float], 
                      n_results: int = 5,
                      filter_metadata: Optional[Dict[str, Any]] = None,
                      similarity_threshold: float = 0.15) -> List[Dict[str, Any]]:
        """
        Buscar documentos similares usando embedding de consulta
        
        Args:
            query_embedding: Embedding de la consulta
            n_results: Número de resultados a devolver
            filter_metadata: Filtros de metadatos (opcional)
            similarity_threshold: Umbral mínimo de similitud (0.0 a 1.0)
        
        Returns:
            Lista de documentos similares con scores
        """
        if not self.is_ready():
            logger.error("[ERROR] ChromaDB no está listo")
            return []
        
        try:
            # Realizar búsqueda con más resultados para filtrar después
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results * 2,  # Buscar más para filtrar por threshold
                where=filter_metadata,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Formatear resultados
            formatted_results = []
            
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    # Convertir distancia a score de similitud (1 - distancia normalizada)
                    similarity_score = max(0, 1 - distance)
                    
                    # Filtrar por threshold
                    if similarity_score < similarity_threshold:
                        continue
                    
                    result = {
                        'rank': len(formatted_results) + 1,
                        'document': doc,
                        'metadata': metadata,
                        'similarity_score': similarity_score,
                        'distance': distance
                    }
                    
                    formatted_results.append(result)
                    
                    # Limitar a n_results después de filtrar
                    if len(formatted_results) >= n_results:
                        break
            
            logger.info(f"[SEARCH] Búsqueda completada: {len(formatted_results)} resultados (threshold: {similarity_threshold})")
            return formatted_results
            
        except Exception as e:
            logger.error(f"[ERROR] Error en búsqueda: {e}")
            return []
    
    def search_by_text(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Buscar documentos por texto (sin embedding previo)
        Nota: Requiere que el sistema de embeddings esté disponible
        
        Args:
            query_text: Texto de consulta
            n_results: Número de resultados
        
        Returns:
            Lista de documentos similares
        """
        if not self.is_ready():
            return []
        
        try:
            # Buscar usando texto directo (ChromaDB hará el embedding internamente si está configurado)
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Formatear resultados igual que search_similar
            formatted_results = []
            
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    similarity_score = max(0, 1 - distance)
                    
                    result = {
                        'rank': i + 1,
                        'document': doc,
                        'metadata': metadata,
                        'similarity_score': similarity_score,
                        'distance': distance
                    }
                    
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"[ERROR] Error en búsqueda por texto: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de la colección
        
        Returns:
            Estadísticas detalladas
        """
        if not self.is_ready():
            return {"ready": False}
        
        try:
            count = self.collection.count()
            
            # Obtener algunos documentos de muestra para análisis
            sample_results = self.collection.peek(limit=10)
            
            stats = {
                "ready": True,
                "collection_name": self.collection_name,
                "total_documents": count,
                "persist_directory": self.persist_directory
            }
            
            # Analizar metadatos de muestra
            if sample_results['metadatas']:
                sample_metadata = sample_results['metadatas'][0] if sample_results['metadatas'] else {}
                
                # Extraer tipos de archivos
                file_types = set()
                for metadata in sample_results['metadatas']:
                    if 'file_extension' in metadata:
                        file_types.add(metadata['file_extension'])
                    elif 'format' in metadata:
                        file_types.add(metadata['format'])
                
                stats['file_types'] = list(file_types)
                stats['sample_metadata_keys'] = list(sample_metadata.keys()) if sample_metadata else []
            
            return stats
            
        except Exception as e:
            logger.error(f"[ERROR] Error obteniendo estadísticas: {e}")
            return {"ready": False, "error": str(e)}
    
    def list_collections(self) -> List[str]:
        """
        Listar todas las colecciones disponibles
        
        Returns:
            Lista de nombres de colecciones
        """
        if not self.client:
            return []
        
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"[ERROR] Error listando colecciones: {e}")
            return []
    
    def list_all_documents(self) -> Dict[str, Any]:
        """
        Listar todos los documentos únicos almacenados en la colección.
        
        Returns:
            Diccionario con información de todos los documentos únicos
        """
        if not self.is_ready():
            return {"success": False, "error": "ChromaDB no está listo"}
        
        try:
            # Obtener todos los datos de la colección
            all_data = self.collection.get(include=['metadatas'])
            
            metadatas = all_data.get('metadatas', [])
            
            # Extraer documentos únicos por nombre de archivo
            unique_documents = {}
            
            for metadata in metadatas:
                source = metadata.get('source', metadata.get('document', metadata.get('file_name', 'Desconocido')))
                
                if source not in unique_documents:
                    unique_documents[source] = {
                        'name': source,
                        'chunks': 1,
                        'pages': set(),
                        'file_extension': metadata.get('file_extension', ''),
                        'processed_date': metadata.get('processed_at', metadata.get('created_at', ''))
                    }
                else:
                    unique_documents[source]['chunks'] += 1
                
                # Agregar página si existe
                if 'page' in metadata:
                    unique_documents[source]['pages'].add(metadata['page'])
            
            # Convertir sets a listas para serialización JSON
            documents_list = []
            for doc_name, doc_info in unique_documents.items():
                doc_info['pages'] = sorted(list(doc_info['pages'])) if doc_info['pages'] else []
                doc_info['total_pages'] = len(doc_info['pages']) if doc_info['pages'] else 'N/A'
                documents_list.append(doc_info)
            
            # Ordenar por nombre
            documents_list.sort(key=lambda x: x['name'].lower())
            
            return {
                "success": True,
                "total_documents": len(documents_list),
                "total_chunks": len(metadatas),
                "documents": documents_list
            }
            
        except Exception as e:
            logger.error(f"[ERROR] Error listando documentos: {e}")
            return {"success": False, "error": str(e)}
    
    def get_collection_count(self, collection_name: str = None) -> int:
        """
        Obtener número de documentos en una colección
        
        Args:
            collection_name: Nombre de la colección (usa la actual si no se especifica)
        
        Returns:
            Número de documentos
        """
        if not self.client:
            return 0
        
        try:
            if collection_name:
                collection = self.client.get_collection(name=collection_name)
                return collection.count()
            elif self.collection:
                return self.collection.count()
            return 0
        except Exception as e:
            logger.error(f"[ERROR] Error obteniendo conteo: {e}")
            return 0
    
    def delete_documents(self, filter_metadata: Dict[str, Any]) -> bool:
        """
        Eliminar documentos que coincidan con filtros
        
        Args:
            filter_metadata: Filtros para eliminar documentos
        
        Returns:
            True si fue exitoso
        """
        if not self.is_ready():
            return False
        
        try:
            # Buscar documentos que coincidan
            results = self.collection.query(
                query_texts=[""],  # Query vacía
                where=filter_metadata,
                include=['ids']
            )
            
            if results['ids'] and results['ids'][0]:
                ids_to_delete = results['ids'][0]
                
                # Eliminar documentos
                self.collection.delete(ids=ids_to_delete)
                
                logger.info(f"[DEL]  {len(ids_to_delete)} documentos eliminados")
                return True
            else:
                logger.info("[INFO]  No se encontraron documentos para eliminar")
                return True
                
        except Exception as e:
            logger.error(f"[ERROR] Error eliminando documentos: {e}")
            return False
    
    def reset_collection(self) -> bool:
        """
        Resetear (vaciar) la colección completamente
        
        Returns:
            True si fue exitoso
        """
        if not self.client:
            return False
        
        try:
            # Eliminar colección existente
            self.client.delete_collection(name=self.collection_name)
            
            # Crear nueva colección
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Documentos RAG del sistema Nisira"}
            )
            
            logger.info(f"[SYNC] Colección {self.collection_name} reseteada")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error reseteando colección: {e}")
            return False
    
    def backup_collection(self, backup_path: str) -> bool:
        """
        Crear respaldo de la colección
        
        Args:
            backup_path: Ruta para el respaldo
        
        Returns:
            True si fue exitoso
        """
        if not self.is_ready():
            return False
        
        try:
            # Obtener todos los documentos
            all_docs = self.collection.get(include=['documents', 'metadatas', 'embeddings'])
            
            backup_data = {
                'collection_name': self.collection_name,
                'timestamp': datetime.now().isoformat(),
                'total_documents': len(all_docs['documents']),
                'documents': all_docs['documents'],
                'metadatas': all_docs['metadatas'],
                'embeddings': all_docs['embeddings'],
                'ids': all_docs['ids']
            }
            
            # Guardar respaldo
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"[SAVE] Respaldo creado: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error creando respaldo: {e}")
            return False
    
    def restore_collection(self, backup_path: str) -> bool:
        """
        Restaurar colección desde respaldo
        
        Args:
            backup_path: Ruta del respaldo
        
        Returns:
            True si fue exitoso
        """
        if not os.path.exists(backup_path):
            logger.error(f"[ERROR] Archivo de respaldo no encontrado: {backup_path}")
            return False
        
        try:
            # Cargar respaldo
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Resetear colección actual
            self.reset_collection()
            
            # Restaurar datos
            if backup_data['documents']:
                self.collection.add(
                    ids=backup_data['ids'],
                    documents=backup_data['documents'],
                    metadatas=backup_data['metadatas'],
                    embeddings=backup_data['embeddings']
                )
            
            logger.info(f"[INFO] Colección restaurada desde {backup_path}")
            logger.info(f"[STATS] {backup_data['total_documents']} documentos restaurados")
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error restaurando respaldo: {e}")
            return False