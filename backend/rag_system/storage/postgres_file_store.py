"""
PostgreSQL File Store
====================

Almacenamiento persistente de archivos (PDFs) en PostgreSQL
como alternativa al filesystem efímero de DigitalOcean.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

try:
    import psycopg2
    from psycopg2.extras import Json
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

logger = logging.getLogger(__name__)


class PostgresFileStore:
    """
    Almacenamiento de archivos binarios en PostgreSQL
    """
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        self.conn = None
        
        if not PSYCOPG2_AVAILABLE:
            logger.error("❌ psycopg2 no disponible")
            return
        
        self._initialize_connection()
        self._ensure_table_exists()
    
    def _initialize_connection(self):
        """Conectar a PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                self.database_url,
                connect_timeout=10,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5
            )
            self.conn.autocommit = False
            logger.info("✅ Conectado a PostgreSQL para almacenamiento de archivos")
        except Exception as e:
            logger.error(f"❌ Error conectando a PostgreSQL: {e}")
            self.conn = None
    
    def _ensure_connection(self):
        """Verificar y reconectar si es necesario"""
        try:
            if self.conn is None or self.conn.closed:
                logger.warning("⚠️ Conexión cerrada, reconectando...")
                self._initialize_connection()
                if self.conn and not self.conn.closed:
                    self._ensure_table_exists()
                return self.conn is not None and not self.conn.closed
            
            # Verificar que la conexión esté viva
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Conexión perdida, reconectando: {e}")
            try:
                if self.conn:
                    self.conn.close()
            except:
                pass
            self._initialize_connection()
            if self.conn and not self.conn.closed:
                self._ensure_table_exists()
            return self.conn is not None and not self.conn.closed
    
    def _ensure_table_exists(self):
        """Crear tabla de archivos si no existe"""
        if not self.conn:
            return
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS document_files (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        file_name TEXT NOT NULL,
                        file_content BYTEA NOT NULL,
                        file_size BIGINT NOT NULL,
                        mime_type TEXT,
                        drive_file_id TEXT,
                        drive_modified_time TIMESTAMP,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(drive_file_id)
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_file_name 
                    ON document_files(file_name);
                    
                    CREATE INDEX IF NOT EXISTS idx_drive_file_id 
                    ON document_files(drive_file_id);
                    
                    CREATE INDEX IF NOT EXISTS idx_created_at 
                    ON document_files(created_at DESC);
                """)
                
                self.conn.commit()
                logger.info("✅ Tabla document_files lista")
                
        except Exception as e:
            logger.error(f"❌ Error creando tabla document_files: {e}")
            if self.conn:
                self.conn.rollback()
    
    def is_ready(self) -> bool:
        """Verificar si el store está listo"""
        if not PSYCOPG2_AVAILABLE:
            return False
        return self._ensure_connection()
    
    def save_file(self, 
                  file_name: str, 
                  file_content: bytes,
                  mime_type: str = None,
                  drive_file_id: str = None,
                  drive_modified_time: datetime = None,
                  metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Guardar archivo en PostgreSQL
        
        Args:
            file_name: Nombre del archivo
            file_content: Contenido binario del archivo
            mime_type: Tipo MIME del archivo
            drive_file_id: ID del archivo en Google Drive
            drive_modified_time: Fecha de modificación en Drive
            metadata: Metadatos adicionales
        
        Returns:
            UUID del archivo guardado o None si falló
        """
        if not self.is_ready():
            logger.error("❌ PostgreSQL no está listo")
            return None
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                file_id = str(uuid.uuid4())
                file_size = len(file_content)
                now = datetime.now()
                
                with self.conn.cursor() as cur:
                    # Verificar si ya existe el archivo de Drive
                    if drive_file_id:
                        cur.execute(
                            "SELECT id FROM document_files WHERE drive_file_id = %s",
                            (drive_file_id,)
                        )
                        existing = cur.fetchone()
                        
                        if existing:
                            # Actualizar archivo existente
                            logger.info(f"📝 Actualizando archivo existente: {file_name}")
                            cur.execute("""
                                UPDATE document_files 
                                SET file_content = %s,
                                    file_size = %s,
                                    mime_type = %s,
                                    drive_modified_time = %s,
                                    metadata = %s,
                                    updated_at = %s
                                WHERE drive_file_id = %s
                                RETURNING id
                            """, (
                                psycopg2.Binary(file_content),
                                file_size,
                                mime_type,
                                drive_modified_time,
                                Json(metadata or {}),
                                now,
                                drive_file_id
                            ))
                            file_id = str(cur.fetchone()[0])
                        else:
                            # Insertar nuevo archivo
                            cur.execute("""
                                INSERT INTO document_files 
                                (id, file_name, file_content, file_size, mime_type, 
                                 drive_file_id, drive_modified_time, metadata, created_at, updated_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                file_id,
                                file_name,
                                psycopg2.Binary(file_content),
                                file_size,
                                mime_type,
                                drive_file_id,
                                drive_modified_time,
                                Json(metadata or {}),
                                now,
                                now
                            ))
                    else:
                        # Sin drive_file_id, insertar directamente
                        cur.execute("""
                            INSERT INTO document_files 
                            (id, file_name, file_content, file_size, mime_type, 
                             metadata, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            file_id,
                            file_name,
                            psycopg2.Binary(file_content),
                            file_size,
                            mime_type,
                            Json(metadata or {}),
                            now,
                            now
                        ))
                    
                    self.conn.commit()
                    logger.info(f"💾 Archivo guardado en PostgreSQL: {file_name} ({file_size} bytes)")
                    return file_id
                    
            except Exception as e:
                logger.error(f"❌ Error guardando archivo {file_name} (intento {attempt+1}/{max_retries}): {e}")
                if self.conn:
                    try:
                        self.conn.rollback()
                    except:
                        pass
                
                if attempt < max_retries - 1:
                    # Reconectar y reintentar
                    if not self._ensure_connection():
                        return None
                else:
                    return None
        
        return None
    
    def get_file(self, file_id: str = None, file_name: str = None) -> Optional[Dict[str, Any]]:
        """
        Obtener archivo de PostgreSQL
        
        Args:
            file_id: UUID del archivo
            file_name: Nombre del archivo (alternativa a file_id)
        
        Returns:
            Diccionario con datos del archivo o None
        """
        if not self.is_ready():
            return None
        
        if not file_id and not file_name:
            logger.error("❌ Debe proporcionar file_id o file_name")
            return None
        
        try:
            with self.conn.cursor() as cur:
                if file_id:
                    cur.execute("""
                        SELECT id, file_name, file_content, file_size, mime_type,
                               drive_file_id, drive_modified_time, metadata, created_at
                        FROM document_files
                        WHERE id = %s
                    """, (file_id,))
                else:
                    cur.execute("""
                        SELECT id, file_name, file_content, file_size, mime_type,
                               drive_file_id, drive_modified_time, metadata, created_at
                        FROM document_files
                        WHERE file_name = %s
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, (file_name,))
                
                row = cur.fetchone()
                
                if not row:
                    return None
                
                return {
                    'id': str(row[0]),
                    'file_name': row[1],
                    'file_content': bytes(row[2]),
                    'file_size': row[3],
                    'mime_type': row[4],
                    'drive_file_id': row[5],
                    'drive_modified_time': row[6],
                    'metadata': row[7],
                    'created_at': row[8]
                }
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo archivo: {e}")
            return None
    
    def list_files(self, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Listar archivos almacenados
        
        Args:
            limit: Número máximo de resultados
            offset: Offset para paginación
        
        Returns:
            Lista de archivos (sin contenido binario)
        """
        if not self.is_ready():
            return []
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id, file_name, file_size, mime_type, 
                           drive_file_id, drive_modified_time, created_at
                    FROM document_files
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                
                files = []
                for row in cur.fetchall():
                    files.append({
                        'id': str(row[0]),
                        'file_name': row[1],
                        'file_size': row[2],
                        'mime_type': row[3],
                        'drive_file_id': row[4],
                        'drive_modified_time': row[5],
                        'created_at': row[6]
                    })
                
                return files
                
        except Exception as e:
            logger.error(f"❌ Error listando archivos: {e}")
            return []
    
    def file_exists(self, drive_file_id: str) -> bool:
        """
        Verificar si un archivo de Drive ya existe
        
        Args:
            drive_file_id: ID del archivo en Google Drive
        
        Returns:
            True si existe
        """
        if not self.is_ready():
            return False
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.conn.cursor() as cur:
                    cur.execute("""
                        SELECT EXISTS(
                            SELECT 1 FROM document_files 
                            WHERE drive_file_id = %s
                        )
                    """, (drive_file_id,))
                    
                    return cur.fetchone()[0]
                    
            except Exception as e:
                logger.error(f"❌ Error verificando existencia (intento {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    # Reconectar y reintentar
                    if not self._ensure_connection():
                        return False
                else:
                    return False
        
        return False
    
    def get_file_modified_time(self, drive_file_id: str) -> Optional[datetime]:
        """
        Obtener fecha de modificación de un archivo
        
        Args:
            drive_file_id: ID del archivo en Drive
        
        Returns:
            Fecha de modificación o None
        """
        if not self.is_ready():
            return None
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.conn.cursor() as cur:
                    cur.execute("""
                        SELECT drive_modified_time
                        FROM document_files
                        WHERE drive_file_id = %s
                    """, (drive_file_id,))
                    
                    row = cur.fetchone()
                    return row[0] if row else None
                    
            except Exception as e:
                logger.error(f"❌ Error obteniendo fecha (intento {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    # Reconectar y reintentar
                    if not self._ensure_connection():
                        return None
                else:
                    return None
        
        return None
    
    def delete_file(self, file_id: str) -> bool:
        """
        Eliminar archivo
        
        Args:
            file_id: UUID del archivo
        
        Returns:
            True si se eliminó
        """
        if not self.is_ready():
            return False
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM document_files WHERE id = %s", (file_id,))
                self.conn.commit()
                
                deleted = cur.rowcount > 0
                if deleted:
                    logger.info(f"🗑️  Archivo eliminado: {file_id}")
                
                return deleted
                
        except Exception as e:
            logger.error(f"❌ Error eliminando archivo: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de almacenamiento
        
        Returns:
            Estadísticas de archivos
        """
        if not self.is_ready():
            return {"ready": False}
        
        try:
            with self.conn.cursor() as cur:
                # Total de archivos
                cur.execute("SELECT COUNT(*) FROM document_files")
                total_files = cur.fetchone()[0]
                
                # Tamaño total
                cur.execute("SELECT SUM(file_size) FROM document_files")
                total_size = cur.fetchone()[0] or 0
                
                # Tamaño de la tabla
                cur.execute("""
                    SELECT pg_size_pretty(pg_total_relation_size('document_files'))
                """)
                table_size = cur.fetchone()[0]
                
                # Archivos por tipo MIME
                cur.execute("""
                    SELECT mime_type, COUNT(*) 
                    FROM document_files 
                    GROUP BY mime_type
                    ORDER BY COUNT(*) DESC
                """)
                by_mime = dict(cur.fetchall())
                
                return {
                    "ready": True,
                    "total_files": total_files,
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "table_size": table_size,
                    "by_mime_type": by_mime
                }
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {"ready": False, "error": str(e)}
    
    def close(self):
        """Cerrar conexión"""
        if self.conn:
            self.conn.close()
            logger.info("✅ Conexión PostgreSQL cerrada")
