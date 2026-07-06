from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0011_conversation_slug"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentIngestTiming",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("batch_id", models.UUIDField(db_index=True, help_text="Identifica la corrida de sincronización")),
                ("document_name", models.CharField(max_length=255)),
                ("drive_file_id", models.CharField(blank=True, max_length=255, null=True)),
                ("run_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("download_seconds", models.FloatField(help_text="Tiempo de descarga desde Google Drive")),
                ("extraction_seconds", models.FloatField(help_text="Tiempo de extracción de texto y chunking")),
                ("embedding_seconds", models.FloatField(help_text="Tiempo de generación de embeddings")),
                ("chunks_count", models.IntegerField(default=0, help_text="Chunks generados para este documento")),
            ],
            options={
                "verbose_name": "Tiempo de ingesta por documento",
                "verbose_name_plural": "Tiempos de ingesta por documento",
                "ordering": ["-run_at"],
            },
        ),
    ]
