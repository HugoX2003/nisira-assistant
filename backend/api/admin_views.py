"""
Admin Views para el panel de administración
===========================================

Vistas especiales para el usuario administrador que permiten:
- Gestión de documentos de Google Drive
- Gestión de embeddings
- Visualización de logs y metadata
- Control del pipeline RAG
"""

import logging
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

# Importar managers del sistema RAG
try:
    from rag_system.drive_sync.drive_manager import GoogleDriveManager
    from rag_system.embeddings.embedding_manager import EmbeddingManager
    from rag_system.vector_store.chroma_manager import ChromaManager
    from rag_system.document_processing.pdf_processor import PDFProcessor
    from rag_system.document_processing.text_processor import TextProcessor
    RAG_MODULES_AVAILABLE = True
except ImportError as e:
    RAG_MODULES_AVAILABLE = False
    logger.warning(f"⚠️ Módulos RAG no disponibles: {e}")


def is_admin_user(user):
    """
    Verifica si el usuario es el administrador
    Usuario: admin
    Contraseña: admin123
    """
    return user and user.username == 'admin'


def admin_required(view_func):
    """
    Decorador para requerir permisos de administrador
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"error": "No autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not is_admin_user(request.user):
            return Response(
                {"error": "Permisos insuficientes. Solo administradores."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def calculate_file_hash(file_path: str) -> str:
    """
    Calcular hash MD5 de un archivo para identificación única
    
    Args:
        file_path: Ruta del archivo
    
    Returns:
        Hash MD5 del archivo
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"❌ Error calculando hash para {file_path}: {e}")
        return None


def check_file_already_processed(chroma_manager, file_hash: str, file_name: str) -> bool:
    """
    Verificar si un archivo ya fue procesado anteriormente
    
    Args:
        chroma_manager: Instancia de ChromaManager
        file_hash: Hash MD5 del archivo
        file_name: Nombre del archivo (fallback si no hay hash)
    
    Returns:
        True si el archivo ya fue procesado
    """
    if not chroma_manager.is_ready():
        return False
    
    try:
        # Buscar por hash primero (más confiable)
        if file_hash:
            results = chroma_manager.collection.get(
                where={"file_hash": file_hash},
                limit=1
            )
            if results and results['ids']:
                return True
        
        # Fallback: buscar por nombre de archivo
        results = chroma_manager.collection.get(
            where={"file_name": file_name},
            limit=1
        )
        return bool(results and results['ids'])
        
    except Exception as e:
        logger.warning(f"⚠️  Error verificando duplicados: {e}")
        return False


# ==========================================
# ENDPOINTS DE GOOGLE DRIVE
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@admin_required
def list_drive_files(request):
    """
    Listar archivos en Google Drive con paginación y búsqueda
    Query params:
    - page: número de página (default: 1)
    - pageSize: archivos por página (default: 20)
    - search: término de búsqueda (filtra por nombre)
    """
    if not RAG_MODULES_AVAILABLE:
        return Response(
            {"error": "Sistema RAG no disponible"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        # Obtener parámetros de paginación y búsqueda
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 20))
        search_query = request.GET.get('search', '').strip().lower()
        
        drive_manager = GoogleDriveManager()
        
        if not drive_manager.is_authenticated():
            return Response(
                {"error": "No autenticado con Google Drive"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Obtener todos los archivos
        all_files = drive_manager.list_files()
        
        # Formatear archivos
        formatted_files = []
        for file_info in all_files:
            formatted_files.append({
                "id": file_info.get('id'),
                "name": file_info.get('name'),
                "mimeType": file_info.get('mimeType'),
                "size": file_info.get('size', 0),
                "modifiedTime": file_info.get('modifiedTime'),
                "parents": file_info.get('parents', [])
            })
        
        # Filtrar por búsqueda si hay término
        if search_query:
            formatted_files = [
                f for f in formatted_files 
                if search_query in f['name'].lower()
            ]
        
        # Calcular paginación
        total_files = len(formatted_files)
        total_pages = (total_files + page_size - 1) // page_size  # Redondeo hacia arriba
        
        # Validar página
        if page < 1:
            page = 1
        if page > total_pages and total_pages > 0:
            page = total_pages
        
        # Obtener archivos de la página actual
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_files = formatted_files[start_idx:end_idx]
        
        return Response({
            "success": True,
            "files": paginated_files,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "totalFiles": total_files,
                "totalPages": total_pages,
                "hasNextPage": page < total_pages,
                "hasPrevPage": page > 1
            }
        })
        
    except Exception as e:
        logger.error(f"Error listando archivos de Drive: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@admin_required
def upload_to_drive(request):
    """
    Subir un archivo a Google Drive
    Solo acepta PDFs y archivos de texto
    """
    logger.info(f"📤 Upload request recibido de usuario: {request.user.username}")
    
    if not RAG_MODULES_AVAILABLE:
        return Response(
            {"error": "Sistema RAG no disponible"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        # Validar archivo
        if 'file' not in request.FILES:
            logger.error("❌ No se proporcionó archivo en la petición")
            return Response(
                {"error": "No se proporcionó ningún archivo"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name
        logger.info(f"📁 Archivo recibido: {file_name}, tamaño: {uploaded_file.size} bytes")
        
        # Validar tipo de archivo
        allowed_extensions = ['.pdf', '.txt', '.md', '.doc', '.docx']
        file_ext = os.path.splitext(file_name)[1].lower()
        
        if file_ext not in allowed_extensions:
            return Response(
                {"error": f"Tipo de archivo no permitido. Solo: {', '.join(allowed_extensions)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Guardar temporalmente
        temp_path = os.path.join(settings.BASE_DIR, 'data', 'temp', file_name)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        
        with open(temp_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        # Subir a Google Drive
        drive_manager = GoogleDriveManager()
        
        if not drive_manager.is_authenticated():
            # Si no está autenticado con Drive, guardar solo localmente
            final_path = os.path.join(settings.BASE_DIR, 'data', 'documents', file_name)
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            
            import shutil
            shutil.move(temp_path, final_path)
            
            logger.warning(f"⚠️ Drive no autenticado. Archivo guardado solo localmente: {file_name}")
            
            return Response({
                "success": True,
                "message": f"Archivo '{file_name}' guardado localmente (Drive no disponible)",
                "file_name": file_name,
                "file_path": final_path,
                "drive_uploaded": False
            })
        
        # Subir a Drive
        result = drive_manager.upload_file(temp_path, file_name)
        
        if result:
            # También guardar localmente
            final_path = os.path.join(settings.BASE_DIR, 'data', 'documents', file_name)
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            
            import shutil
            shutil.copy(temp_path, final_path)
            
            # Eliminar archivo temporal
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            logger.info(f"✅ Archivo subido a Drive y guardado localmente: {file_name}")
            
            return Response({
                "success": True,
                "message": f"Archivo '{file_name}' subido correctamente a Drive",
                "file_name": file_name,
                "file_id": result.get('id'),
                "file_path": final_path,
                "drive_uploaded": True
            })
        else:
            # Si falla la subida a Drive, guardar solo localmente
            final_path = os.path.join(settings.BASE_DIR, 'data', 'documents', file_name)
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            
            import shutil
            shutil.move(temp_path, final_path)
            
            logger.error(f"❌ Error subiendo a Drive. Archivo guardado localmente: {file_name}")
            
            return Response({
                "success": True,
                "message": f"Archivo '{file_name}' guardado localmente (error subiendo a Drive)",
                "file_name": file_name,
                "file_path": final_path,
                "drive_uploaded": False
            })
        
    except Exception as e:
        logger.error(f"Error subiendo archivo: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@admin_required
def delete_drive_file(request, file_id):
    """
    Eliminar un archivo de Google Drive
    """
    logger.info(f"🗑️ Delete request recibido de usuario: {request.user.username} para file_id: {file_id}")
    
    if not RAG_MODULES_AVAILABLE:
        return Response(
            {"error": "Sistema RAG no disponible"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        drive_manager = GoogleDriveManager()
        
        if not drive_manager.is_authenticated():
            logger.error("❌ Drive no autenticado")
            return Response(
                {"error": "No autenticado con Google Drive"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Eliminar de Google Drive
        logger.info(f"🔄 Intentando eliminar archivo {file_id} de Drive...")
        success = drive_manager.delete_file(file_id)
        
        if success:
            logger.info(f"✅ Archivo {file_id} eliminado de Drive")
            
            return Response({
                "success": True,
                "message": f"Archivo eliminado correctamente"
            })
        else:
            return Response(
                {"error": "Error eliminando archivo de Drive"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except Exception as e:
        logger.error(f"Error eliminando archivo: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@admin_required
def sync_drive_documents(request):
    """
    Sincronizar documentos de Google Drive
    """
    if not RAG_MODULES_AVAILABLE:
        return Response(
            {"error": "Sistema RAG no disponible"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        drive_manager = GoogleDriveManager()
        result = drive_manager.sync_documents()
        
        return Response({
            "success": result.get('success', False),
            "data": result
        })
        
    except Exception as e:
        logger.error(f"Error sincronizando documentos: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==========================================
# ENDPOINTS DE EMBEDDINGS
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@admin_required
def get_embeddings_status(request):
    """
    Obtener estado actual de los embeddings
    """
    if not RAG_MODULES_AVAILABLE:
        return Response(
            {"error": "Sistema RAG no disponible"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        chroma_manager = ChromaManager()
        
        # Obtener colecciones
        collections = chroma_manager.list_collections()
        
        total_documents = 0
        collections_info = []
        
        for collection_name in collections:
            try:
                count = chroma_manager.get_collection_count(collection_name)
                total_documents += count
                collections_info.append({
                    "name": collection_name,
                    "document_count": count
                })
            except Exception as e:
                logger.warning(f"Error obteniendo info de colección {collection_name}: {e}")
        
        return Response({
            "success": True,
            "total_collections": len(collections),
            "total_documents": total_documents,
            "collections": collections_info
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de embeddings: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _save_progress(progress_data):
    """Guardar progreso en archivo temporal"""
    try:
        progress_file = os.path.join(settings.BASE_DIR, 'data', 'temp', 'embedding_progress.json')
        os.makedirs(os.path.dirname(progress_file), exist_ok=True)
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f)
    except Exception as e:
        logger.error(f"Error guardando progreso: {e}")

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@admin_required
def get_embedding_progress(request):
    """Obtener progreso de generación de embeddings"""
    try:
        progress_file = os.path.join(settings.BASE_DIR, 'data', 'temp', 'embedding_progress.json')
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        # Archivo vacío, es normal al inicio
                        return Response({
                            "status": "idle",
                            "total": 0,
                            "current": 0,
                            "current_file": "",
                            "processed": 0,
                            "errors": 0,
                            "logs": []
                        })
                    progress = json.loads(content)
                return Response(progress)
            except json.JSONDecodeError as e:
                # Archivo corrupto o mal formado
                logger.warning(f"Archivo de progreso mal formado: {e}")
                return Response({
                    "status": "idle",
                    "total": 0,
                    "current": 0,
                    "current_file": "",
                    "processed": 0,
                    "errors": 0,
                    "logs": []
                })
            except Exception as e:
                logger.error(f"Error leyendo archivo de progreso: {e}")
                return Response({
                    "status": "idle",
                    "total": 0,
                    "current": 0,
                    "current_file": "",
                    "processed": 0,
                    "errors": 0,
                    "logs": []
                })
        else:
            return Response({
                "status": "idle",
                "total": 0,
                "current": 0,
                "current_file": "",
                "processed": 0,
                "errors": 0,
                "logs": []
            })
    except Exception as e:
        logger.error(f"Error general en get_embedding_progress: {e}", exc_info=True)
        return Response(
            {
                "status": "error",
                "error": str(e),
                "total": 0,
                "current": 0,
                "current_file": "",
                "processed": 0,
                "errors": 0,
                "logs": []
            },
            status=status.HTTP_200_OK  # Cambiado a 200 para evitar errores en frontend
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@admin_required
def generate_embeddings(request):
    """
    Generar embeddings para documentos nuevos
    Verifica duplicados antes de generar
    """
    if not RAG_MODULES_AVAILABLE:
        return Response(
            {"error": "Sistema RAG no disponible"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        # Obtener documentos del directorio
        documents_path = os.path.join(settings.BASE_DIR, 'data', 'documents')
        
        if not os.path.exists(documents_path):
            return Response(
                {"error": "Directorio de documentos no existe"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Listar archivos
        files = os.listdir(documents_path)
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        txt_files = [f for f in files if f.lower().endswith(('.txt', '.md'))]
        
        processed_files = []
        skipped_files = []
        errors = []
        
        chroma_manager = ChromaManager()
        embedding_manager = EmbeddingManager()
        pdf_processor = PDFProcessor()
        text_processor = TextProcessor()
        
        total_files = len(pdf_files) + len(txt_files)
        logger.info(f"🚀 INICIANDO GENERACIÓN DE EMBEDDINGS: {total_files} archivos totales ({len(pdf_files)} PDFs, {len(txt_files)} TXTs)")
        
        # Inicializar progreso
        progress = {
            "status": "running",
            "total": total_files,
            "current": 0,
            "current_file": "",
            "processed": 0,
            "errors": 0,
            "logs": []
        }
        _save_progress(progress)
        
        # Procesar PDFs
        for idx, pdf_file in enumerate(pdf_files, 1):
            try:
                progress["current"] = idx
                progress["current_file"] = pdf_file
                progress["logs"].append(f"📄 [{idx}/{total_files}] Procesando: {pdf_file}")
                _save_progress(progress)
                
                logger.info(f"📄 [{idx}/{len(pdf_files)}] Procesando PDF: {pdf_file}")
                file_path = os.path.join(documents_path, pdf_file)
                
                # Calcular hash del archivo
                file_hash = calculate_file_hash(file_path)
                
                # Verificar si ya fue procesado
                if check_file_already_processed(chroma_manager, file_hash, pdf_file):
                    logger.info(f"   ⏭️  Archivo ya procesado anteriormente, saltando: {pdf_file}")
                    progress["logs"].append(f"   ⏭️  Ya existe en embeddings, saltando")
                    _save_progress(progress)
                    skipped_files.append(pdf_file)
                    continue
                
                # Procesar PDF
                logger.info(f"   🔍 Extrayendo texto del PDF...")
                result = pdf_processor.process_pdf(file_path)
                
                if result.get('success') and result.get('chunks'):
                    chunks = result['chunks']
                    logger.info(f"   ✂️  {len(chunks)} chunks extraídos")
                    # Preparar textos y metadatas
                    texts = []
                    metadatas = []
                    
                    for chunk in chunks:
                        # Metadata base con hash para deduplicación
                        base_metadata = {
                            "source": pdf_file, 
                            "type": "pdf", 
                            "file_name": pdf_file,
                            "file_hash": file_hash  # Agregar hash para identificación única
                        }
                        
                        # Si chunk es un string, usarlo directamente
                        if isinstance(chunk, str):
                            texts.append(chunk)
                            metadatas.append(base_metadata)
                        # Si chunk es un dict, extraer texto y metadata
                        elif isinstance(chunk, dict):
                            texts.append(chunk.get('text', str(chunk)))
                            meta = chunk.get('metadata', {})
                            if not isinstance(meta, dict):
                                meta = {}
                            # Combinar metadata existente con base_metadata
                            meta.update(base_metadata)
                            metadatas.append(meta)
                        else:
                            # Convertir a string si es otro tipo
                            texts.append(str(chunk))
                            metadatas.append(base_metadata)
                    
                    # Generar embeddings
                    logger.info(f"   🧠 Generando embeddings para {len(texts)} chunks...")
                    embeddings = embedding_manager.create_embeddings_batch(texts)
                    logger.info(f"   ✅ Embeddings generados exitosamente")
                    
                    # Preparar documentos para ChromaDB
                    logger.info(f"   💾 Guardando en ChromaDB...")
                    documents = []
                    for text, metadata in zip(texts, metadatas):
                        documents.append({
                            'text': text,
                            'metadata': metadata
                        })
                    
                    # Agregar a ChromaDB
                    chroma_manager.add_documents(
                        documents=documents,
                        embeddings=embeddings
                    )
                    
                    logger.info(f"   ✅ PDF '{pdf_file}' procesado completamente ({len(chunks)} chunks)")
                    progress["processed"] += 1
                    progress["logs"].append(f"   ✅ Completado: {len(chunks)} chunks")
                    _save_progress(progress)
                    
                    processed_files.append({
                        "name": pdf_file,
                        "chunks": len(chunks),
                        "type": "pdf"
                    })
                else:
                    logger.warning(f"   ⚠️  No se extrajeron chunks del PDF '{pdf_file}'")
                    skipped_files.append(pdf_file)
                    
            except Exception as e:
                logger.error(f"   ❌ ERROR procesando {pdf_file}: {e}")
                progress["errors"] += 1
                progress["logs"].append(f"   ❌ Error: {str(e)[:100]}")
                _save_progress(progress)
                errors.append({"file": pdf_file, "error": str(e)})
        
        logger.info(f"📝 PDFs completados. Procesando archivos de texto...")
        
        # Procesar archivos de texto
        for idx, txt_file in enumerate(txt_files, 1):
            try:
                current_file_idx = len(pdf_files) + idx
                progress["current"] = current_file_idx
                progress["current_file"] = txt_file
                progress["logs"].append(f"📝 [{current_file_idx}/{total_files}] Procesando: {txt_file}")
                _save_progress(progress)
                
                logger.info(f"📝 [{idx}/{len(txt_files)}] Procesando TXT: {txt_file}")
                file_path = os.path.join(documents_path, txt_file)
                
                # Calcular hash del archivo
                file_hash = calculate_file_hash(file_path)
                
                # Verificar si ya fue procesado
                if check_file_already_processed(chroma_manager, file_hash, txt_file):
                    logger.info(f"   ⏭️  Archivo ya procesado anteriormente, saltando: {txt_file}")
                    progress["logs"].append(f"   ⏭️  Ya existe en embeddings, saltando")
                    _save_progress(progress)
                    skipped_files.append(txt_file)
                    continue
                
                # Procesar texto
                logger.info(f"   🔍 Extrayendo texto...")
                chunks = text_processor.process_text_file(file_path)
                
                if chunks:
                    logger.info(f"   ✂️  {len(chunks)} chunks extraídos")
                    # Preparar textos y metadatas
                    texts = []
                    metadatas = []
                    
                    for chunk in chunks:
                        # Metadata base con hash para deduplicación
                        base_metadata = {
                            "source": txt_file, 
                            "type": "text", 
                            "file_name": txt_file,
                            "file_hash": file_hash  # Agregar hash para identificación única
                        }
                        
                        # Si chunk es un string, usarlo directamente
                        if isinstance(chunk, str):
                            texts.append(chunk)
                            metadatas.append(base_metadata)
                        # Si chunk es un dict, extraer texto y metadata
                        elif isinstance(chunk, dict):
                            texts.append(chunk.get('text', str(chunk)))
                            meta = chunk.get('metadata', {})
                            if not isinstance(meta, dict):
                                meta = {}
                            # Combinar metadata existente con base_metadata
                            meta.update(base_metadata)
                            metadatas.append(meta)
                        else:
                            # Convertir a string si es otro tipo
                            texts.append(str(chunk))
                            metadatas.append(base_metadata)
                    
                    # Generar embeddings
                    logger.info(f"   🧠 Generando embeddings para {len(texts)} chunks...")
                    embeddings = embedding_manager.create_embeddings_batch(texts)
                    logger.info(f"   ✅ Embeddings generados exitosamente")
                    
                    # Preparar documentos para ChromaDB
                    logger.info(f"   💾 Guardando en ChromaDB...")
                    documents = []
                    for text, metadata in zip(texts, metadatas):
                        documents.append({
                            'text': text,
                            'metadata': metadata
                        })
                    
                    chroma_manager.add_documents(
                        documents=documents,
                        embeddings=embeddings
                    )
                    
                    logger.info(f"   ✅ TXT '{txt_file}' procesado completamente ({len(chunks)} chunks)")
                    progress["processed"] += 1
                    progress["logs"].append(f"   ✅ Completado: {len(chunks)} chunks")
                    _save_progress(progress)
                    
                    processed_files.append({
                        "name": txt_file,
                        "chunks": len(chunks),
                        "type": "text"
                    })
                else:
                    logger.warning(f"   ⚠️  No se extrajeron chunks del TXT '{txt_file}'")
                    skipped_files.append(txt_file)
                    
            except Exception as e:
                logger.error(f"   ❌ ERROR procesando {txt_file}: {e}")
                progress["errors"] += 1
                progress["logs"].append(f"   ❌ Error: {str(e)[:100]}")
                _save_progress(progress)
                errors.append({"file": txt_file, "error": str(e)})
        
        logger.info(f"🎉 PROCESO COMPLETADO!")
        logger.info(f"   ✅ Procesados: {len(processed_files)}")
        logger.info(f"   ⏭️  Omitidos (duplicados): {len(skipped_files)}")
        logger.info(f"   ❌ Errores: {len(errors)}")
        
        # Finalizar progreso
        progress["status"] = "completed"
        progress["logs"].append(f"🎉 Completado: {len(processed_files)} nuevos, {len(skipped_files)} ya existían, {len(errors)} errores")
        _save_progress(progress)
        
        return Response({
            "success": True,
            "processed": len(processed_files),
            "skipped": len(skipped_files),
            "errors": len(errors),
            "processed_files": processed_files,
            "skipped_files": skipped_files,
            "error_details": errors,
            "message": f"✅ {len(processed_files)} archivos nuevos procesados. {len(skipped_files)} ya existían (omitidos)."
        })
        
    except Exception as e:
        logger.error(f"Error generando embeddings: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@admin_required
def verify_embeddings(request):
    """
    Verificar estado de embeddings y detectar duplicados
    """
    if not RAG_MODULES_AVAILABLE:
        return Response(
            {"error": "Sistema RAG no disponible"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        chroma_manager = ChromaManager()
        
        # Obtener todos los documentos
        collections = chroma_manager.list_collections()
        
        verification_results = []
        
        for collection_name in collections:
            try:
                # Obtener metadatos de la colección
                collection_info = {
                    "collection": collection_name,
                    "document_count": chroma_manager.get_collection_count(collection_name),
                    "status": "OK"
                }
                
                # TODO: Implementar detección de duplicados
                # Usar hashes de contenido para detectar duplicados
                
                verification_results.append(collection_info)
                
            except Exception as e:
                verification_results.append({
                    "collection": collection_name,
                    "status": "ERROR",
                    "error": str(e)
                })
        
        return Response({
            "success": True,
            "collections_verified": len(verification_results),
            "results": verification_results
        })
        
    except Exception as e:
        logger.error(f"Error verificando embeddings: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@admin_required
def clear_embeddings(request):
    """
    Limpiar/eliminar todos los embeddings de ChromaDB
    ADVERTENCIA: Esta acción eliminará todas las colecciones y embeddings
    """
    if not RAG_MODULES_AVAILABLE:
        return Response(
            {"error": "Sistema RAG no disponible"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        chroma_manager = ChromaManager()
        
        # Obtener todas las colecciones
        collections = chroma_manager.list_collections()
        
        if not collections:
            return Response({
                "success": True,
                "message": "No hay embeddings para limpiar",
                "collections_deleted": 0
            })
        
        deleted_collections = []
        errors = []
        
        # Eliminar cada colección usando el cliente directo
        for collection_name in collections:
            try:
                # Usar el cliente de ChromaDB directamente
                chroma_manager.client.delete_collection(name=collection_name)
                deleted_collections.append(collection_name)
                logger.info(f"✅ Colección '{collection_name}' eliminada")
            except Exception as e:
                error_msg = f"Error eliminando '{collection_name}': {str(e)}"
                errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        response_data = {
            "success": len(errors) == 0,
            "message": f"Limpieza completada. {len(deleted_collections)} colecciones eliminadas.",
            "collections_deleted": len(deleted_collections),
            "deleted": deleted_collections
        }
        
        if errors:
            response_data["errors"] = errors
            response_data["message"] += f" {len(errors)} errores encontrados."
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error limpiando embeddings: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==========================================
# ENDPOINTS DE LOGS Y METADATA
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@admin_required
def get_system_logs(request):
    """
    Obtener logs del sistema
    """
    try:
        # Intentar leer logs de Django (últimas 100 líneas)
        logs_data = []
        
        # Buscar archivos de log comunes
        possible_log_paths = [
            os.path.join(settings.BASE_DIR, 'logs', 'app.log'),
            os.path.join(settings.BASE_DIR, 'logs', 'django.log'),
            os.path.join(settings.BASE_DIR, 'app.log'),
        ]
        
        log_file_found = None
        for log_path in possible_log_paths:
            if os.path.exists(log_path):
                log_file_found = log_path
                break
        
        if log_file_found:
            try:
                with open(log_file_found, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    last_lines = lines[-100:] if len(lines) > 100 else lines
                    logs_data = [line.strip() for line in last_lines if line.strip()]
                    
                return Response({
                    "success": True,
                    "logs": logs_data,
                    "total_lines": len(lines),
                    "log_file": log_file_found
                })
            except Exception as e:
                logger.error(f"Error leyendo archivo de log: {e}")
        
        # Si no hay archivo de logs, retornar mensaje con instrucciones
        return Response({
            "success": True,
            "logs": [
                "📍 UBICACIÓN DE LOS LOGS:",
                "",
                "Los logs del sistema se muestran en la CONSOLA DEL SERVIDOR.",
                "",
                "👉 Para ver los logs:",
                "   1. Ve a la terminal donde ejecutaste 'python manage.py runserver'",
                "   2. Los logs aparecen en tiempo real ahí",
                "   3. Busca líneas con emojis como 🚀 📄 🧠 ✅ ❌",
                "",
                "💡 Los logs incluyen:",
                "   • Inicio del proceso (🚀)",
                "   • Progreso por archivo ([1/400])",
                "   • Extracción de texto (🔍)",
                "   • Generación de embeddings (🧠)",
                "   • Errores si ocurren (❌)",
                "",
                "🔧 Para guardar logs en archivo, configura LOGGING en settings.py"
            ],
            "message": "Logs disponibles en consola del servidor"
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo logs: {e}")
        return Response({
            "success": False,
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@admin_required
def get_metadata_info(request):
    """
    Obtener información de metadata del sistema
    """
    try:
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "base_dir": str(settings.BASE_DIR),
                "debug_mode": settings.DEBUG,
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
            },
            "storage": {
                "documents_path": str(os.path.join(settings.BASE_DIR, 'data', 'documents')),
                "chroma_path": str(os.path.join(settings.BASE_DIR, 'chroma_db')),
            }
        }
        
        # Información de documentos
        documents_path = metadata["storage"]["documents_path"]
        if os.path.exists(documents_path):
            try:
                files = [f for f in os.listdir(documents_path) if os.path.isfile(os.path.join(documents_path, f))]
                metadata["documents"] = {
                    "total": len(files),
                    "sample_files": files[:10] if len(files) > 10 else files  # Primeros 10
                }
            except Exception as e:
                metadata["documents"] = {"error": str(e)}
        else:
            metadata["documents"] = {"total": 0, "message": "Carpeta no existe"}
        
        # Información de ChromaDB
        if RAG_MODULES_AVAILABLE:
            try:
                chroma_manager = ChromaManager()
                collections_info = chroma_manager.list_collections()
                
                # Obtener detalles de cada colección
                collections_details = []
                for coll_name in collections_info:
                    try:
                        collection = chroma_manager.get_collection(coll_name)
                        count = collection.count() if collection else 0
                        collections_details.append({
                            "name": coll_name,
                            "count": count
                        })
                    except:
                        collections_details.append({
                            "name": coll_name,
                            "count": "N/A"
                        })
                
                metadata["embeddings"] = {
                    "collections": collections_details,
                    "total_collections": len(collections_info)
                }
            except Exception as e:
                logger.error(f"Error obteniendo info de ChromaDB: {e}")
                metadata["embeddings"] = {"error": str(e), "message": "Error accediendo a ChromaDB"}
        else:
            metadata["embeddings"] = {"message": "Módulos RAG no disponibles"}
        
        return Response({
            "success": True,
            "metadata": metadata
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo metadata: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@admin_required
def get_pipeline_status(request):
    """
    Obtener estado del pipeline RAG
    """
    if not RAG_MODULES_AVAILABLE:
        return Response({
            "success": False,
            "status": "unavailable",
            "message": "Sistema RAG no disponible"
        })
    
    try:
        status_info = {
            "drive_sync": False,
            "embeddings": False,
            "vector_store": False,
            "pipeline": False
        }
        
        # Verificar Google Drive
        try:
            drive_manager = GoogleDriveManager()
            status_info["drive_sync"] = drive_manager.is_authenticated()
        except Exception as e:
            logger.warning(f"Drive sync no disponible: {e}")
        
        # Verificar Embeddings
        try:
            embedding_manager = EmbeddingManager()
            status_info["embeddings"] = True
        except Exception as e:
            logger.warning(f"Embeddings no disponibles: {e}")
        
        # Verificar Vector Store
        try:
            chroma_manager = ChromaManager()
            collections = chroma_manager.list_collections()
            status_info["vector_store"] = len(collections) > 0
        except Exception as e:
            logger.warning(f"Vector store no disponible: {e}")
        
        # Estado general del pipeline
        status_info["pipeline"] = all([
            status_info["embeddings"],
            status_info["vector_store"]
        ])
        
        return Response({
            "success": True,
            "status": status_info,
            "overall": "operational" if status_info["pipeline"] else "degraded"
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del pipeline: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@admin_required
def get_system_metrics(request):
    """
    Obtener métricas REALES del sistema RAG para análisis de tesis
    
    3 MÉTRICAS FINALES:
    1. Latencia Total: Tiempo de respuesta promedio (segundos)
    2. Reducción de Tiempo: Velocidad de procesamiento (tokens/segundo)
    3. Calidad de Respuesta: Score RAGAS compuesto (0-1)
       - Faithfulness: Fidelidad al contexto
       - Answer Relevancy: Relevancia de la respuesta
       - Context Precision: Precisión de recuperación
    """
    try:
        # Importar función de métricas agregadas
        from .metrics_tracker import get_aggregated_metrics
        
        # Obtener métricas reales de la base de datos (SOLO 3 MÉTRICAS)
        metrics_data = get_aggregated_metrics()
        
        # Estructura simplificada con las 3 métricas
        response_data = {
            "latenciaTotal": metrics_data.get("tiempoRespuesta", 0),  # Tiempo promedio en segundos
            "reduccionTiempo": metrics_data.get("velocidadProcesamiento", 0),  # Tokens/segundo
            "calidadRespuesta": metrics_data.get("calidadRespuesta", 0),  # Score RAGAS 0-1
            "totalQueries": metrics_data.get("totalQueries", 0),
            "metadata": {
                "lastUpdated": datetime.now().isoformat(),
                "dataSource": "real_database_ragas_gemini",
                "isRealData": True,
                "description": "3 métricas finales: Latencia Total, Reducción de Tiempo, Calidad de Respuesta (RAGAS con Gemini)"
            }
        }
        
        logger.info(f"📊 Métricas obtenidas: {metrics_data.get('totalQueries', 0)} consultas registradas")
        
        return Response({
            "success": True,
            "metrics": response_data,
            "message": f"Métricas reales obtenidas: {metrics_data.get('totalQueries', 0)} consultas"
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo métricas: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@admin_required
def get_query_list(request):
    """
    Obtener lista de consultas individuales con sus métricas
    
    Query params:
    - page: número de página (default: 1)
    - page_size: consultas por página (default: 20)
    - complex_only: filtrar solo consultas complejas (default: false)
    """
    try:
        from .models import QueryMetrics, RAGASMetrics
        from django.core.paginator import Paginator
        
        # Parámetros de paginación
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        complex_only = request.GET.get('complex_only', 'false').lower() == 'true'
        
        # Consultar base de datos
        queries = QueryMetrics.objects.all().order_by('-created_at')
        
        # Filtrar consultas complejas si se solicita
        if complex_only:
            queries = queries.filter(is_complex_query=True)
        
        # Paginar
        paginator = Paginator(queries, page_size)
        page_obj = paginator.get_page(page)
        
        # Construir lista de consultas con métricas
        queries_list = []
        for query_metric in page_obj:
            # Buscar métricas de precisión asociadas
            precision_metrics = None
            try:
                ragas_metric = RAGASMetrics.objects.filter(query_metrics=query_metric).first()
                if ragas_metric:
                    precision_metrics = {
                        'precision_at_k': ragas_metric.precision_at_k,
                        'recall_at_k': ragas_metric.recall_at_k,
                        'faithfulness': ragas_metric.faithfulness_score,
                        'hallucination_rate': ragas_metric.hallucination_rate,
                        'answer_relevancy': ragas_metric.answer_relevancy,
                        'wer': ragas_metric.wer_score
                    }
            except:
                pass
            
            queries_list.append({
                'query_id': query_metric.query_id,
                'query_text': query_metric.query_text[:200] if query_metric.query_text else '',
                'timestamp': query_metric.created_at.isoformat(),
                'is_complex': query_metric.is_complex_query or False,
                'complexity_score': query_metric.query_complexity_score or 0.0,
                'performance': {
                    'total_latency': query_metric.total_latency or 0.0,
                    'time_to_first_token': query_metric.time_to_first_token or 0.0,
                    'retrieval_time': query_metric.retrieval_time or 0.0,
                    'generation_time': query_metric.generation_time or 0.0,
                    'documents_retrieved': query_metric.documents_retrieved or 0
                },
                'precision': precision_metrics
            })
        
        return Response({
            'success': True,
            'queries': queries_list,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_queries': paginator.count,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo lista de consultas: {e}", exc_info=True)
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@admin_required
def get_query_detail(request, query_id):
    """
    Obtener detalles completos de una consulta específica incluyendo
    cómo se calculó cada métrica
    """
    try:
        from .models import QueryMetrics, RAGASMetrics
        
        # Buscar query_metrics
        try:
            query_metric = QueryMetrics.objects.get(query_id=query_id)
        except QueryMetrics.DoesNotExist:
            return Response(
                {"error": "Consulta no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Buscar métricas de precisión
        ragas_metric = RAGASMetrics.objects.filter(query_metrics=query_metric).first()
        
        # SOLO 4 MÉTRICAS PRINCIPALES
        response_data = {
            'query_id': query_metric.query_id,
            'query_text': query_metric.query_text or '',
            'timestamp': query_metric.created_at.isoformat(),
            'top_k_used': query_metric.top_k or 5,
            
            # MÉTRICA 1: TIEMPO DE RESPUESTA
            'tiempo_respuesta': {
                'valor': query_metric.total_latency or 0.0,
                'unidad': 'segundos',
                'metodo': 'time.time() de Python',
                'formula': 'end_time - start_time',
                'calculo_detallado': {
                    'descripcion': 'Se toma el timestamp al inicio de la consulta y al final de la respuesta completa',
                    'codigo_usado': 'start_time = time.time(); ... ; end_time = time.time(); response_time = end_time - start_time',
                    'valor_final': f'{query_metric.total_latency:.4f} segundos'
                }
            }
        }
        
        # Calcular velocidad de procesamiento si tenemos respuesta
        if ragas_metric and ragas_metric.response_text:
            tokens_generados = len(ragas_metric.response_text.split())
            velocidad = tokens_generados / query_metric.total_latency if query_metric.total_latency > 0 else 0
            
            # MÉTRICA 2: VELOCIDAD DE PROCESAMIENTO
            response_data['velocidad_procesamiento'] = {
                'valor': velocidad,
                'unidad': 'tokens/segundo',
                'metodo': 'len(respuesta.split()) / tiempo_total',
                'formula': 'tokens_generados / tiempo_respuesta',
                'calculo_detallado': {
                    'descripcion': 'Se cuenta el número de tokens (palabras) en la respuesta y se divide por el tiempo total',
                    'tokens_generados': tokens_generados,
                    'tiempo_total': query_metric.total_latency,
                    'operacion': f'{tokens_generados} tokens / {query_metric.total_latency:.4f} segundos = {velocidad:.2f} tokens/s',
                    'valor_final': f'{velocidad:.2f} tokens/segundo'
                }
            }
        
        # Agregar Precision y Recall si existen
        if ragas_metric:
            k_value = query_metric.top_k or 5
            docs_relevantes = int(ragas_metric.precision_at_k * k_value)
            contextos_usados = int(ragas_metric.recall_at_k * k_value)
            
            # MÉTRICA 3: ÍNDICE DE PRECISIÓN
            response_data['precision'] = {
                'valor': ragas_metric.precision_at_k,
                'porcentaje': f"{ragas_metric.precision_at_k * 100:.2f}%",
                'unidad': 'proporción (0-1)',
                'metodo': 'Jaccard Similarity',
                'formula': 'documentos_relevantes / k',
                'threshold': '0.08 (8% de overlap mínimo)',
                'calculo_detallado': {
                    'descripcion': 'Se calcula Jaccard Similarity entre palabras de la respuesta y cada documento. Si similarity > 0.20, el documento es relevante.',
                    'k_value': k_value,
                    'documentos_relevantes': docs_relevantes,
                    'documentos_irrelevantes': k_value - docs_relevantes,
                    'operacion': f'{docs_relevantes} documentos relevantes / {k_value} documentos totales = {ragas_metric.precision_at_k:.4f}',
                    'valor_final': f'{ragas_metric.precision_at_k:.4f} ({ragas_metric.precision_at_k * 100:.2f}%)',
                    'interpretacion': f'De {k_value} documentos recuperados, {docs_relevantes} fueron realmente útiles para responder'
                }
            }
            
            # MÉTRICA 4: ÍNDICE DE EXHAUSTIVIDAD
            response_data['recall'] = {
                'valor': ragas_metric.recall_at_k,
                'porcentaje': f"{ragas_metric.recall_at_k * 100:.2f}%",
                'unidad': 'proporción (0-1)',
                'metodo': 'Detección de n-gramas',
                'formula': 'contextos_usados / k',
                'ngram_size': '3 palabras',
                'calculo_detallado': {
                    'descripcion': 'Se extraen frases de 3 palabras (n-gramas) de cada documento. Si al menos 1 frase aparece en la respuesta, el contexto fue usado.',
                    'k_value': k_value,
                    'contextos_usados': contextos_usados,
                    'contextos_no_usados': k_value - contextos_usados,
                    'operacion': f'{contextos_usados} contextos usados / {k_value} contextos totales = {ragas_metric.recall_at_k:.4f}',
                    'valor_final': f'{ragas_metric.recall_at_k:.4f} ({ragas_metric.recall_at_k * 100:.2f}%)',
                    'interpretacion': f'La respuesta utilizó información de {contextos_usados} de {k_value} documentos recuperados'
                }
            }
            

        
        return Response({
            'success': True,
            'query': response_data
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo detalle de consulta: {e}", exc_info=True)
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Funciones auxiliares para explicaciones
def _explain_complexity(query_metric):
    score = query_metric.query_complexity_score
    length = len(query_metric.query_text)
    
    factors = []
    if length > 100:
        factors.append(f"Longitud alta ({length} caracteres)")
    if '?' in query_metric.query_text and query_metric.query_text.count('?') > 1:
        factors.append("Múltiples preguntas")
    
    complex_keywords = ['comparar', 'diferencia', 'analizar', 'explicar detalladamente', 'por qué', 'cómo funciona']
    found_keywords = [kw for kw in complex_keywords if kw in query_metric.query_text.lower()]
    if found_keywords:
        factors.append(f"Palabras clave complejas: {', '.join(found_keywords)}")
    
    if query_metric.is_complex_query:
        return f"Consulta compleja (score: {score:.2f}). Factores: {'; '.join(factors) if factors else 'Múltiples criterios'}"
    else:
        return f"Consulta simple (score: {score:.2f})"


def _explain_faithfulness(score):
    if score >= 0.9:
        return "Excelente - Respuesta fuertemente respaldada por contexto"
    elif score >= 0.7:
        return "Bueno - Mayor parte de la respuesta tiene soporte en contexto"
    elif score >= 0.5:
        return "Regular - Algunos datos pueden no estar respaldados"
    else:
        return "Bajo - Respuesta contiene mucha información sin respaldo"


def _explain_hallucination(rate):
    if rate <= 0.1:
        return "Excelente - Casi sin información inventada"
    elif rate <= 0.3:
        return "Aceptable - Poca información inventada"
    elif rate <= 0.5:
        return "Preocupante - Cantidad considerable de información inventada"
    else:
        return "Crítico - Alta tasa de información sin respaldo"


def _get_hallucination_severity(rate):
    if rate <= 0.1:
        return "low"
    elif rate <= 0.3:
        return "medium"
    else:
        return "high"


def _explain_relevancy(score):
    if score >= 0.8:
        return "Muy relevante - Respuesta aborda completamente la pregunta"
    elif score >= 0.6:
        return "Relevante - Respuesta relacionada con la pregunta"
    elif score >= 0.4:
        return "Parcialmente relevante - Algunos aspectos de la pregunta cubiertos"
    else:
        return "Poco relevante - Respuesta no aborda bien la pregunta"


def _explain_wer(wer):
    if wer == 0:
        return "Perfecto - Texto idéntico a referencia"
    elif wer < 0.3:
        return "Buena calidad - Pocas diferencias con referencia"
    elif wer < 0.5:
        return "Calidad aceptable - Algunas diferencias notables"
    else:
        return "Baja calidad - Muchas diferencias con referencia"


def _get_wer_quality(wer):
    if wer < 0.3:
        return "good"
    elif wer < 0.5:
        return "fair"
    else:
        return "poor"
