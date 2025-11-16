"""
PostgreSQL Vector Store
=======================

Almacenamiento de embeddings directamente en PostgreSQL
usando la extensión pgvector para búsqueda eficiente.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import uuid
import numpy as np

try:
    import psycopg2
    from psycopg2.extras import Json, execute_values
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

logger = logging.getLogger(__name__)


class PostgresVectorStore:
    """
    Gestor de embeddings usando PostgreSQL + pgvector
    """
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        self.conn = None
        self.embedding_dim = 768  # Dimensión de embeddings de Google
        
        if not PSYCOPG2_AVAILABLE:
            logger.error("❌ psycopg2 no disponible")
            return
        
        self._initialize_connection()
        self._ensure_table_exists()
    
    def _initialize_connection(self):
        """Conectar a PostgreSQL"""
        try:
            self.conn = psycopg2.connect(self.database_url)
            self.conn.autocommit = False
            logger.info("✅ Conectado a PostgreSQL para embeddings")
        except Exception as e:
            logger.error(f"❌ Error conectando a PostgreSQL: {e}")
            self.conn = None
    
    def _ensure_table_exists(self):
        """Crear tabla de embeddings si no existe"""
        if not self.conn:
            return
        
        try:
            with self.conn.cursor() as cur:
                # Habilitar extensión pgvector (si está disponible)
                # Si no está, usamos JSONB para almacenar los vectores
                try:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    use_vector = True
                except Exception:
                    logger.warning("⚠️ pgvector no disponible, usando JSONB para vectores")
                    use_vector = False
                
                # Crear tabla
                if use_vector:
                    cur.execute(f"""
                        CREATE TABLE IF NOT EXISTS rag_embeddings (
                            id UUID PRIMARY KEY,
                            chunk_text TEXT NOT NULL,
                            embedding_vector vector({self.embedding_dim}),
                            metadata JSONB,
                            created_at TIMESTAMP DEFAULT NOW(),
                            updated_at TIMESTAMP DEFAULT NOW()
                        );
                        
                        CREATE INDEX IF NOT EXISTS idx_embedding_vector 
                        ON rag_embeddings USING ivfflat (embedding_vector vector_cosine_ops)
                        WITH (lists = 100);
                    """)
                else:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS rag_embeddings (
                            id UUID PRIMARY KEY,
                            chunk_text TEXT NOT NULL,
                            embedding_vector JSONB,
                            metadata JSONB,
                            created_at TIMESTAMP DEFAULT NOW(),
                            updated_at TIMESTAMP DEFAULT NOW()
                        );
                        
                        CREATE INDEX IF NOT EXISTS idx_metadata 
                        ON rag_embeddings USING gin(metadata);
                    """)
                
                self.conn.commit()
                logger.info("✅ Tabla rag_embeddings lista")
                
        except Exception as e:
            logger.error(f"❌ Error creando tabla: {e}")
            if self.conn:
                self.conn.rollback()
    
    def is_ready(self) -> bool:
        """Verificar si el store está listo"""
        return PSYCOPG2_AVAILABLE and self.conn is not None
    
    def add_documents(self, documents: List[Dict[str, Any]], 
                     embeddings: List[List[float]]) -> bool:
        """
        Agregar documentos con embeddings a PostgreSQL
        
        Args:
            documents: Lista de documentos con metadatos
            embeddings: Lista de embeddings correspondientes
        
        Returns:
            True si fue exitoso
        """
        if not self.is_ready():
            logger.error("❌ PostgreSQL no está listo")
            return False
        
        if len(documents) != len(embeddings):
            logger.error("❌ Número de documentos y embeddings no coinciden")
            return False
        
        try:
            with self.conn.cursor() as cur:
                # Preparar datos para inserción batch
                values = []
                for doc, embedding in zip(documents, embeddings):
                    if embedding is None:
                        continue
                    
                    doc_id = str(uuid.uuid4())
                    chunk_text = doc['text']
                    metadata = doc.get('metadata', {})
                    metadata['doc_id'] = doc_id
                    metadata['added_at'] = datetime.now().isoformat()
                    
                    # Convertir embedding a formato JSON
                    embedding_json = json.dumps(embedding)
                    
                    values.append((
                        doc_id,
                        chunk_text,
                        embedding_json,
                        Json(metadata)
                    ))
                
                if not values:
                    logger.warning("⚠️ No hay documentos válidos para insertar")
                    return True
                
                # Inserción batch
                execute_values(
                    cur,
                    """
                    INSERT INTO rag_embeddings 
                    (id, chunk_text, embedding_vector, metadata)
                    VALUES %s
                    """,
                    values,
                    template="(%s, %s, %s::jsonb, %s)"
                )
                
                self.conn.commit()
                logger.info(f"✅ {len(values)} documentos insertados en PostgreSQL")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error insertando documentos: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def search_similar(self, query_embedding: List[float], 
                      n_results: int = 5,
                      similarity_threshold: float = 0.15) -> List[Dict[str, Any]]:
        """
        Buscar documentos similares usando embedding de consulta
        
        Args:
            query_embedding: Embedding de la consulta
            n_results: Número de resultados
            similarity_threshold: Umbral mínimo de similitud
        
        Returns:
            Lista de documentos similares con scores
        """
        if not self.is_ready():
            logger.error("❌ PostgreSQL no está listo")
            return []
        
        try:
            with self.conn.cursor() as cur:
                # Convertir query embedding a JSON
                query_vector = json.dumps(query_embedding)
                
                # Búsqueda por similitud coseno
                # Calculamos la similitud manualmente con JSONB
                cur.execute("""
                    WITH query_vec AS (
                        SELECT %s::jsonb as vec
                    )
                    SELECT 
                        id,
                        chunk_text,
                        embedding_vector,
                        metadata,
                        (
                            SELECT 1 - (
                                SUM((ev.value::float * qv.value::float)) / 
                                (
                                    SQRT(SUM(POW(ev.value::float, 2))) * 
                                    SQRT(SUM(POW(qv.value::float, 2)))
                                )
                            )
                            FROM jsonb_array_elements_text(embedding_vector) WITH ORDINALITY ev(value, idx)
                            JOIN jsonb_array_elements_text((SELECT vec FROM query_vec)) WITH ORDINALITY qv(value, idx2)
                                ON ev.idx = qv.idx2
                        ) as distance
                    FROM rag_embeddings
                    ORDER BY distance ASC
                    LIMIT %s * 2;
                """, (query_vector, n_results))
                
                results = []
                for row in cur.fetchall():
                    doc_id, chunk_text, embedding_json, metadata, distance = row
                    
                    # Convertir distancia a score de similitud
                    similarity_score = max(0, 1 - distance) if distance else 0
                    
                    # Filtrar por threshold
                    if similarity_score < similarity_threshold:
                        continue
                    
                    results.append({
                        'id': str(doc_id),
                        'document': chunk_text,
                        'content': chunk_text,
                        'metadata': metadata,
                        'similarity_score': similarity_score,
                        'distance': distance,
                        'rank': len(results) + 1
                    })
                    
                    if len(results) >= n_results:
                        break
                
                logger.info(f"🔍 Búsqueda completada: {len(results)} resultados")
                return results
                
        except Exception as e:
            logger.error(f"❌ Error en búsqueda: {e}")
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
            with self.conn.cursor() as cur:
                # Contar documentos
                cur.execute("SELECT COUNT(*) FROM rag_embeddings;")
                total_docs = cur.fetchone()[0]
                
                # Obtener tamaño de la tabla
                cur.execute("""
                    SELECT pg_size_pretty(pg_total_relation_size('rag_embeddings'));
                """)
                table_size = cur.fetchone()[0]
                
                return {
                    "ready": True,
                    "total_documents": total_docs,
                    "table_size": table_size,
                    "storage": "PostgreSQL",
                }
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {"ready": False, "error": str(e)}
    
    def reset_collection(self) -> bool:
        """
        Eliminar todos los embeddings (CUIDADO)
        
        Returns:
            True si fue exitoso
        """
        if not self.is_ready():
            return False
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE rag_embeddings;")
                self.conn.commit()
                
                logger.info("🔄 Tabla rag_embeddings vaciada")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error vaciando tabla: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def close(self):
        """Cerrar conexión"""
        if self.conn:
            self.conn.close()
            logger.info("✅ Conexión PostgreSQL cerrada")
