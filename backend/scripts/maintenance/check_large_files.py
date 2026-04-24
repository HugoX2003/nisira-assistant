#!/usr/bin/env python
"""
Script para identificar archivos grandes en Google Drive sin descargarlos
Muestra el tamaño de cada archivo para ayudar a decidir el límite MAX_FILE_SIZE
"""

import os
import sys
from pathlib import Path

# Agregar el directorio backend al path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from rag_system.drive_sync.drive_manager import GoogleDriveManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_size(size_bytes):
    """Formatear tamaño en bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def main():
    logger.info("[SEARCH] Analizando archivos en Google Drive...")

    # Inicializar Google Drive Manager
    manager = GoogleDriveManager()

    if not manager.service:
        logger.error("[ERROR] No se pudo inicializar Google Drive")
        return

    # Obtener lista de archivos con tamaños
    files = manager.list_files()

    if not files:
        logger.warning("[WARN] No se encontraron archivos")
        return
    
    # Recopilar información de tamaños
    file_info = []
    
    for file_data in files:
        file_id = file_data['id']
        file_name = file_data['name']
        
        # Obtener metadatos completos incluyendo tamaño
        try:
            metadata = manager.service.files().get(
                fileId=file_id, 
                fields='id,name,mimeType,size'
            ).execute()
            
            size_str = metadata.get('size', '0')
            size_bytes = int(size_str) if size_str else 0
            mime_type = metadata.get('mimeType', 'unknown')
            
            file_info.append({
                'name': file_name,
                'size_bytes': size_bytes,
                'size_formatted': format_size(size_bytes),
                'mime_type': mime_type
            })
            
        except Exception as e:
            logger.warning(f"[WARN] No se pudo obtener tamaño de {file_name}: {e}")
    
    # Ordenar por tamaño (mayor a menor)
    file_info.sort(key=lambda x: x['size_bytes'], reverse=True)
    
    # Estadísticas
    total_files = len(file_info)
    total_size = sum(f['size_bytes'] for f in file_info)
    avg_size = total_size / total_files if total_files > 0 else 0
    
    # Límites para análisis
    limits = {
        '10MB': 10 * 1024 * 1024,
        '25MB': 25 * 1024 * 1024,
        '50MB': 50 * 1024 * 1024,
        '100MB': 100 * 1024 * 1024
    }
    
    print("\n" + "="*80)
    print("[STATS] ANÁLISIS DE TAMAÑOS DE ARCHIVOS EN GOOGLE DRIVE")
    print("="*80)

    print(f"\n[DIR] Total de archivos: {total_files}")
    print(f"[SAVE] Tamaño total: {format_size(total_size)}")
    print(f"[INFO] Tamaño promedio: {format_size(avg_size)}")

    # Contar archivos por límite
    print("\n[UP] DISTRIBUCIÓN POR TAMAÑO:")
    for limit_name, limit_bytes in limits.items():
        count = sum(1 for f in file_info if f['size_bytes'] > limit_bytes)
        percentage = (count / total_files * 100) if total_files > 0 else 0
        print(f"   > {limit_name:6s}: {count:3d} archivos ({percentage:5.1f}%)")
    
    # Mostrar los 10 archivos más grandes
    print("\n[INFO] TOP 10 ARCHIVOS MÁS GRANDES:")
    print("-" * 80)
    for i, file in enumerate(file_info[:10], 1):
        print(f"{i:2d}. {file['size_formatted']:>10s} - {file['name']}")
    
    # Mostrar archivos que exceden 50MB (límite actual)
    large_files = [f for f in file_info if f['size_bytes'] > 50 * 1024 * 1024]
    
    if large_files:
        print(f"\n[WARN]  ARCHIVOS QUE EXCEDEN 50MB (límite actual):")
        print("-" * 80)
        for file in large_files:
            print(f"   {file['size_formatted']:>10s} - {file['name']}")

        print(f"\n[TIP] RECOMENDACIONES:")
        print(f"   • {len(large_files)} archivos exceden el límite de 50MB")
        print(f"   • Estos archivos causarán OOM si intentas sincronizarlos")
        print(f"   • Opciones:")
        print(f"     1. Mantener límite en 50MB (rechazar {len(large_files)} archivos)")
        print(f"     2. Aumentar límite a 100MB (rechazar {sum(1 for f in file_info if f['size_bytes'] > 100*1024*1024)} archivos)")
        print(f"     3. Comprimir archivos grandes antes de subirlos a Drive")
    else:
        print(f"\n[OK] Todos los archivos están bajo el límite de 50MB")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
