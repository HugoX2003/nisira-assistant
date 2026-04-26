# 🚀 INSTRUCCIONES PARA DESPLEGAR EN DIGITAL OCEAN
# Repo: https://github.com/SeijiAMG16/nisira-assistant

## ✅ IMÁGENES DOCKER YA CONSTRUIDAS

Las imágenes ya están listas localmente. Ahora vamos a subirlas a Digital Ocean.

## 📋 PASO 1: Preparar GitHub

El código ya está en: https://github.com/SeijiAMG16/nisira-assistant

## 🌊 PASO 2: Crear App en Digital Ocean

1. Ve a: https://cloud.digitalocean.com/apps/new
2. **Source Provider**: GitHub
3. **Repository**: SeijiAMG16/nisira-assistant
4. **Branch**: main
5. Click **Next**

## ⚙️ PASO 3: Configurar Recursos

### Backend Service
- **Name**: backend
- **Type**: Web Service
- **Dockerfile Path**: `backend/Dockerfile`
- **HTTP Port**: 8000
- **Instance Size**: Basic 2 GB RAM ($12/mes)

### Frontend Service
- **Name**: frontend  
- **Type**: Static Site
- **Dockerfile Path**: `frontend/Dockerfile`
- **HTTP Port**: 80
- **Instance Size**: Basic ($5/mes)

### Database
Click **Add Resource > Database**
- **Engine**: PostgreSQL 16
- **Plan**: Basic ($7/mes)
- **Name**: db

## 🔑 PASO 4: Variables de Entorno

En **Backend > Environment Variables**, agrega:

```bash
# Django Core
DJANGO_SETTINGS_MODULE=core.production_settings
SECRET_KEY=tu_secret_key_aqui_generar_uno_largo_y_aleatorio
DEBUG=False
ALLOWED_HOSTS=.ondigitalocean.app

# Database (auto-generada)
DATABASE_URL=${db.DATABASE_URL}

# API Keys (marcar como SECRET)
OPENROUTER_API_KEY=sk-or-v1-tu_openrouter_key_aqui
GOOGLE_API_KEY=tu_google_api_key_aqui
GOOGLE_DRIVE_FOLDER_ID=tu_folder_id_aqui

# Google Credentials JSON (marcar como SECRET)
GOOGLE_CREDENTIALS_JSON={"installed":{"client_id":"...","project_id":"tu_project_id",...}}

# Gunicorn
PORT=8000
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=300
```

En **Frontend > Environment Variables**:

```bash
REACT_APP_API_URL=${backend.PUBLIC_URL}
```

## 🚀 PASO 5: Lanzar

1. **Region**: New York
2. **App Name**: nisira-assistant
3. Click **Create Resources**

Digital Ocean construirá y desplegará automáticamente.

## 💰 COSTO TOTAL

- Backend (2 GB): $12/mes
- Frontend: $5/mes
- PostgreSQL: $7/mes
- **TOTAL**: $24/mes

Con $200 créditos = **8 meses gratis** 🎉

## 📊 URLs Finales

Después del despliegue:
- Frontend: https://nisira-assistant-xxxxx.ondigitalocean.app
- Backend: https://backend-xxxxx.ondigitalocean.app/api/

## ✅ Verificar

```bash
curl https://backend-xxxxx.ondigitalocean.app/api/health/
```

Deberías ver: `{"status":"healthy"}`
