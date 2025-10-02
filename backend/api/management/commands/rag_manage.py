"""
Comando Django para gestionar el sistema RAG
==========================================

Permite sincronizar documentos, procesar archivos y realizar consultas
desde la línea de comandos.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import json
import os
import sys

# Agregar el path del rag_system al Python path
sys.path.append(os.path.join(settings.BASE_DIR, 'rag_system'))

try:
    from rag_system import (
        initialize_rag_system, 
        get_rag_status,
        sync_drive_documents,
        query_rag,
        RAG_MODULES_AVAILABLE
    )
    from rag_system.rag_engine.pipeline import RAGPipeline
except ImportError as e:
    RAG_MODULES_AVAILABLE = False
    RAGPipeline = None

class Command(BaseCommand):
    help = 'Gestionar el sistema RAG (Retrieval-Augmented Generation)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['status', 'init', 'sync', 'query', 'reset', 'process'],
            help='Acción a realizar'
        )
        
        parser.add_argument(
            '--question', '-q',
            type=str,
            help='Pregunta para consulta RAG'
        )
        
        parser.add_argument(
            '--file', '-f',
            type=str,
            help='Archivo específico a procesar'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar reprocesamiento de documentos'
        )
        
        parser.add_argument(
            '--top-k', '-k',
            type=int,
            default=5,
            help='Número de documentos relevantes a recuperar (default: 5)'
        )
        
        parser.add_argument(
            '--no-generation',
            action='store_true',
            help='Solo búsqueda, sin generación de respuesta'
        )
        
        parser.add_argument(
            '--format',
            choices=['json', 'text'],
            default='text',
            help='Formato de salida (default: text)'
        )
    
    def handle(self, *args, **options):
        if not RAG_MODULES_AVAILABLE:
            raise CommandError(
                "❌ Sistema RAG no disponible. "
                "Instala las dependencias: pip install -r requirements.txt"
            )
        
        action = options['action']
        
        try:
            if action == 'status':
                self._handle_status(options)
            elif action == 'init':
                self._handle_init(options)
            elif action == 'sync':
                self._handle_sync(options)
            elif action == 'query':
                self._handle_query(options)
            elif action == 'reset':
                self._handle_reset(options)
            elif action == 'process':
                self._handle_process(options)
            else:
                raise CommandError(f"Acción no reconocida: {action}")
                
        except Exception as e:
            raise CommandError(f"❌ Error ejecutando {action}: {e}")
    
    def _handle_status(self, options):
        """Mostrar estado del sistema RAG"""
        self.stdout.write("🔍 Verificando estado del sistema RAG...")
        
        try:
            status = get_rag_status()
            
            if options['format'] == 'json':
                self.stdout.write(json.dumps(status, indent=2, ensure_ascii=False))
                return
            
            # Formato texto
            self.stdout.write(f"\\n📊 Estado del Sistema RAG")
            self.stdout.write(f"========================")
            self.stdout.write(f"Versión: {status.get('version', 'Unknown')}")
            self.stdout.write(f"Módulos disponibles: {'✅' if status['modules_available'] else '❌'}")
            
            # Configuración
            config = status.get('configuration', {})
            self.stdout.write(f"\\n🔧 Configuración:")
            for key, value in config.items():
                icon = '✅' if value else '❌'
                self.stdout.write(f"  {icon} {key}")
            
            # Componentes
            if 'components' in status:
                self.stdout.write(f"\\n🧩 Componentes:")
                for component, ready in status['components'].items():
                    icon = '✅' if ready else '❌'
                    self.stdout.write(f"  {icon} {component}")
            
            if 'components_error' in status:
                self.stdout.write(f"\\n⚠️  Error en componentes: {status['components_error']}")
            
        except Exception as e:
            raise CommandError(f"Error obteniendo estado: {e}")
    
    def _handle_init(self, options):
        """Inicializar sistema RAG"""
        self.stdout.write("🚀 Inicializando sistema RAG...")
        
        try:
            result = initialize_rag_system()
            
            if options['format'] == 'json':
                self.stdout.write(json.dumps(result, indent=2, ensure_ascii=False))
                return
            
            if result['success']:
                self.stdout.write("✅ Sistema RAG inicializado correctamente")
                
                components = result.get('components', {})
                for component, status in components.items():
                    icon = '✅' if status else '❌'
                    self.stdout.write(f"  {icon} {component}")
            else:
                self.stdout.write(f"❌ Error inicializando: {result.get('error', 'Unknown')}")
                
                if 'config_status' in result:
                    self.stdout.write("\\n🔧 Estado de configuración:")
                    for key, value in result['config_status'].items():
                        icon = '✅' if value else '❌'
                        self.stdout.write(f"  {icon} {key}")
            
        except Exception as e:
            raise CommandError(f"Error inicializando: {e}")
    
    def _handle_sync(self, options):
        """Sincronizar documentos desde Google Drive"""
        self.stdout.write("📥 Sincronizando documentos desde Google Drive...")
        
        try:
            pipeline = RAGPipeline()
            result = pipeline.sync_and_process_documents(
                force_reprocess=options.get('force', False)
            )
            
            if options['format'] == 'json':
                self.stdout.write(json.dumps(result, indent=2, ensure_ascii=False))
                return
            
            if result['success']:
                sync_result = result.get('sync_result', {})
                processing = result.get('processing_summary', {})
                
                self.stdout.write("✅ Sincronización completada")
                self.stdout.write(f"\\n📁 Archivos Drive:")
                self.stdout.write(f"  📥 Descargados: {sync_result.get('downloaded', 0)}")
                self.stdout.write(f"  ⏭️  Omitidos: {sync_result.get('skipped', 0)}")
                self.stdout.write(f"  ❌ Errores: {sync_result.get('errors', 0)}")
                
                self.stdout.write(f"\\n📄 Procesamiento:")
                self.stdout.write(f"  ✅ Exitosos: {processing.get('successful', 0)}")
                self.stdout.write(f"  ❌ Fallidos: {processing.get('failed', 0)}")
                self.stdout.write(f"  📝 Chunks: {processing.get('valid_chunks', 0)}")
                
            else:
                self.stdout.write(f"❌ Error en sincronización: {result.get('error', 'Unknown')}")
            
        except Exception as e:
            raise CommandError(f"Error sincronizando: {e}")
    
    def _handle_query(self, options):
        """Realizar consulta RAG"""
        question = options.get('question')
        
        if not question:
            raise CommandError("❌ Pregunta requerida. Usa --question 'tu pregunta'")
        
        self.stdout.write(f"❓ Procesando consulta: {question}")
        
        try:
            pipeline = RAGPipeline()
            result = pipeline.query(
                question=question,
                top_k=options.get('top_k', 5),
                include_generation=not options.get('no_generation', False)
            )
            
            if options['format'] == 'json':
                self.stdout.write(json.dumps(result, indent=2, ensure_ascii=False))
                return
            
            if result['success']:
                self.stdout.write(f"\\n🔍 Documentos encontrados: {len(result.get('relevant_documents', []))}")
                
                # Mostrar fuentes
                sources = result.get('sources', [])
                if sources:
                    self.stdout.write(f"\\n📚 Fuentes:")
                    for source in sources[:3]:  # Solo las 3 más relevantes
                        score = source.get('similarity_score', 0)
                        self.stdout.write(f"  📄 {source.get('file_name', 'unknown')} (similitud: {score:.3f})")
                
                # Mostrar respuesta
                answer = result.get('answer')
                if answer:
                    self.stdout.write(f"\\n💬 Respuesta:")
                    self.stdout.write(f"{answer}")
                else:
                    self.stdout.write(f"\\n⚠️  No se generó respuesta automática")
                    
                    # Mostrar contexto si no hay respuesta
                    context = result.get('context', '')
                    if context:
                        self.stdout.write(f"\\n📋 Contexto encontrado:")
                        self.stdout.write(f"{context[:500]}...")
            else:
                self.stdout.write(f"❌ Error en consulta: {result.get('error', 'Unknown')}")
            
        except Exception as e:
            raise CommandError(f"Error en consulta: {e}")
    
    def _handle_process(self, options):
        """Procesar archivo específico"""
        file_path = options.get('file')
        
        if not file_path:
            raise CommandError("❌ Archivo requerido. Usa --file 'ruta/al/archivo'")
        
        if not os.path.exists(file_path):
            raise CommandError(f"❌ Archivo no encontrado: {file_path}")
        
        self.stdout.write(f"📄 Procesando archivo: {os.path.basename(file_path)}")
        
        try:
            pipeline = RAGPipeline()
            result = pipeline.process_document(file_path)
            
            if options['format'] == 'json':
                self.stdout.write(json.dumps(result, indent=2, ensure_ascii=False))
                return
            
            if result['success']:
                stats = result.get('stats', {})
                
                self.stdout.write("✅ Archivo procesado correctamente")
                self.stdout.write(f"\\n📊 Estadísticas:")
                self.stdout.write(f"  📝 Caracteres: {stats.get('total_chars', 0):,}")
                self.stdout.write(f"  🔤 Palabras: {stats.get('total_words', 0):,}")
                self.stdout.write(f"  📄 Chunks: {stats.get('total_chunks', 0)}")
                self.stdout.write(f"  🔧 Método: {stats.get('processing_method', 'unknown')}")
                
            else:
                self.stdout.write(f"❌ Error procesando archivo: {result.get('error', 'Unknown')}")
            
        except Exception as e:
            raise CommandError(f"Error procesando archivo: {e}")
    
    def _handle_reset(self, options):
        """Resetear sistema RAG"""
        self.stdout.write("⚠️  Reseteando sistema RAG...")
        
        # Confirmación de seguridad
        confirm = input("\\n¿Estás seguro de que quieres eliminar todos los documentos? (sí/no): ")
        
        if confirm.lower() not in ['sí', 'si', 'yes', 'y']:
            self.stdout.write("❌ Operación cancelada")
            return
        
        try:
            pipeline = RAGPipeline()
            result = pipeline.reset_system()
            
            if options['format'] == 'json':
                self.stdout.write(json.dumps(result, indent=2, ensure_ascii=False))
                return
            
            if result['success']:
                self.stdout.write("✅ Sistema RAG reseteado completamente")
                self.stdout.write("  🗑️  Base de datos vectorial limpiada")
                self.stdout.write("  🧹 Cache de embeddings limpiado")
                self.stdout.write("  📊 Estadísticas reiniciadas")
            else:
                self.stdout.write(f"❌ Error reseteando: {result.get('error', 'Unknown')}")
            
        except Exception as e:
            raise CommandError(f"Error reseteando: {e}")