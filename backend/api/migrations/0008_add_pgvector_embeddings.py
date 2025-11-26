# Generated migration for pgvector embeddings storage

from django.db import migrations, models, connection


def create_vector_extension(apps, schema_editor):
    """Solo crear extensión vector si es PostgreSQL"""
    if connection.vendor == 'postgresql':
        schema_editor.execute('CREATE EXTENSION IF NOT EXISTS vector;')


def drop_vector_extension(apps, schema_editor):
    """Solo eliminar extensión vector si es PostgreSQL"""
    if connection.vendor == 'postgresql':
        schema_editor.execute('DROP EXTENSION IF EXISTS vector;')


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_add_wer_score'),
    ]

    operations = [
        # Habilitar extensión pgvector solo en PostgreSQL
        migrations.RunPython(create_vector_extension, drop_vector_extension),
        
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
