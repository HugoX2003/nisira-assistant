"""
Document Loader Utility
=======================

Utilidad para cargar documentos desde PostgreSQL o filesystem
de manera transparente para el procesador.
"""

import os
import tempfile
import logging
from typing import Optional
from contextlib import contextmanager

from ..storage.postgres_file_store import PostgresFileStore

logger = logging.getLogger(__name__)


class DocumentLoader:
    """
    Cargador de documentos que abstrae el origen (PostgreSQL o filesystem)
    """
    
    def __init__(self):
        database_url = os.getenv('DATABASE_URL')
        self.use_postgres = bool(database_url)
        
        if self.use_postgres:
            self.file_store = PostgresFileStore(database_url)
            if self.file_store.is_ready():
                logger.info("✅ DocumentLoader usando PostgreSQL")
            else:
                logger.warning("⚠️  PostgreSQL no disponible, usando filesystem")
                self.use_postgres = False
        else:
            self.use_postgres = False
    
    @contextmanager
    def get_file_path(self, file_name: str, file_id: str = None):
        """
        Context manager que proporciona una ruta de archivo válida.
        Si el archivo está en PostgreSQL, lo descarga temporalmente.
        
        Args:
            file_name: Nombre del archivo
            file_id: ID del archivo en PostgreSQL (opcional)
        
        Yields:
            Ruta del archivo (temporal si viene de PostgreSQL)
        """
        temp_path = None
        
        try:
            if self.use_postgres:
                # Obtener archivo de PostgreSQL
                file_data = self.file_store.get_file(
                    file_id=file_id,
                    file_name=file_name
                )
                
                if not file_data:
                    logger.error(f"❌ Archivo no encontrado en PostgreSQL: {file_name}")
                    raise FileNotFoundError(f"Archivo no encontrado: {file_name}")
                
                # Crear archivo temporal
                suffix = os.path.splitext(file_name)[1]
                with tempfile.NamedTemporaryFile(
                    mode='wb',
                    suffix=suffix,
                    delete=False
                ) as temp_file:
                    temp_file.write(file_data['file_content'])
                    temp_path = temp_file.name
                
                logger.debug(f"📄 Archivo temporal creado: {file_name} -> {temp_path}")
                yield temp_path
            else:
                # Usar filesystem directamente
                from ..config import GOOGLE_DRIVE_CONFIG
                download_path = GOOGLE_DRIVE_CONFIG['download_path']
                file_path = os.path.join(download_path, file_name)
                
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
                
                yield file_path
        
        finally:
            # Limpiar archivo temporal si se creó
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                    logger.debug(f"🗑️  Archivo temporal eliminado: {temp_path}")
                except Exception as e:
                    logger.warning(f"⚠️  Error eliminando archivo temporal: {e}")
    
    def list_available_files(self):
        """
        Listar archivos disponibles para procesamiento
        
        Returns:
            Lista de diccionarios con información de archivos
        """
        if self.use_postgres:
            return self.file_store.list_files()
        else:
            from ..config import GOOGLE_DRIVE_CONFIG
            download_path = GOOGLE_DRIVE_CONFIG['download_path']
            
            if not os.path.exists(download_path):
                return []
            
            files = []
            for filename in os.listdir(download_path):
                file_path = os.path.join(download_path, filename)
                if os.path.isfile(file_path):
                    files.append({
                        'file_name': filename,
                        'file_size': os.path.getsize(file_path),
                        'storage': 'filesystem'
                    })
            
            return files
    
    def get_storage_type(self) -> str:
        """
        Obtener tipo de almacenamiento usado
        
        Returns:
            'postgres' o 'filesystem'
        """
        return 'postgres' if self.use_postgres else 'filesystem'
