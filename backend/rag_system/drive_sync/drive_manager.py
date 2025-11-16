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
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False

from ..config import GOOGLE_DRIVE_CONFIG
from ..storage.postgres_file_store import PostgresFileStore

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
        self.token_path = str(GOOGLE_DRIVE_CONFIG.get('token_file', 'data/token.json'))
        
        # Inicializar PostgreSQL File Store para almacenamiento persistente
        database_url = os.getenv('DATABASE_URL')
        self.use_postgres = bool(database_url)
        
        if self.use_postgres:
            self.file_store = PostgresFileStore(database_url)
            if self.file_store.is_ready():
                logger.info("✅ Usando PostgreSQL para almacenamiento de archivos (PERSISTENTE)")
            else:
                logger.warning("⚠️  PostgreSQL no disponible, usando filesystem (EFÍMERO)")
                self.use_postgres = False
        else:
            logger.warning("⚠️  DATABASE_URL no configurado, usando filesystem (EFÍMERO)")
            self.use_postgres = False
        
        # Crear directorio de descarga temporal si no se usa PostgreSQL
        if not self.use_postgres:
            os.makedirs(self.download_path, exist_ok=True)
        
        # Inicializar servicio
        self._initialize_service()
    
    def _initialize_service(self):
        """Inicializar el servicio de Google Drive con Service Account"""
        if not GOOGLE_APIS_AVAILABLE:
            logger.error("Google APIs no están disponibles. Instalar google-api-python-client")
            return False
        
        try:
            credentials_path = GOOGLE_DRIVE_CONFIG['credentials_path']
            
            if not os.path.exists(credentials_path):
                logger.error(f"❌ Archivo de credenciales no encontrado: {credentials_path}")
                return False
            
            # Cargar credenciales
            with open(credentials_path, 'r', encoding='utf-8') as f:
                cred_data = json.load(f)
            
            # Verificar tipo de credenciales
            if 'type' in cred_data and cred_data['type'] == 'service_account':
                logger.info("� Usando Service Account credentials")
                creds = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=GOOGLE_DRIVE_CONFIG['scopes']
                )
                logger.info(f"✅ Service Account: {cred_data.get('client_email', 'N/A')}")
            else:
                # OAuth credentials (flujo antiguo - deprecated pero mantenido por compatibilidad)
                logger.info("🔑 Usando OAuth credentials")
                
                creds = None
                
                # Intentar cargar token existente
                if os.path.exists(self.token_path):
                    logger.info(f"🔑 Cargando token desde: {self.token_path}")
                    creds = Credentials.from_authorized_user_file(self.token_path, GOOGLE_DRIVE_CONFIG['scopes'])
                
                # Si no hay credenciales válidas, autenticar
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        logger.info("🔄 Refrescando token expirado...")
                        creds.refresh(Request())
                    else:
                        # Flujo OAuth
                        logger.info("🌐 Iniciando flujo de autenticación OAuth...")
                        flow = InstalledAppFlow.from_client_secrets_file(
                            credentials_path, 
                            GOOGLE_DRIVE_CONFIG['scopes']
                        )
                        creds = flow.run_local_server(port=0)
                        
                        # Guardar token
                        os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
                        with open(self.token_path, 'w') as token:
                            token.write(creds.to_json())
                        
                        logger.info(f"✅ Token guardado en: {self.token_path}")
            
            self.credentials = creds
            
            # Construir servicio
            self.service = build('drive', 'v3', credentials=self.credentials)
            logger.info("✅ Servicio de Google Drive inicializado correctamente")
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
            
            # Paginar para obtener TODOS los archivos
            all_files = []
            page_token = None
            
            while True:
                results = self.service.files().list(
                    q=query,
                    pageSize=1000,  # Máximo por página
                    pageToken=page_token,
                    fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, parents)"
                ).execute()
                
                files = results.get('files', [])
                all_files.extend(files)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break  # No hay más páginas
                
                logger.info(f"� Obtenidos {len(all_files)} archivos hasta ahora...")
            
            logger.info(f"📁 Total: {len(all_files)} archivos en Google Drive")
            
            return all_files
            
        except HttpError as e:
            logger.error(f"❌ Error listando archivos: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            return []
    
    def download_file(self, file_id: str, file_name: str, file_modified_time: str = None) -> Optional[str]:
        """
        Descargar un archivo de Google Drive y guardarlo en PostgreSQL o filesystem
        
        Args:
            file_id: ID del archivo en Google Drive
            file_name: Nombre del archivo
            file_modified_time: Fecha de modificación del archivo en Drive
        
        Returns:
            ID del archivo guardado (UUID para PostgreSQL, path para filesystem)
            o None si falló
            o "TOO_LARGE" si el archivo excede el límite de tamaño
        """
        if not self.service:
            logger.error("Servicio de Google Drive no inicializado")
            return None
        
        # Límite de tamaño para PostgreSQL (200MB - ajustado para servidor con RAM suficiente)
        MAX_FILE_SIZE_POSTGRES = 200 * 1024 * 1024  # 200MB
        
        try:
            # Obtener metadatos del archivo
            file_metadata = self.service.files().get(fileId=file_id, fields='id,name,mimeType,size').execute()
            mime_type = file_metadata.get('mimeType', '')
            file_size = int(file_metadata.get('size', 0))
            
            # Verificar tamaño si vamos a usar PostgreSQL
            if self.use_postgres and file_size > MAX_FILE_SIZE_POSTGRES:
                logger.warning(f"⚠️ Archivo muy grande ({file_size / 1024 / 1024:.1f}MB): {file_name}")
                logger.warning(f"   Límite para PostgreSQL: {MAX_FILE_SIZE_POSTGRES / 1024 / 1024:.0f}MB")
                logger.warning(f"   Saltando archivo para evitar crash del servidor")
                return "TOO_LARGE"
            
            # Descargar a memoria
            if 'google-apps' in mime_type:
                # Archivo de Google Workspace - exportar como PDF
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType='application/pdf'
                )
                file_name = os.path.splitext(file_name)[0] + '.pdf'
                mime_type = 'application/pdf'
            else:
                # Archivo normal
                request = self.service.files().get_media(fileId=file_id)
            
            # Descargar contenido a memoria con límite
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            done = False
            downloaded_size = 0
            
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    downloaded_size = int(status.resumable_progress)
                    
                    # Verificar tamaño durante descarga
                    if self.use_postgres and downloaded_size > MAX_FILE_SIZE_POSTGRES:
                        logger.warning(f"⚠️ Descarga excedió límite: {file_name} ({downloaded_size / 1024 / 1024:.1f}MB)")
                        return "TOO_LARGE"
                    logger.debug(f"Descarga {int(status.progress() * 100)}% - {file_name}")
            
            # Obtener bytes
            file_bytes = file_content.getvalue()
            
            # Guardar según configuración
            if self.use_postgres:
                # Guardar en PostgreSQL con manejo de errores
                modified_time = None
                if file_modified_time:
                    try:
                        modified_time = datetime.fromisoformat(
                            file_modified_time.replace('Z', '+00:00')
                        )
                    except:
                        pass
                
                logger.info(f"💾 Guardando en PostgreSQL: {file_name} ({len(file_bytes) / 1024 / 1024:.1f}MB)")
                
                try:
                    saved_id = self.file_store.save_file(
                        file_name=file_name,
                        file_content=file_bytes,
                        mime_type=mime_type,
                        drive_file_id=file_id,
                        drive_modified_time=modified_time,
                        metadata={
                            'source': 'google_drive',
                            'original_mime': file_metadata.get('mimeType', ''),
                            'size': len(file_bytes)
                        }
                    )
                    
                    if saved_id:
                        logger.info(f"✅ Guardado en PostgreSQL: {file_name} (ID: {saved_id})")
                        return saved_id
                    else:
                        logger.error(f"❌ Error guardando en PostgreSQL: {file_name}")
                        return None
                        
                except Exception as e:
                    # Detectar errores de OOM o memoria
                    error_msg = str(e).lower()
                    if 'memory' in error_msg or 'oom' in error_msg or 'out of memory' in error_msg:
                        logger.error(f"❌ Error de memoria al guardar {file_name} ({len(file_bytes) / 1024 / 1024:.1f}MB)")
                        logger.error(f"   Archivo muy grande para PostgreSQL, considere reducir MAX_FILE_SIZE_POSTGRES")
                    elif 'connection' in error_msg or 'closed' in error_msg:
                        logger.error(f"❌ Conexión PostgreSQL perdida al guardar {file_name}")
                        logger.error(f"   Posible crash del servidor - revisar logs de PostgreSQL")
                    else:
                        logger.error(f"❌ Error inesperado al guardar {file_name}: {e}")
                    return None
            else:
                # Guardar en filesystem (fallback)
                local_path = os.path.join(self.download_path, file_name)
                with open(local_path, 'wb') as f:
                    f.write(file_bytes)
                
                logger.info(f"📁 Archivo guardado en filesystem: {local_path}")
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
        logger.info(f"💾 Modo de almacenamiento: {'PostgreSQL (persistente)' if self.use_postgres else 'Filesystem (efímero)'}")
        
        try:
            # Listar archivos en Drive
            files = self.list_files()
            
            if not files:
                return {
                    "success": True,
                    "message": "No se encontraron archivos para sincronizar",
                    "files_processed": 0
                }
            
            downloaded_files = []
            skipped_files = []
            too_large_files = []  # Archivos omitidos por tamaño
            errors = []
            
            for file_info in files:
                file_id = file_info['id']
                file_name = file_info['name']
                modified_time = file_info.get('modifiedTime')
                
                should_download = True
                
                # Verificar si ya existe
                if self.use_postgres:
                    # Verificar en PostgreSQL
                    if self.file_store.file_exists(file_id):
                        # Verificar si necesita actualización
                        stored_mtime = self.file_store.get_file_modified_time(file_id)
                        
                        if stored_mtime and modified_time:
                            drive_mtime = datetime.fromisoformat(
                                modified_time.replace('Z', '+00:00')
                            )
                            
                            # Comparar sin zona horaria para evitar problemas
                            stored_naive = stored_mtime.replace(tzinfo=None) if stored_mtime.tzinfo else stored_mtime
                            drive_naive = drive_mtime.replace(tzinfo=None) if drive_mtime.tzinfo else drive_mtime
                            
                            if stored_naive >= drive_naive:
                                should_download = False
                                skipped_files.append(file_name)
                else:
                    # Verificar en filesystem
                    local_path = os.path.join(self.download_path, file_name)
                    
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
                    downloaded_id = self.download_file(file_id, file_name, modified_time)
                    
                    if downloaded_id == "TOO_LARGE":
                        # Archivo omitido por tamaño
                        too_large_files.append(file_name)
                    elif downloaded_id:
                        # Descargado exitosamente
                        downloaded_files.append({
                            "name": file_name,
                            "id": file_id,
                            "stored_id": downloaded_id,
                            "modified_time": modified_time,
                            "storage": "postgres" if self.use_postgres else "filesystem"
                        })
                    else:
                        # Error al descargar
                        errors.append(f"Error descargando {file_name}")
            
            result = {
                "success": True,
                "files_processed": len(files),
                "downloaded": len(downloaded_files),
                "skipped": len(skipped_files),
                "too_large": len(too_large_files),
                "errors": len(errors),
                "storage_type": "PostgreSQL" if self.use_postgres else "Filesystem",
                "downloaded_files": downloaded_files,
                "skipped_files": skipped_files,
                "too_large_files": too_large_files
            }
            
            if errors:
                result["error_details"] = errors
            
            # Log resumen con detalles
            logger.info(f"✅ Sincronización completada:")
            logger.info(f"   📥 {len(downloaded_files)} descargados")
            logger.info(f"   ⏭️  {len(skipped_files)} omitidos (ya existían)")
            if too_large_files:
                logger.warning(f"   ⚠️  {len(too_large_files)} muy grandes (>50MB)")
                logger.warning(f"   Archivos grandes omitidos: {', '.join(too_large_files[:5])}")
                if len(too_large_files) > 5:
                    logger.warning(f"   ... y {len(too_large_files) - 5} más")
            if errors:
                logger.error(f"   ❌ {len(errors)} errores")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en sincronización: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def upload_file(self, file_path: str, file_name: Optional[str] = None, folder_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Subir un archivo a Google Drive
        
        Args:
            file_path: Ruta local del archivo a subir
            file_name: Nombre para el archivo en Drive (usa el nombre local si no se especifica)
            folder_id: ID de la carpeta destino (usa la configurada por defecto si no se especifica)
        
        Returns:
            Información del archivo subido o None si falló
        """
        if not self.service:
            logger.error("Servicio de Google Drive no inicializado")
            return None
        
        if not os.path.exists(file_path):
            logger.error(f"Archivo no encontrado: {file_path}")
            return None
        
        try:
            target_folder = folder_id or self.folder_id
            upload_name = file_name or os.path.basename(file_path)
            
            # Determinar tipo MIME
            mime_types = {
                '.pdf': 'application/pdf',
                '.txt': 'text/plain',
                '.md': 'text/markdown',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            }
            
            file_ext = os.path.splitext(file_path)[1].lower()
            mime_type = mime_types.get(file_ext, 'application/octet-stream')
            
            # Metadatos del archivo
            file_metadata = {
                'name': upload_name,
                'parents': [target_folder]
            }
            
            # Crear media
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            
            # Subir archivo
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, mimeType, size, modifiedTime'
            ).execute()
            
            logger.info(f"✅ Archivo subido a Drive: {upload_name} (ID: {file.get('id')})")
            
            return file
            
        except HttpError as e:
            logger.error(f"❌ Error HTTP subiendo archivo: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error subiendo archivo: {e}")
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """
        Eliminar un archivo de Google Drive
        
        Args:
            file_id: ID del archivo a eliminar
        
        Returns:
            True si se eliminó correctamente
        """
        if not self.service:
            logger.error("Servicio de Google Drive no inicializado")
            return False
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"✅ Archivo eliminado de Drive: {file_id}")
            return True
            
        except HttpError as e:
            logger.error(f"❌ Error HTTP eliminando archivo: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error eliminando archivo: {e}")
            return False
    
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
            "supported_formats": self.supported_formats,
            "storage_type": "PostgreSQL" if self.use_postgres else "Filesystem"
        }
        
        if self.use_postgres:
            # Estadísticas de PostgreSQL
            stats = self.file_store.get_stats()
            status["storage_stats"] = stats
            status["files_count"] = stats.get("total_files", 0)
        else:
            # Estadísticas de filesystem
            if os.path.exists(self.download_path):
                local_files = os.listdir(self.download_path)
                status["local_files_count"] = len(local_files)
                status["local_files"] = local_files
            else:
                status["local_files_count"] = 0
                status["local_files"] = []
        
        return status