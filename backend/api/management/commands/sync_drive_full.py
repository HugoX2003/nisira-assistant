
"""
Sincronizar PDFs desde Google Drive, extraer texto y alimentar ChromaDB.

Opciones:
    --chunk-size: tamaño de cada fragmento de texto para embeddings
    --chunk-overlap: solapamiento entre fragmentos
    --force: fuerza la descarga de PDFs aunque ya existan localmente
"""
from django.core.management.base import BaseCommand
import os

class Command(BaseCommand):
    # Descripción del comando para ayuda en CLI
    help = "Sync + extraer texto + ingestar PDFs desde Google Drive"

    def add_arguments(self, parser):
        """
        Define los argumentos que acepta el comando:
        - chunk-size: tamaño de los fragmentos de texto
        - chunk-overlap: solapamiento entre fragmentos
        - force: fuerza la descarga de PDFs
        """
        parser.add_argument('--chunk-size', type=int, default=500)
        parser.add_argument('--chunk-overlap', type=int, default=50)
        parser.add_argument('--force', action='store_true', default=False)

    def handle(self, *args, **opts):
        """
        Lógica principal del comando:
        - Sincroniza documentos desde Google Drive usando RAGPipeline
        - Procesa y genera embeddings
        """
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando sincronización completa desde Google Drive...'))
        
        try:
            # Importar RAGPipeline directamente
            import sys
            from django.conf import settings
            
            rag_path = os.path.join(settings.BASE_DIR, 'rag_system')
            if rag_path not in sys.path:
                sys.path.append(rag_path)
            
            from rag_system.rag_engine.pipeline import RAGPipeline
            
            # Crear instancia del pipeline
            pipeline = RAGPipeline()
            
            # Ejecutar sincronización y procesamiento
            force_reprocess = opts.get('force', False)
            self.stdout.write(f'Forzar reprocesamiento: {force_reprocess}')
            
            result = pipeline.sync_and_process_documents(force_reprocess=force_reprocess)
            
            if result.get('success'):
                self.stdout.write(self.style.SUCCESS('✅ Sincronización completada exitosamente'))
                self.stdout.write(f"📊 Documentos procesados: {result.get('documents_processed', 0)}")
                self.stdout.write(f"📝 Chunks generados: {result.get('chunks_generated', 0)}")
            else:
                self.stdout.write(self.style.ERROR(f'❌ Error: {result.get("error", "Unknown error")}'))
                
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'❌ Sistema RAG no disponible: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error durante sincronización: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())