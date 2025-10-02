"""
Google Drive Manager
==================

Gestiona la conexión y sincronización de documentos desde Google Drive.
Utiliza las credenciales existentes en credentials.json para acceder a la API.
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import io

try:
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseDownload
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False

from ..config import GOOGLE_DRIVE_CONFIG

logger = logging.getLogger(__name__)

class GoogleDriveManager:
    """
    Gestor de Google Drive para sincronización de documentos
    """
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self.folder_id = GOOGLE_DRIVE_CONFIG['folder_id']
        self.download_path = GOOGLE_DRIVE_CONFIG['download_path']
        self.supported_formats = GOOGLE_DRIVE_CONFIG['supported_formats']
        
        # Crear directorio de descarga si no existe
        os.makedirs(self.download_path, exist_ok=True)
        
        # Inicializar servicio
        self._initialize_service()
    
    def _initialize_service(self):
        """Inicializar el servicio de Google Drive"""
        if not GOOGLE_APIS_AVAILABLE:
            logger.error("Google APIs no están disponibles. Instalar google-api-python-client")
            return False
        
        credentials_path = GOOGLE_DRIVE_CONFIG['credentials_path']
        
        if not os.path.exists(credentials_path):
            logger.error(f"Archivo de credenciales no encontrado: {credentials_path}")
            return False
        
        try:
            # Cargar credenciales
            with open(credentials_path, 'r', encoding='utf-8') as f:
                cred_data = json.load(f)
            
            # Determinar tipo de credenciales
            if 'type' in cred_data and cred_data['type'] == 'service_account':
                # Credenciales de cuenta de servicio
                self.credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=GOOGLE_DRIVE_CONFIG['scopes']
                )
                logger.info("✅ Credenciales de cuenta de servicio cargadas")
            else:
                # Credenciales OAuth2 (usuario)
                logger.warning("⚠️  Credenciales OAuth2 detectadas. Se recomienda usar cuenta de servicio.")
                # Para OAuth2 necesitarías implementar el flujo completo
                return False
            
            # Construir servicio
            self.service = build('drive', 'v3', credentials=self.credentials)
            logger.info("✅ Servicio de Google Drive inicializado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Google Drive: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Verificar si está autenticado con Google Drive"""
        if not self.service:
            return False
        
        try:
            # Probar acceso con una consulta simple
            self.service.about().get(fields="user").execute()
            return True
        except Exception as e:
            logger.error(f"Error verificando autenticación: {e}")
            return False
    
    def list_files(self, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Listar archivos en Google Drive
        
        Args:
            folder_id: ID de carpeta específica (usa la configurada por defecto si no se especifica)
        
        Returns:
            Lista de archivos con metadatos
        """
        if not self.service:
            logger.error("Servicio de Google Drive no inicializado")
            return []
        
        target_folder = folder_id or self.folder_id
        
        try:
            # Consulta para archivos en la carpeta especificada
            query = f"'{target_folder}' in parents and trashed=false"
            
            # Agregar filtro de formatos soportados
            if self.supported_formats:
                format_queries = []
                for fmt in self.supported_formats:
                    if fmt.startswith('.'):
                        # Extensión de archivo
                        format_queries.append(f"name contains '{fmt}'")
                    else:
                        # Tipo MIME
                        format_queries.append(f"mimeType='{fmt}'")
                
                if format_queries:
                    query += f" and ({' or '.join(format_queries)})"
            
            results = self.service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, parents)"
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"📁 Encontrados {len(files)} archivos en Google Drive")
            
            return files
            
        except HttpError as e:
            logger.error(f"❌ Error listando archivos: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            return []
    
    def download_file(self, file_id: str, file_name: str) -> Optional[str]:
        """
        Descargar un archivo de Google Drive
        
        Args:
            file_id: ID del archivo en Google Drive
            file_name: Nombre del archivo
        
        Returns:
            Ruta local del archivo descargado o None si falló
        """
        if not self.service:
            logger.error("Servicio de Google Drive no inicializado")
            return None
        
        try:
            # Obtener metadatos del archivo
            file_metadata = self.service.files().get(fileId=file_id).execute()
            mime_type = file_metadata.get('mimeType', '')
            
            # Ruta de destino
            local_path = os.path.join(self.download_path, file_name)
            
            # Descargar archivo
            if 'google-apps' in mime_type:
                # Archivo de Google Workspace - exportar como PDF
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType='application/pdf'
                )
                local_path = local_path.replace(os.path.splitext(local_path)[1], '.pdf')
            else:
                # Archivo normal
                request = self.service.files().get_media(fileId=file_id)
            
            # Descargar contenido
            with io.FileIO(local_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.debug(f"Descarga {int(status.progress() * 100)}% - {file_name}")
            
            logger.info(f"✅ Archivo descargado: {local_path}")
            return local_path
            
        except HttpError as e:
            logger.error(f"❌ Error descargando {file_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado descargando {file_name}: {e}")
            return None
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información detallada de un archivo
        
        Args:
            file_id: ID del archivo
        
        Returns:
            Diccionario con información del archivo
        """
        if not self.service:
            return None
        
        try:
            file_info = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, modifiedTime, createdTime, parents, description"
            ).execute()
            
            return file_info
            
        except Exception as e:
            logger.error(f"Error obteniendo información del archivo {file_id}: {e}")
            return None
    
    def sync_documents(self) -> Dict[str, Any]:
        """
        Sincronizar todos los documentos de la carpeta configurada
        
        Returns:
            Resultado de la sincronización
        """
        if not self.service:
            return {
                "success": False,
                "error": "Servicio de Google Drive no inicializado"
            }
        
        logger.info("🔄 Iniciando sincronización de documentos desde Google Drive")
        
        try:
            # Listar archivos en Drive
            files = self.list_files()
            
            if not files:
                return {
                    "success": True,
                    "message": "No se encontraron archivos para sincronizar",
                    "files_processed": 0
                }
            
            # Directorio local para comparar
            local_files = os.listdir(self.download_path) if os.path.exists(self.download_path) else []
            
            downloaded_files = []
            skipped_files = []
            errors = []
            
            for file_info in files:
                file_id = file_info['id']
                file_name = file_info['name']
                modified_time = file_info.get('modifiedTime')
                
                # Verificar si ya existe localmente
                local_path = os.path.join(self.download_path, file_name)
                
                should_download = True
                
                if os.path.exists(local_path):
                    # Comparar fechas de modificación
                    local_mtime = datetime.fromtimestamp(
                        os.path.getmtime(local_path), 
                        tz=timezone.utc
                    )
                    
                    if modified_time:
                        drive_mtime = datetime.fromisoformat(
                            modified_time.replace('Z', '+00:00')
                        )
                        
                        if local_mtime >= drive_mtime:
                            should_download = False
                            skipped_files.append(file_name)
                
                if should_download:
                    downloaded_path = self.download_file(file_id, file_name)
                    if downloaded_path:
                        downloaded_files.append({
                            "name": file_name,
                            "path": downloaded_path,
                            "id": file_id,
                            "modified_time": modified_time
                        })
                    else:
                        errors.append(f"Error descargando {file_name}")
            
            result = {
                "success": True,
                "files_processed": len(files),
                "downloaded": len(downloaded_files),
                "skipped": len(skipped_files),
                "errors": len(errors),
                "downloaded_files": downloaded_files,
                "skipped_files": skipped_files
            }
            
            if errors:
                result["error_details"] = errors
            
            logger.info(f"✅ Sincronización completada: {len(downloaded_files)} descargados, {len(skipped_files)} omitidos")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en sincronización: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def setup_folder_monitoring(self) -> bool:
        """
        Configurar monitoreo de cambios en la carpeta (para implementación futura)
        
        Returns:
            True si se configuró correctamente
        """
        # Placeholder para monitoreo en tiempo real
        # Requeriría webhooks o polling periódico
        logger.info("⚠️  Monitoreo de carpetas no implementado aún")
        return False
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Obtener estado actual de sincronización
        
        Returns:
            Estado detallado
        """
        status = {
            "authenticated": self.is_authenticated(),
            "folder_id": self.folder_id,
            "download_path": self.download_path,
            "supported_formats": self.supported_formats
        }
        
        if os.path.exists(self.download_path):
            local_files = os.listdir(self.download_path)
            status["local_files_count"] = len(local_files)
            status["local_files"] = local_files
        else:
            status["local_files_count"] = 0
            status["local_files"] = []
        
        return status