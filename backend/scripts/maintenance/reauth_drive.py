"""
Script para re-autenticar Google Drive con nuevos permisos
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rag_system.drive_sync.drive_manager import GoogleDriveManager

def main():
    print("[INFO] Re-autenticando Google Drive con nuevos permisos...")
    print("=" * 60)

    # Crear instancia del manager
    drive_manager = GoogleDriveManager()

    # Verificar autenticación
    if drive_manager.is_authenticated():
        print("[OK] Google Drive autenticado correctamente!")
        print(f"[DIR] Folder ID: {drive_manager.folder_id}")

        # Listar archivos para verificar
        print("\n[LIST] Listando archivos en Google Drive...")
        try:
            files = drive_manager.list_files()
            print(f"[OK] Se encontraron {len(files)} archivos")

            for i, file in enumerate(files[:5], 1):
                print(f"  {i}. {file.get('name')} ({file.get('mimeType')})")

            if len(files) > 5:
                print(f"  ... y {len(files) - 5} archivos más")

            print("\n[OK] ¡Todo listo! Ahora puedes subir y eliminar archivos desde el panel de administración.")

        except Exception as e:
            print(f"[WARN] Error listando archivos: {e}")
            print("Pero la autenticación fue exitosa.")
    else:
        print("[ERROR] Error: No se pudo autenticar con Google Drive")
        print("Verifica que el archivo credentials.json esté en la carpeta backend/")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
