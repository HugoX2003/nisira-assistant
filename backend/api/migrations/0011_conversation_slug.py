"""
Agregar campo `slug` aleatorio a Conversation.
- Anade columna nullable
- Genera slugs unicos para filas existentes
- Hace la columna unique + not null
"""
import secrets
from django.db import migrations, models


def _gen():
    return secrets.token_urlsafe(8)[:11]


def backfill_slugs(apps, schema_editor):
    Conversation = apps.get_model('api', 'Conversation')
    used = set(Conversation.objects.exclude(slug__isnull=True).values_list('slug', flat=True))
    for conv in Conversation.objects.filter(slug__isnull=True).iterator():
        while True:
            candidate = _gen()
            if candidate not in used:
                used.add(candidate)
                break
        conv.slug = candidate
        conv.save(update_fields=['slug'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_delete_embeddingstorage'),
    ]

    operations = [
        # 1. Agregar columna nullable temporalmente
        migrations.AddField(
            model_name='conversation',
            name='slug',
            field=models.CharField(max_length=16, null=True, blank=True, db_index=True),
        ),
        # 2. Backfill: generar slugs para filas existentes
        migrations.RunPython(backfill_slugs, noop_reverse),
        # 3. Hacer unique y not null con default
        migrations.AlterField(
            model_name='conversation',
            name='slug',
            field=models.CharField(
                max_length=16,
                unique=True,
                db_index=True,
                default='temp',
            ),
        ),
    ]
