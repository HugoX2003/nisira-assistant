"""
Comando de benchmark: mide tiempos reales de descarga, extracción y
embeddings sobre una muestra de documentos, SIN insertarlos en el
índice de producción (no llama a add_documents()).

Uso:
  python manage.py benchmark_ingest --sample 25
  python manage.py benchmark_ingest --sample 25 --folder-id <ID_OPCIONAL>
"""
import os
import random
import uuid
from time import perf_counter

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Benchmark de tiempos de ingesta (descarga, extracción, embeddings) por documento, sin indexar."

    def add_arguments(self, parser):
        parser.add_argument("--sample", type=int, default=25, help="Cantidad de documentos a muestrear")
        parser.add_argument("--folder-id", type=str, default=None, help="ID de carpeta de Drive (opcional)")
        parser.add_argument("--seed", type=int, default=42, help="Semilla para muestreo aleatorio reproducible")

    def handle(self, *args, **options):
        from rag_system.rag_engine.pipeline import RAGPipeline  # ajusta el import si la clase vive en otro módulo
        from api.models import DocumentIngestTiming

        sample_n = options["sample"]
        folder_id = options["folder_id"]
        random.seed(options["seed"])

        pipeline = RAGPipeline()  # ajusta si tu pipeline se instancia distinto (p.ej. como singleton)

        self.stdout.write(f"Listando archivos en Drive (folder_id={folder_id or 'default'})...")
        files = pipeline.drive_manager.list_files(folder_id=folder_id)
        if not files:
            self.stderr.write("No se encontraron archivos en Drive.")
            return

        sample_files = random.sample(files, min(sample_n, len(files)))
        self.stdout.write(f"Muestra seleccionada: {len(sample_files)} documentos de {len(files)} totales.")

        batch_id = uuid.uuid4()
        self.stdout.write(f"Batch de benchmark: {batch_id}")

        download_dir = getattr(pipeline.drive_manager, "download_path", "/tmp/benchmark_downloads")
        os.makedirs(download_dir, exist_ok=True)

        for i, f in enumerate(sample_files, 1):
            file_id = f.get("id")
            file_name = f.get("name")
            self.stdout.write(f"[{i}/{len(sample_files)}] {file_name}")

            try:
                # --- Descarga real ---
                t0 = perf_counter()
                local_path = pipeline.drive_manager.download_file(
                    file_id, file_name, f.get("modifiedTime")
                )
                download_seconds = perf_counter() - t0

                if not local_path or not os.path.exists(local_path):
                    self.stderr.write(f"  Descarga fallida para {file_name}, se omite.")
                    continue

                # --- Extracción + chunking ---
                t1 = perf_counter()
                result = pipeline.process_document(local_path)
                extraction_seconds = perf_counter() - t1

                if not result.get("success"):
                    self.stderr.write(f"  Error procesando {file_name}: {result.get('error')}")
                    continue

                chunks = result.get("chunks", [])
                chunk_texts = [c["text"] for c in chunks]

                # --- Embeddings ---
                t2 = perf_counter()
                embeddings = (
                    pipeline.embedding_manager.create_embeddings_batch(chunk_texts)
                    if chunk_texts else []
                )
                embedding_seconds = perf_counter() - t2

                valid_count = sum(1 for e in embeddings if e is not None)

                DocumentIngestTiming.objects.create(
                    batch_id=batch_id,
                    document_name=file_name,
                    drive_file_id=file_id,
                    download_seconds=round(download_seconds, 4),
                    extraction_seconds=round(extraction_seconds, 4),
                    embedding_seconds=round(embedding_seconds, 4),
                    chunks_count=valid_count,
                )

                self.stdout.write(
                    f"  OK: descarga={download_seconds:.2f}s "
                    f"extracción={extraction_seconds:.2f}s "
                    f"embeddings={embedding_seconds:.2f}s "
                    f"chunks={valid_count}"
                )

                # IMPORTANTE: no se llama a add_documents() / no se toca pgvector de producción.

            except Exception as e:
                self.stderr.write(f"  Error inesperado con {file_name}: {e}")
                continue

        self.stdout.write(self.style.SUCCESS(
            f"\nBenchmark completado. Corre ahora:\n"
            f"  python manage.py ingest_stats --batch-id {batch_id}\n"
            f"para ver media y desviación estándar por fase."
        ))