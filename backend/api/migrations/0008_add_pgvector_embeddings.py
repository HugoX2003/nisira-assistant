# Generated migration for pgvector embeddings storage

from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_add_wer_score'),
    ]

    operations = [
        # Habilitar extensión pgvector (opcional, funciona sin ella)
        migrations.RunSQL(
            sql='CREATE EXTENSION IF NOT EXISTS vector;',
            reverse_sql='DROP EXTENSION IF EXISTS vector;'
        ),
        
        # Crear tabla para embeddings
        migrations.CreateModel(
            name='EmbeddingStorage',
            fields=[
                ('id', models.UUIDField(primary_key=True, editable=False)),
                ('chunk_text', models.TextField(help_text='Texto del chunk procesado')),
                ('embedding_vector', models.TextField(help_text='Vector de embedding serializado como JSON')),
                ('metadata', models.JSONField(default=dict, help_text='Metadata del documento')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'rag_embeddings',
                'indexes': [
                    models.Index(fields=['created_at'], name='rag_emb_created_idx'),
                ],
            },
        ),
    ]
