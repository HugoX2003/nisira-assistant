#!/usr/bin/env python3
"""
Comando Django para gestionar la sincronización con Google Drive
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import os
import sys
import threading
import time
from pathlib import Path

class Command(BaseCommand):
    help = 'Gestiona la sincronización automática con Google Drive'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['start', 'stop', 'sync', 'status', 'setup'],
            default='sync',
            help='Acción a realizar'
        )
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Ejecutar como servicio en background'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Intervalo de sincronización en minutos'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        # Agregar path del backend
        backend_path = Path(__file__).parent.parent.parent.parent
        sys.path.append(str(backend_path))
        
        try:
            if action == 'setup':
                self._setup_google_drive()
            elif action == 'sync':
                self._sync_once()
            elif action == 'start':
                self._start_daemon(options['interval'])
            elif action == 'status':
                self._show_status()
            else:
                self.stdout.write(self.style.ERROR(f'Acción no implementada: {action}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            import traceback
            traceback.print_exc()
    
    def _setup_google_drive(self):
        """Ejecuta configuración inicial"""
        self.stdout.write("[START] Iniciando configuración de Google Drive...")
        
        try:
            from setup_google_drive import setup_google_drive
            success = setup_google_drive()
            
            if success:
                self.stdout.write(self.style.SUCCESS('[OK] Configuración completada'))
            else:
                self.stdout.write(self.style.ERROR('[ERROR] Error en configuración'))
                
        except ImportError:
            self.stdout.write(self.style.ERROR('[ERROR] Módulo setup_google_drive no encontrado'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[ERROR] Error: {e}'))
    
    def _sync_once(self):
        """Ejecuta sincronización única"""
        self.stdout.write("[SYNC] Iniciando sincronización única...")
        
        try:
            from google_drive_sync import GoogleDriveSync, create_sync_config
            from dotenv import load_dotenv
            
            # Cargar configuración
            load_dotenv()
            
            if not os.getenv("GOOGLE_DRIVE_ENABLED", "false").lower() == "true":
                self.stdout.write(self.style.WARNING('[WARN] Google Drive sync deshabilitado'))
                return
            
            config = create_sync_config()
            
            if not config.drive_folder_id:
                self.stdout.write(self.style.ERROR('[ERROR] GOOGLE_DRIVE_FOLDER_ID no configurado'))
                self.stdout.write('Ejecuta: python manage.py start_drive_sync --action setup')
                return
            
            # Crear sistema de sync
            sync_system = GoogleDriveSync(config)
            
            # Inicializar API
            if not sync_system.initialize_drive_api():
                self.stdout.write(self.style.ERROR('[ERROR] Error inicializando Google Drive API'))
                return
            
            # Ejecutar sincronización
            stats = sync_system.sync_once()
            
            # Mostrar resultados
            self.stdout.write(self.style.SUCCESS('[OK] Sincronización completada'))
            self.stdout.write(f"[INFO] Archivos encontrados: {stats['files_found']}")
            self.stdout.write(f"[INFO] Archivos descargados: {stats['files_downloaded']}")
            self.stdout.write(f"[SYNC] Archivos procesados: {stats['files_processed']}")
            
            if stats['errors'] > 0:
                self.stdout.write(self.style.WARNING(f"[WARN] Errores: {stats['errors']}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[ERROR] Error en sincronización: {e}'))
    
    def _start_daemon(self, interval_minutes):
        """Inicia servicio daemon"""
        self.stdout.write(f"[START] Iniciando servicio daemon (cada {interval_minutes} minutos)...")
        
        try:
            from google_drive_sync import GoogleDriveSync, create_sync_config
            from dotenv import load_dotenv
            
            # Cargar configuración
            load_dotenv()
            
            if not os.getenv("GOOGLE_DRIVE_ENABLED", "false").lower() == "true":
                self.stdout.write(self.style.ERROR('[ERROR] Google Drive sync deshabilitado'))
                return
            
            config = create_sync_config()
            config.sync_interval_minutes = interval_minutes
            
            # Crear sistema de sync
            sync_system = GoogleDriveSync(config)
            
            # Inicializar API
            if not sync_system.initialize_drive_api():
                self.stdout.write(self.style.ERROR('[ERROR] Error inicializando Google Drive API'))
                return
            
            # Iniciar servicio
            sync_system.start_background_sync()
            
            self.stdout.write(self.style.SUCCESS('[OK] Servicio iniciado'))
            self.stdout.write('Presiona Ctrl+C para detener...')
            
            # Mantener vivo
            try:
                while sync_system.running:
                    time.sleep(10)
            except KeyboardInterrupt:
                self.stdout.write('\n[INFO] Deteniendo servicio...')
                sync_system.stop_background_sync()
                self.stdout.write(self.style.SUCCESS('[OK] Servicio detenido'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[ERROR] Error: {e}'))
    
    def _show_status(self):
        """Muestra estado del sistema"""
        self.stdout.write("[STATS] ESTADO DEL SISTEMA GOOGLE DRIVE SYNC")
        self.stdout.write("=" * 50)
        
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            # Estado de configuración
            enabled = os.getenv("GOOGLE_DRIVE_ENABLED", "false").lower() == "true"
            folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
            interval = os.getenv("SYNC_INTERVAL_MINUTES", "30")
            auto_process = os.getenv("AUTO_PROCESS_NEW_FILES", "true").lower() == "true"
            
            self.stdout.write(f"[CONFIG] Habilitado: {'[OK] Sí' if enabled else '[ERROR] No'}")
            self.stdout.write(f"[DIR] Carpeta ID: {folder_id if folder_id else '[ERROR] No configurado'}")
            self.stdout.write(f"⏱️ Intervalo: {interval} minutos")
            self.stdout.write(f"[SYNC] Auto-proceso: {'[OK] Sí' if auto_process else '[ERROR] No'}")
            
            # Verificar archivos
            backend_path = Path(__file__).parent.parent.parent.parent
            creds_path = backend_path / "credentials.json"
            token_path = backend_path / "token.json"
            
            self.stdout.write(f"\n[LIST] ARCHIVOS:")
            self.stdout.write(f"[KEY] credentials.json: {'[OK] Existe' if creds_path.exists() else '[ERROR] No existe'}")
            self.stdout.write(f"[INFO] token.json: {'[OK] Existe' if token_path.exists() else '[ERROR] No existe'}")
            
            # Estado de directorios
            data_dir = backend_path / "data"
            downloads_dir = data_dir / "downloads"
            pdfs_dir = data_dir / "pdfs"
            texts_dir = data_dir / "texts"
            
            self.stdout.write(f"\n[DIR] DIRECTORIOS:")
            self.stdout.write(f"[INFO] downloads: {'[OK]' if downloads_dir.exists() else '[ERROR]'}")
            self.stdout.write(f"[INFO] pdfs: {'[OK]' if pdfs_dir.exists() else '[ERROR]'}")
            self.stdout.write(f"[NOTE] texts: {'[OK]' if texts_dir.exists() else '[ERROR]'}")
            
            # Contar archivos procesados
            processed_file = data_dir / "processed_files.json"
            if processed_file.exists():
                import json
                with open(processed_file, 'r') as f:
                    data = json.load(f)
                    processed_count = len(data.get('processed_files', []))
                    self.stdout.write(f"[STATS] Archivos procesados: {processed_count}")
            
            if not enabled:
                self.stdout.write(f"\n[TIP] Para habilitar:")
                self.stdout.write(f"   python manage.py start_drive_sync --action setup")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[ERROR] Error: {e}'))