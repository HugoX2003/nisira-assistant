#!/usr/bin/env python
import os
import sys
sys.path.insert(0, '/app')

from rag_system.drive_sync.drive_service import GoogleDriveService

def main():
    folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    print(f'[SEARCH] Verificando Google Drive...')
    print(f'[DIR] Folder ID: {folder_id}')

    if not folder_id:
        print('[ERROR] GOOGLE_DRIVE_FOLDER_ID no configurado')
        return

    try:
        service = GoogleDriveService()
        files = service.list_files_in_folder(folder_id)
        print(f'[STATS] Total de archivos encontrados: {len(files)}')

        if files:
            print('\n[INFO] Primeros 10 archivos:')
            for i, f in enumerate(files[:10], 1):
                print(f"  {i}. {f.get('name')} ({f.get('mimeType')})")
        else:
            print('[WARN] No se encontraron archivos en la carpeta')

    except Exception as e:
        print(f'[ERROR] Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
