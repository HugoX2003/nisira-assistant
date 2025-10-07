#!/bin/bash

# 🚀 Script de despliegue rápido para Railway

echo "🚀 PREPARANDO DESPLIEGUE EN RAILWAY"
echo "=================================="

# 1. Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Este script debe ejecutarse desde el directorio backend/"
    exit 1
fi

# 2. Generar SECRET_KEY si no existe
if [ -z "$DJANGO_SECRET_KEY" ]; then
    echo "🔑 Generando Django SECRET_KEY..."
    export DJANGO_SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    echo "✅ SECRET_KEY generada: $DJANGO_SECRET_KEY"
    echo ""
    echo "⚠️  IMPORTANTE: Guarda esta clave en Railway como variable de entorno:"
    echo "   DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY"
    echo ""
fi

# 3. Instalar dependencias de producción
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# 4. Recolectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# 5. Aplicar migraciones
echo "🗄️  Aplicando migraciones..."
python manage.py migrate

# 6. Test de salud
echo "🏥 Verificando sistema..."
python manage.py check --deploy

echo ""
echo "✅ PREPARACIÓN COMPLETADA"
echo "========================"
echo ""
echo "📋 PRÓXIMOS PASOS:"
echo "1. Subir código a GitHub"
echo "2. Crear proyecto en Railway"
echo "3. Agregar variables de entorno:"
echo "   - DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY"
echo "   - OPENROUTER_API_KEY=tu_clave_aqui"
echo "   - ALLOWED_HOSTS=*.railway.app"
echo "4. Agregar volumen persistente en /app/data"
echo ""