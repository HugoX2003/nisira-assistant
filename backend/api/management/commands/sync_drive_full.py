
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
        - Llama a la vista sync_drive_full_view 
        - Simula una petición POST con los parámetros recibidos
        - Muestra el resultado en consola (OK o error)
        """
        # Asegura que la vista no exija autenticación para este comando
        os.environ["AUTH_REQUIRED"] = "false"

        from api.views import sync_drive_full_view
        from django.test import RequestFactory

        # Crea una petición POST simulada con los datos recibidos
        rf = RequestFactory()
        data = {
            'chunk_size': opts['chunk_size'],
            'chunk_overlap': opts['chunk_overlap'],
            'force': opts['force'],
        }
        req = rf.post('/sync-drive/full', data)

        # Ejecuta la vista y obtiene la respuesta
        resp = sync_drive_full_view(req)

        # Muestra el resultado en consola
        if hasattr(resp, 'status_code') and resp.status_code == 200:
            self.stdout.write(self.style.SUCCESS("OK: " + str(getattr(resp, 'data', {}))))
        else:
            self.stderr.write("ERROR: status=" + str(getattr(resp, 'status_code', 'unknown')) + " body=" + str(getattr(resp, 'data', {})))