import os
import sys
import django
import logging

# Configurar entorno Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import UploadedDocument
from rag_system.storage.postgres_file_store import PostgresFileStore
from django.utils import timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_postgres_to_uploaded_docs():
    """
    Sincronizar archivos de la tabla document_files (PostgreSQL) 
    a la tabla api_uploadeddocument (Django)
    """
    print("🔄 Iniciando sincronización de metadatos...")
    
    store = PostgresFileStore()
    if not store.is_ready():
        print("❌ No se pudo conectar a PostgreSQL")
        return

    # Obtener todos los archivos de PostgreSQL
    files = store.list_files(limit=10000)
    print(f"📊 Encontrados {len(files)} archivos en PostgreSQL")
    
    count = 0
    updated = 0
    
    for file_info in files:
        try:
            file_name = file_info['file_name']
            drive_file_id = file_info.get('drive_file_id')
            file_id = file_info['id']
            
            # Verificar si ya existe en UploadedDocument
            doc, created = UploadedDocument.objects.update_or_create(
                file_name=file_name,
                defaults={
                    'file_path': f"postgres://{file_id}",
                    'file_size': file_info['file_size'],
                    'file_type': file_info['mime_type'],
                    'drive_file_id': drive_file_id,
                    'drive_uploaded': True,
                    'uploaded_at': file_info['created_at'] or timezone.now()
                }
            )
            
            if created:
                print(f"✅ Creado registro para: {file_name}")
                count += 1
            else:
                # Si existía pero apuntaba a otro lado, actualizar
                if not doc.file_path.startswith('postgres://'):
                    print(f"📝 Actualizado path para: {file_name}")
                    updated += 1
                    
        except Exception as e:
            print(f"❌ Error procesando {file_info.get('file_name')}: {e}")
            
    print(f"\n✨ Sincronización completada:")
    print(f"   - Nuevos registros: {count}")
    print(f"   - Actualizados: {updated}")

if __name__ == "__main__":
    sync_postgres_to_uploaded_docs()
