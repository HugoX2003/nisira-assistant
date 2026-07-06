"""
management command: ingest_stats
=================================
Calcula y muestra estadísticas (media ± desviación estándar) de los
tiempos de ingesta por fase, filtradas por batch_id o rango de fechas.

Uso:
    python manage.py ingest_stats
    python manage.py ingest_stats --batch-id <uuid>
    python manage.py ingest_stats --from-date 2025-01-01 --to-date 2025-01-31
    python manage.py ingest_stats --from-date 2025-01-01
"""

import statistics
from datetime import date, datetime, time

from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import make_aware

from api.models import DocumentIngestTiming


class Command(BaseCommand):
    help = "Estadísticas de tiempos de ingesta documental por fase"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-id",
            type=str,
            default=None,
            help="UUID de la corrida de sincronización (batch_id)",
        )
        parser.add_argument(
            "--from-date",
            type=str,
            default=None,
            metavar="YYYY-MM-DD",
            help="Fecha de inicio del rango (inclusive)",
        )
        parser.add_argument(
            "--to-date",
            type=str,
            default=None,
            metavar="YYYY-MM-DD",
            help="Fecha de fin del rango (inclusive)",
        )

    def handle(self, *args, **options):
        qs = DocumentIngestTiming.objects.all()

        # — Filtro por batch_id —
        if options["batch_id"]:
            qs = qs.filter(batch_id=options["batch_id"])

        # — Filtro por rango de fechas —
        if options["from_date"]:
            try:
                d = date.fromisoformat(options["from_date"])
                qs = qs.filter(run_at__gte=make_aware(datetime.combine(d, time.min)))
            except ValueError:
                raise CommandError(f"Formato de fecha inválido: {options['from_date']} (use YYYY-MM-DD)")

        if options["to_date"]:
            try:
                d = date.fromisoformat(options["to_date"])
                qs = qs.filter(run_at__lte=make_aware(datetime.combine(d, time.max)))
            except ValueError:
                raise CommandError(f"Formato de fecha inválido: {options['to_date']} (use YYYY-MM-DD)")

        records = list(qs.values("document_name", "download_seconds", "extraction_seconds", "embedding_seconds"))

        if not records:
            self.stdout.write(self.style.WARNING("No se encontraron registros con los filtros indicados."))
            return

        n = len(records)

        downloads = [r["download_seconds"] for r in records]
        extractions = [r["extraction_seconds"] for r in records]
        embeddings = [r["embedding_seconds"] for r in records]

        def stats(values):
            mean = statistics.mean(values)
            std = statistics.stdev(values) if len(values) > 1 else 0.0
            return mean, std

        dl_mean, dl_std = stats(downloads)
        ext_mean, ext_std = stats(extractions)
        emb_mean, emb_std = stats(embeddings)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("━" * 56))
        self.stdout.write(self.style.SUCCESS("  Estadísticas de tiempos de ingesta documental"))
        self.stdout.write(self.style.SUCCESS("━" * 56))

        # Encabezado de filtros activos
        if options["batch_id"]:
            self.stdout.write(f"  Batch : {options['batch_id']}")
        if options["from_date"] or options["to_date"]:
            rng = f"{options['from_date'] or '…'} → {options['to_date'] or '…'}"
            self.stdout.write(f"  Rango : {rng}")

        self.stdout.write("")
        self.stdout.write(
            f"  Descarga    : {dl_mean:.2f}s ± {dl_std:.2f}s  (n={n} documentos)"
        )
        self.stdout.write(
            f"  Extracción  : {ext_mean:.2f}s ± {ext_std:.2f}s  (n={n} documentos)"
        )
        self.stdout.write(
            f"  Embeddings  : {emb_mean:.2f}s ± {emb_std:.2f}s  (n={n} documentos)"
        )
        self.stdout.write("")

        total_mean = dl_mean + ext_mean + emb_mean
        self.stdout.write(f"  Total prom. : {total_mean:.2f}s por documento")
        self.stdout.write(self.style.SUCCESS("━" * 56))
        self.stdout.write("")

        # Detalle por documento (útil para batches pequeños)
        if n <= 20:
            self.stdout.write("  Detalle por documento:")
            header = f"  {'Documento':<40} {'DL':>7} {'Ext':>7} {'Emb':>7}"
            self.stdout.write(header)
            self.stdout.write("  " + "-" * 62)
            for r in records:
                name = r["document_name"][:40]
                self.stdout.write(
                    f"  {name:<40} {r['download_seconds']:>6.2f}s {r['extraction_seconds']:>6.2f}s {r['embedding_seconds']:>6.2f}s"
                )
            self.stdout.write("")
