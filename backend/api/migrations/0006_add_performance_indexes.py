# Generated manually for performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_querymetrics_ragasmetrics_and_more'),
    ]

    operations = [
        # Índices para QueryMetrics (rendimiento en dashboard y filtros)
        migrations.AddIndex(
            model_name='querymetrics',
            index=models.Index(fields=['created_at', 'total_latency'], name='api_queryme_created_total_idx'),
        ),
        migrations.AddIndex(
            model_name='querymetrics',
            index=models.Index(fields=['user', 'created_at'], name='api_queryme_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='querymetrics',
            index=models.Index(fields=['query_id'], name='api_queryme_query_id_idx'),
        ),
        
        # Índices para RAGASMetrics (filtros por calidad)
        migrations.AddIndex(
            model_name='ragasmetrics',
            index=models.Index(fields=['faithfulness_score', 'answer_relevancy'], name='api_ragasme_faithfu_idx'),
        ),
        migrations.AddIndex(
            model_name='ragasmetrics',
            index=models.Index(fields=['evaluation_timestamp'], name='api_ragasme_evaluat_ts_idx'),
        ),
        migrations.AddIndex(
            model_name='ragasmetrics',
            index=models.Index(fields=['evaluation_id'], name='api_ragasme_evaluat_idx'),
        ),
    ]
