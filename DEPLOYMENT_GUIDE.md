# 🚀 GUÍA DE DESPLIEGUE GRATUITO - SISTEMA RAG NISIRA

## 📋 ÍNDICE
1. [Opciones de Despliegue](#opciones)
2. [Despliegue Recomendado](#recomendado)
3. [Configuración Paso a Paso](#pasos)
4. [Variables de Entorno](#variables)
5. [Troubleshooting](#troubleshooting)

---

## 🎯 OPCIONES DE DESPLIEGUE GRATUITO

### Opción 1: Railway.app (RECOMENDADO) ⭐
**Backend + Base de Datos**
- ✅ 500 horas/mes gratis
- ✅ 512 MB RAM
- ✅ 1 GB almacenamiento persistente
- ✅ Soporta ChromaDB
- ⚠️ Requiere tarjeta (no cobran)

**Frontend en Vercel**
- ✅ Ilimitado gratis
- ✅ CDN global
- ✅ Deploy automático desde GitHub

### Opción 2: Render.com
**Backend**
- ✅ 750 horas/mes gratis
- ✅ 512 MB RAM
- ⚠️ Se duerme después de 15 min inactividad
- ⚠️ Almacenamiento efímero (ChromaDB se pierde)

**Frontend en Vercel**
- ✅ Mismo que opción 1

### Opción 3: Google Cloud Run (Avanzado)
- ✅ 2 millones requests/mes gratis
- ✅ Alta escalabilidad
- ⚠️ Setup más complejo
- ⚠️ Requiere Docker

---

## ⭐ DESPLIEGUE RECOMENDADO: RAILWAY + VERCEL

### 🏗️ ARQUITECTURA
```
Frontend (React)          Backend (Django)           Datos
━━━━━━━━━━━━━━━          ━━━━━━━━━━━━━━━           ━━━━━━━
   Vercel          →          Railway          ←    ChromaDB
(CDN Global)              (Servidor Python)        (Persistente)
```

---

## 📝 PASO A PASO: RAILWAY + VERCEL

### 🔧 PREPARACIÓN PREVIA (5 minutos)

#### 1. Crear cuenta en Railway
```bash
1. Ir a https://railway.app
2. Sign up con GitHub
3. Verificar email
```

#### 2. Crear cuenta en Vercel
```bash
1. Ir a https://vercel.com
2. Sign up con GitHub
3. Conectar repositorio
```

#### 3. Subir proyecto a GitHub
```bash
# En tu proyecto local
git init
git add .
git commit -m "Initial commit - RAG System"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/nisira-assistant.git
git push -u origin main
```

---

### 🎯 PARTE 1: DESPLEGAR BACKEND EN RAILWAY

#### Paso 1: Crear proyecto en Railway
```
1. Login en Railway.app
2. Click "New Project"
3. Seleccionar "Deploy from GitHub repo"
4. Elegir repositorio: nisira-assistant
5. Seleccionar root path: /backend
```

#### Paso 2: Configurar variables de entorno
```bash
# En Railway Dashboard > Variables
DJANGO_SECRET_KEY=tu_clave_secreta_aqui
DEBUG=False
ALLOWED_HOSTS=*.railway.app,localhost
OPENROUTER_API_KEY=tu_clave_openrouter
GOOGLE_API_KEY=tu_clave_google_opcional
DATABASE_URL=${{POSTGRES.DATABASE_URL}}  # Auto-generada
```

#### Paso 3: Crear archivo railway.json en /backend
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt && python manage.py migrate"
  },
  "deploy": {
    "startCommand": "gunicorn core.wsgi:application --bind 0.0.0.0:$PORT",
    "healthcheckPath": "/api/health/",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### Paso 4: Agregar dependencias de producción
Agregar a `requirements.txt`:
```txt
gunicorn==21.2.0
whitenoise==6.6.0
psycopg2-binary==2.9.9
dj-database-url==2.1.0
```

#### Paso 5: Configurar Django para producción
Crear `backend/core/production_settings.py`:
```python
from .settings import *
import dj_database_url

# Seguridad
DEBUG = False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Base de datos
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600
    )
}

# Archivos estáticos
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# CORS para frontend
CORS_ALLOWED_ORIGINS = [
    "https://tu-app.vercel.app",
]

# ChromaDB persistente
CHROMA_DIR = '/app/data/chroma_db'
os.makedirs(CHROMA_DIR, exist_ok=True)
```

#### Paso 6: Deploy
```bash
# Railway detecta cambios automáticamente y despliega
# Esperar 5-10 minutos para el primer deploy
# Ver logs en Railway Dashboard
```

---

### 🎨 PARTE 2: DESPLEGAR FRONTEND EN VERCEL

#### Paso 1: Configurar API URL
Crear `frontend/.env.production`:
```bash
REACT_APP_API_URL=https://tu-backend.railway.app
REACT_APP_WS_URL=wss://tu-backend.railway.app
```

#### Paso 2: Deploy en Vercel
```bash
1. Ir a https://vercel.com/dashboard
2. Click "Add New" > "Project"
3. Importar repositorio: nisira-assistant
4. Configurar:
   - Framework: Create React App
   - Root Directory: frontend
   - Build Command: npm run build
   - Output Directory: build
5. Agregar variables de entorno:
   - REACT_APP_API_URL=https://tu-backend.railway.app
6. Click "Deploy"
```

#### Paso 3: Configurar dominio (opcional)
```bash
1. En Vercel Dashboard > tu proyecto > Settings > Domains
2. Agregar dominio personalizado gratuito: tu-app.vercel.app
```

---

## 🔐 CONFIGURACIÓN DE VARIABLES DE ENTORNO

### Backend (Railway)
```bash
# Obligatorias
DJANGO_SECRET_KEY=genera_una_clave_segura_aqui
OPENROUTER_API_KEY=sk-or-v1-tu-clave-aqui
ALLOWED_HOSTS=*.railway.app,tu-dominio.vercel.app

# Opcionales
DEBUG=False
GOOGLE_API_KEY=tu_clave_google
GROQ_API_KEY=tu_clave_groq
DATABASE_URL=auto  # Railway lo genera
```

### Frontend (Vercel)
```bash
REACT_APP_API_URL=https://tu-backend.railway.app
```

---

## 📦 GESTIÓN DE ChromaDB EN PRODUCCIÓN

### Opción 1: Volumen persistente Railway (Recomendado)
```bash
# En Railway Dashboard:
1. Ir a tu servicio > Settings > Volumes
2. Click "Add Volume"
3. Mount Path: /app/data
4. Size: 1 GB (gratis)
```

### Opción 2: Backup/Restore automático
Crear `backend/management/commands/backup_chroma.py`:
```python
from django.core.management.base import BaseCommand
import os
import shutil
from datetime import datetime

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # Backup ChromaDB a S3/Cloudflare R2 (gratis)
        source = '/app/data/chroma_db'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'/tmp/chroma_backup_{timestamp}.tar.gz'
        
        # Crear tarball
        shutil.make_archive(backup_path[:-7], 'gztar', source)
        
        # Subir a almacenamiento externo
        # ... implementar según proveedor
```

---

## 🚀 COMANDOS ÚTILES

### Generar Django SECRET_KEY
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Ver logs en Railway
```bash
# En Railway Dashboard > tu servicio > Logs
# O usar Railway CLI:
railway logs
```

### Deploy manual
```bash
# Forzar redeploy en Railway
railway up

# Deploy frontend en Vercel
vercel --prod
```

---

## 🐛 TROUBLESHOOTING

### Error: ChromaDB no persiste
```bash
✅ Solución: Agregar volumen persistente en Railway
Settings > Volumes > Add Volume > /app/data
```

### Error: 502 Bad Gateway
```bash
✅ Solución: Verificar gunicorn workers
En railway.json cambiar startCommand a:
"gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 300"
```

### Error: CORS en frontend
```bash
✅ Solución: Agregar dominio Vercel a CORS_ALLOWED_ORIGINS
En production_settings.py:
CORS_ALLOWED_ORIGINS = [
    "https://tu-app.vercel.app",
    "https://tu-app-custom.vercel.app"
]
```

### Error: Embeddings muy lentos
```bash
✅ Solución: Pre-procesar todos los PDFs localmente
Subir ChromaDB completa a Railway usando railway CLI:
railway up --detach
```

---

## 💰 COSTOS ESTIMADOS

### Totalmente Gratis
- Railway: $0/mes (con plan gratuito)
- Vercel: $0/mes (ilimitado)
- ChromaDB: $0 (local)
- Embeddings: $0 (local)
- **ÚNICO COSTO:** OpenRouter API (~$0.10/mes para uso moderado)

### Escalado Futuro
- Railway Pro: $5/mes (más RAM)
- Vercel Pro: $20/mes (más features)
- **Total estimado con Pro:** $25/mes

---

## 📚 RECURSOS ADICIONALES

- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
- Django Production: https://docs.djangoproject.com/en/5.0/howto/deployment/
- ChromaDB Persistence: https://docs.trychroma.com/deployment

---

## ✅ CHECKLIST DE DESPLIEGUE

- [ ] Crear cuentas Railway y Vercel
- [ ] Subir código a GitHub
- [ ] Configurar railway.json
- [ ] Agregar gunicorn a requirements.txt
- [ ] Configurar variables de entorno Railway
- [ ] Deploy backend en Railway
- [ ] Agregar volumen persistente
- [ ] Configurar .env.production frontend
- [ ] Deploy frontend en Vercel
- [ ] Probar endpoints
- [ ] Verificar persistencia ChromaDB
- [ ] Configurar dominio personalizado (opcional)

---

**🎉 ¡Sistema desplegado y funcionando!**

Para soporte: https://github.com/TU_USUARIO/nisira-assistant/issues