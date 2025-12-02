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
                
                # Verificar si la tabla existe y su tipo de columna
                cur.execute("""
                    SELECT column_name, data_type, udt_name
                    FROM information_schema.columns
                    WHERE table_name = 'rag_embeddings' 
                    AND column_name = 'embedding_vector'
                """)
                existing_column = cur.fetchone()
                
                # Si la tabla existe pero con tipo incorrecto, migrar
                if existing_column:
                    column_type = existing_column[2]  # udt_name
                    
                    if use_vector and column_type != 'vector':
                        logger.warning(f"⚠️ Columna embedding_vector es tipo '{column_type}', migrando a vector...")
                        
                        # Renombrar tabla antigua
                        cur.execute("ALTER TABLE IF EXISTS rag_embeddings RENAME TO rag_embeddings_old;")
                        self.conn.commit()
                        logger.info("✅ Tabla antigua respaldada como rag_embeddings_old")
                
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
                    
                    # Migrar datos de tabla antigua si existe
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'rag_embeddings_old'
                        )
                    """)
                    if cur.fetchone()[0]:
                        logger.info("🔄 Migrando datos de rag_embeddings_old...")
                        try:
                            # Migrar datos - convertir TEXT/JSONB a vector
                            cur.execute(f"""
                                INSERT INTO rag_embeddings (id, chunk_text, embedding_vector, metadata, created_at, updated_at)
                                SELECT 
                                    id,
                                    chunk_text,
                                    CASE 
                                        WHEN embedding_vector::text LIKE '[%' THEN embedding_vector::text::vector({self.embedding_dim})
                                        ELSE NULL
                                    END as embedding_vector,
                                    metadata,
                                    created_at,
                                    updated_at
                                FROM rag_embeddings_old
                                WHERE embedding_vector IS NOT NULL
                            """)
                            migrated = cur.rowcount
                            self.conn.commit()
                            logger.info(f"✅ {migrated} embeddings migrados exitosamente")
                            
                            # Eliminar tabla antigua
                            cur.execute("DROP TABLE rag_embeddings_old;")
                            self.conn.commit()
                            logger.info("✅ Tabla antigua eliminada")
                        except Exception as migrate_error:
                            logger.error(f"❌ Error migrando datos: {migrate_error}")
                            self.conn.rollback()
                    
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
    
    def check_document_exists(self, file_name: str, file_hash: str = None) -> bool:
        """
        Verificar si un documento ya tiene embeddings
        
        Args:
            file_name: Nombre del archivo
            file_hash: Hash opcional del contenido del archivo
            
        Returns:
            True si el documento ya fue procesado
        """
        if not self.is_ready():
            return False
        
        try:
            with self.conn.cursor() as cur:
                if file_hash:
                    # Verificar por hash (más preciso)
                    cur.execute("""
                        SELECT COUNT(*) FROM rag_embeddings 
                        WHERE metadata->>'file_name' = %s 
                        AND metadata->>'file_hash' = %s
                    """, (file_name, file_hash))
                else:
                    # Verificar solo por nombre
                    cur.execute("""
                        SELECT COUNT(*) FROM rag_embeddings 
                        WHERE metadata->>'file_name' = %s
                    """, (file_name,))
                
                count = cur.fetchone()[0]
                return count > 0
                
        except Exception as e:
            logger.error(f"❌ Error verificando duplicado: {e}")
            return False
    
    def get_processed_files(self) -> List[Dict[str, Any]]:
        """
        Obtener lista de archivos procesados con estadísticas
        
        Returns:
            Lista de archivos con chunks y metadatos
        """
        if not self.is_ready():
            return []
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        metadata->>'file_name' as file_name,
                        metadata->>'file_hash' as file_hash,
                        metadata->>'type' as file_type,
                        COUNT(*) as chunks_count,
                        MIN(created_at) as first_processed,
                        MAX(created_at) as last_processed
                    FROM rag_embeddings
                    WHERE metadata->>'file_name' IS NOT NULL
                    GROUP BY metadata->>'file_name', metadata->>'file_hash', metadata->>'type'
                    ORDER BY last_processed DESC
                """)
                
                results = []
                for row in cur.fetchall():
                    results.append({
                        'file_name': row[0],
                        'file_hash': row[1],
                        'file_type': row[2],
                        'chunks_count': row[3],
                        'first_processed': row[4].isoformat() if row[4] else None,
                        'last_processed': row[5].isoformat() if row[5] else None,
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo archivos procesados: {e}")
            return []
    
    def delete_document_embeddings(self, file_name: str, file_hash: str = None) -> int:
        """
        Eliminar todos los embeddings de un documento específico
        
        Args:
            file_name: Nombre del archivo
            file_hash: Hash opcional del archivo
            
        Returns:
            Cantidad de embeddings eliminados
        """
        if not self.is_ready():
            return 0
        
        try:
            with self.conn.cursor() as cur:
                if file_hash:
                    cur.execute("""
                        DELETE FROM rag_embeddings 
                        WHERE metadata->>'file_name' = %s 
                        AND metadata->>'file_hash' = %s
                        RETURNING id
                    """, (file_name, file_hash))
                else:
                    cur.execute("""
                        DELETE FROM rag_embeddings 
                        WHERE metadata->>'file_name' = %s
                        RETURNING id
                    """, (file_name,))
                
                deleted_count = len(cur.fetchall())
                self.conn.commit()
                
                logger.info(f"🗑️ Eliminados {deleted_count} embeddings de '{file_name}'")
                return deleted_count
                
        except Exception as e:
            logger.error(f"❌ Error eliminando embeddings: {e}")
            self.conn.rollback()
            return 0

    def search_lexical(self, query: str, keywords: List[str] = None, 
                        n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Búsqueda léxica (full-text search) para coincidencias exactas de palabras.
        Complementa la búsqueda semántica para mejorar precisión.
        
        Args:
            query: Consulta original del usuario
            keywords: Lista de palabras clave (opcional)
            n_results: Número de resultados a retornar
        
        Returns:
            Lista de documentos con scores léxicos
        """
        if not self.is_ready():
            logger.error("❌ PostgreSQL no está listo para búsqueda léxica")
            return []
        
        try:
            # Extraer keywords si no se proporcionan
            if not keywords:
                import re
                stopwords = {
                    'el', 'la', 'los', 'las', 'de', 'del', 'y', 'en', 'un', 'una', 'que', 
                    'se', 'con', 'por', 'para', 'como', 'al', 'lo', 'su', 'sus', 'es', 'son',
                    'o', 'a', 'e', 'sobre', 'qué', 'cual', 'cuál', 'quién', 'cómo', 'dónde',
                    'the', 'a', 'an', 'is', 'are', 'of', 'to', 'in', 'for', 'on', 'with',
                    'dice', 'menciona', 'habla', 'trata', 'explica', 'describe', 'documento'
                }
                words = re.findall(r'\b\w+\b', query.lower())
                keywords = [w for w in words if len(w) > 2 and w not in stopwords]
            
            if not keywords:
                logger.warning("⚠️ No se encontraron keywords para búsqueda léxica")
                return []
            
            logger.info(f"🔤 Búsqueda léxica con keywords: {keywords[:10]}")
            
            with self.conn.cursor() as cur:
                # Construir condiciones de búsqueda
                # Método 1: ILIKE para coincidencias parciales (más flexible)
                conditions = []
                params = []
                
                for keyword in keywords[:15]:  # Limitar a 15 keywords
                    conditions.append("chunk_text ILIKE %s")
                    params.append(f"%{keyword}%")
                
                if not conditions:
                    return []
                
                # También buscar la consulta completa (boost alto si coincide)
                conditions.append("chunk_text ILIKE %s")
                params.append(f"%{query[:100]}%")  # Limitar longitud
                
                # Query con scoring basado en coincidencias
                query_sql = f"""
                    WITH keyword_matches AS (
                        SELECT 
                            id,
                            chunk_text,
                            metadata,
                            (
                                {' + '.join([f"(CASE WHEN chunk_text ILIKE %s THEN 1 ELSE 0 END)" for _ in keywords[:15]])}
                            ) as keyword_count,
                            CASE WHEN chunk_text ILIKE %s THEN 0.5 ELSE 0 END as exact_phrase_bonus
                        FROM rag_embeddings
                        WHERE {' OR '.join(conditions)}
                    )
                    SELECT 
                        id,
                        chunk_text,
                        metadata,
                        keyword_count,
                        exact_phrase_bonus,
                        (keyword_count::float / {len(keywords[:15])}) + exact_phrase_bonus as lexical_score
                    FROM keyword_matches
                    WHERE keyword_count > 0 OR exact_phrase_bonus > 0
                    ORDER BY lexical_score DESC, keyword_count DESC
                    LIMIT %s;
                """
                
                # Parámetros: keywords para CASE, frase exacta para bonus, keywords para WHERE, frase para WHERE, límite
                all_params = []
                # Para los CASE statements
                for keyword in keywords[:15]:
                    all_params.append(f"%{keyword}%")
                # Para exact phrase bonus
                all_params.append(f"%{query[:100]}%")
                # Para las condiciones WHERE (ya están en params)
                all_params.extend(params)
                # Límite
                all_params.append(n_results * 2)
                
                cur.execute(query_sql, all_params)
                
                results = []
                for row in cur.fetchall():
                    doc_id, chunk_text, metadata, keyword_count, phrase_bonus, lexical_score = row
                    
                    results.append({
                        'id': str(doc_id),
                        'document': chunk_text,
                        'content': chunk_text,
                        'metadata': metadata,
                        'similarity_score': min(float(lexical_score), 1.0),
                        'lexical_score': float(lexical_score),
                        'keyword_matches': int(keyword_count),
                        'search_type': 'lexical',
                        'rank': len(results) + 1
                    })
                    
                    if len(results) >= n_results:
                        break
                
                logger.info(f"🔤 Búsqueda léxica completada: {len(results)} resultados")
                return results
                
        except Exception as e:
            logger.error(f"❌ Error en búsqueda léxica: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_all_documents(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Obtener todos los documentos (para búsqueda léxica en memoria)
        
        Args:
            limit: Número máximo de documentos
        
        Returns:
            Lista de documentos
        """
        if not self.is_ready():
            return []
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id, chunk_text, metadata
                    FROM rag_embeddings
                    LIMIT %s;
                """, (limit,))
                
                results = []
                for row in cur.fetchall():
                    doc_id, chunk_text, metadata = row
                    results.append({
                        'id': str(doc_id),
                        'document': chunk_text,
                        'content': chunk_text,
                        'metadata': metadata
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo documentos: {e}")
            return []

    def reset_collection(self) -> int:
        """
        Eliminar todos los embeddings (CUIDADO)
        
        Returns:
            Cantidad de embeddings eliminados
        """
        if not self.is_ready():
            return 0
        
        try:
            with self.conn.cursor() as cur:
                # Contar antes de eliminar
                cur.execute("SELECT COUNT(*) FROM rag_embeddings;")
                count = cur.fetchone()[0]
                
                cur.execute("TRUNCATE TABLE rag_embeddings;")
                self.conn.commit()
                
                logger.info(f"🔄 Tabla rag_embeddings vaciada: {count} embeddings eliminados")
                return count
                
        except Exception as e:
            logger.error(f"❌ Error vaciando tabla: {e}")
            if self.conn:
                self.conn.rollback()
            return 0
    
    def close(self):
        """Cerrar conexión"""
        if self.conn:
            self.conn.close()
            logger.info("✅ Conexión PostgreSQL cerrada")
