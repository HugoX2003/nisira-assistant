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
        self.use_vector_type = False  # Rastrear si pgvector está disponible
        
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
                use_vector = False
                try:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    self.conn.commit()
                    use_vector = True
                    self.use_vector_type = True
                    logger.info("✅ Extensión pgvector habilitada")
                except Exception as e:
                    logger.warning(f"⚠️ pgvector no disponible, usando JSONB para vectores: {e}")
                    self.conn.rollback()
                    use_vector = False
                    self.use_vector_type = False
                
                # Crear tabla
                if use_vector:
                    # Con pgvector
                    cur.execute(f"""
                        CREATE TABLE IF NOT EXISTS rag_embeddings (
                            id UUID PRIMARY KEY,
                            chunk_text TEXT NOT NULL,
                            embedding_vector vector({self.embedding_dim}),
                            metadata JSONB,
                            created_at TIMESTAMP DEFAULT NOW(),
                            updated_at TIMESTAMP DEFAULT NOW()
                        );
                    """)
                    self.conn.commit()
                    logger.info("✅ Tabla rag_embeddings creada con tipo vector")
                    
                    # Crear índice IVFFlat (solo si hay suficientes datos)
                    try:
                        # Verificar si ya existe el índice
                        cur.execute("""
                            SELECT COUNT(*) FROM pg_indexes 
                            WHERE tablename = 'rag_embeddings' 
                            AND indexname = 'idx_embedding_vector'
                        """)
                        if cur.fetchone()[0] == 0:
                            # Crear índice solo si hay más de 1000 filas (recomendación pgvector)
                            cur.execute("SELECT COUNT(*) FROM rag_embeddings")
                            row_count = cur.fetchone()[0]
                            
                            if row_count > 1000:
                                logger.info(f"📊 Creando índice IVFFlat para {row_count} embeddings...")
                                cur.execute(f"""
                                    CREATE INDEX idx_embedding_vector 
                                    ON rag_embeddings 
                                    USING ivfflat (embedding_vector vector_cosine_ops)
                                    WITH (lists = 100);
                                """)
                                self.conn.commit()
                                logger.info("✅ Índice IVFFlat creado")
                            else:
                                logger.info(f"ℹ️  Solo {row_count} embeddings, índice IVFFlat se creará después de 1000+")
                    except Exception as idx_error:
                        logger.warning(f"⚠️ No se pudo crear índice IVFFlat: {idx_error}")
                        self.conn.rollback()
                else:
                    # Sin pgvector, usar JSONB
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS rag_embeddings (
                            id UUID PRIMARY KEY,
                            chunk_text TEXT NOT NULL,
                            embedding_vector JSONB,
                            metadata JSONB,
                            created_at TIMESTAMP DEFAULT NOW(),
                            updated_at TIMESTAMP DEFAULT NOW()
                        );
                    """)
                    self.conn.commit()
                    logger.info("✅ Tabla rag_embeddings creada con tipo JSONB")
                    
                    # Índice para metadata
                    try:
                        cur.execute("""
                            CREATE INDEX IF NOT EXISTS idx_metadata 
                            ON rag_embeddings USING gin(metadata);
                        """)
                        self.conn.commit()
                        logger.info("✅ Índice GIN para metadata creado")
                    except Exception as idx_error:
                        logger.warning(f"⚠️ Error creando índice metadata: {idx_error}")
                        self.conn.rollback()
                
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
        logger.info(f"🔵 PostgreSQL add_documents llamado con {len(documents)} docs, {len(embeddings)} embeddings")
        logger.info(f"🔵 DB connection status: {self.conn is not None}")
        logger.info(f"🔵 DB URL configured: {bool(self.database_url)}")
        
        if not self.is_ready():
            logger.error("❌ PostgreSQL no está listo")
            logger.error(f"   - PSYCOPG2_AVAILABLE: {PSYCOPG2_AVAILABLE}")
            logger.error(f"   - self.conn: {self.conn}")
            return False
        
        if len(documents) != len(embeddings):
            logger.error("❌ Número de documentos y embeddings no coinciden")
            return False
        
        try:
            with self.conn.cursor() as cur:
                # Preparar datos para inserción batch
                now = datetime.now()
                values = []
                for doc, embedding in zip(documents, embeddings):
                    if embedding is None:
                        continue
                    
                    doc_id = str(uuid.uuid4())
                    chunk_text = doc['text']
                    metadata = doc.get('metadata', {})
                    metadata['doc_id'] = doc_id
                    metadata['added_at'] = now.isoformat()
                    
                    if self.use_vector_type:
                        # Usar formato de array para pgvector: [0.1, 0.2, ...]
                        embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
                    else:
                        # Convertir embedding a formato JSON para JSONB
                        embedding_str = json.dumps(embedding)
                    
                    values.append((
                        doc_id,
                        chunk_text,
                        embedding_str,
                        Json(metadata),
                        now,
                        now
                    ))
                
                if not values:
                    logger.warning("⚠️ No hay documentos válidos para insertar")
                    return True
                
                logger.info(f"🔵 Preparados {len(values)} valores para insertar en PostgreSQL")
                logger.info(f"🔵 Usando tipo: {'vector' if self.use_vector_type else 'JSONB'}")
                logger.info(f"🔵 Muestra del primer valor: id={values[0][0][:8]}..., texto_len={len(values[0][1])}")
                
                # Inserción batch con el tipo correcto
                logger.info("🔵 Ejecutando INSERT batch en PostgreSQL...")
                if self.use_vector_type:
                    # Con pgvector
                    execute_values(
                        cur,
                        """
                        INSERT INTO rag_embeddings 
                        (id, chunk_text, embedding_vector, metadata, created_at, updated_at)
                        VALUES %s
                        """,
                        values,
                        template="(%s, %s, %s::vector, %s, %s, %s)"
                    )
                else:
                    # Con JSONB
                    execute_values(
                        cur,
                        """
                        INSERT INTO rag_embeddings 
                        (id, chunk_text, embedding_vector, metadata, created_at, updated_at)
                        VALUES %s
                        """,
                        values,
                        template="(%s, %s, %s::jsonb, %s, %s, %s)"
                    )
                
                logger.info("🔵 INSERT completado, ejecutando COMMIT...")
                self.conn.commit()
                logger.info(f"✅ {len(values)} documentos CONFIRMADOS en PostgreSQL (COMMIT exitoso)")
                
                # Verificar que realmente se insertaron
                cur.execute("SELECT COUNT(*) FROM rag_embeddings")
                total_count = cur.fetchone()[0]
                logger.info(f"📊 Total de documentos en tabla rag_embeddings: {total_count}")
                
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
                if self.use_vector_type:
                    # Búsqueda con pgvector (mucho más eficiente)
                    query_vector_str = '[' + ','.join(str(x) for x in query_embedding) + ']'
                    
                    cur.execute("""
                        SELECT 
                            id,
                            chunk_text,
                            metadata,
                            1 - (embedding_vector <=> %s::vector) as similarity
                        FROM rag_embeddings
                        ORDER BY embedding_vector <=> %s::vector
                        LIMIT %s;
                    """, (query_vector_str, query_vector_str, n_results * 2))
                    
                    results = []
                    for row in cur.fetchall():
                        doc_id, chunk_text, metadata, similarity = row
                        
                        # Filtrar por threshold
                        if similarity < similarity_threshold:
                            continue
                        
                        results.append({
                            'id': str(doc_id),
                            'document': chunk_text,
                            'content': chunk_text,
                            'metadata': metadata,
                            'similarity_score': float(similarity),
                            'distance': float(1 - similarity),
                            'rank': len(results) + 1
                        })
                        
                        if len(results) >= n_results:
                            break
                else:
                    # Búsqueda manual con JSONB (menos eficiente pero funciona)
                    query_vector = json.dumps(query_embedding)
                    
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
