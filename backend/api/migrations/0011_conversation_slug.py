"""
Agregar campo `slug` aleatorio a Conversation para URLs publicas.

Idempotente: tolera ejecuciones parciales previas. Si la columna o el indice
quedaron de una corrida fallida anterior, los limpia antes de crear de nuevo.

Estrategia:
1. RunSQL idempotente: drop slug column + drop indice _like si existen
2. AddField (sin db_index; unique=True bastara despues)
3. RunPython: backfill de slugs para filas existentes
4. AlterField: unique=True (crea automaticamente indice b-tree unico)
"""
import secrets
from django.db import migrations, models


def _gen():
    return secrets.token_urlsafe(8)[:11]


def backfill_slugs(apps, schema_editor):
    Conversation = apps.get_model('api', 'Conversation')
    used = set(
        Conversation.objects.exclude(slug__isnull=True).values_list('slug', flat=True)
    )
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
        # 1. Limpiar estado residual de un intento anterior fallido (idempotente).
        #    Si la columna ya existe o el indice _like ya existe, los borramos
        #    para empezar limpio. state_operations=[] porque no cambia el state
        #    de Django (la columna no esta declarada todavia en el modelo).
        migrations.RunSQL(
            sql=(
                "DROP INDEX IF EXISTS api_conversation_slug_c1907496_like; "
                "ALTER TABLE api_conversation DROP COLUMN IF EXISTS slug;"
            ),
            reverse_sql=migrations.RunSQL.noop,
            state_operations=[],
        ),

        # 2. Agregar columna nullable (sin indice; unique=True lo creara despues)
        migrations.AddField(
            model_name='conversation',
            name='slug',
            field=models.CharField(max_length=16, null=True, blank=True),
        ),

        # 3. Backfill: generar slugs para filas existentes
        migrations.RunPython(backfill_slugs, noop_reverse),

        # 4. Hacer unique y not null (unique=True crea automaticamente indice)
        migrations.AlterField(
            model_name='conversation',
            name='slug',
            field=models.CharField(max_length=16, unique=True, default='temp'),
        ),
    ]
