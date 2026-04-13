# 🚀 PASOS PARA DESPLEGAR AHORA

## 1. Commit y Push a GitHub (ejecuta estos comandos)

```powershell
cd "c:\Users\amaya\Downloads\10mo Ciclo\nisira-assistant"
git add .
git commit -m "Complete Dockerization for production deployment"
git push origin main
```

## 2. Ir a Digital Ocean

### 2.1 Crear App
1. Ve a https://cloud.digitalocean.com/apps
2. Click **Create App**
3. Selecciona **GitHub** como source
4. Autoriza Digital Ocean a acceder a tu cuenta GitHub
5. Selecciona el repositorio: `SeijiAMG16/nisira-assistant`
6. Branch: `main`
7. Click **Next**

### 2.2 Configurar Services

#### Backend Service:
- **Name**: `backend`
- **Type**: Web Service
- **Dockerfile Path**: `backend/Dockerfile`
- **HTTP Port**: `8000`
- **HTTP Request Routes**: `/api`, `/admin`, `/static`
- **Instance Size**: `Basic (2 GB RAM)` - **IMPORTANTE!**
  - ⚠️ NO uses 1 GB, necesitas 2 GB mínimo por los embeddings
- **Instances**: 1

#### Frontend Service:
- **Name**: `frontend`
- **Type**: Static Site
- **Dockerfile Path**: `frontend/Dockerfile`
- **HTTP Request Routes**: `/`
- **Instance Size**: `Basic (512 MB)`
- **Instances**: 1

### 2.3 Configurar Database
- Click **Add Resource** → **Database**
- **Engine**: PostgreSQL
- **Version**: 16
- **Plan**: `Basic` ($7/month)
- **Datacenter**: El más cercano a ti

Click **Next**

## 3. Variables de Entorno del BACKEND

Click en **backend** service → **Environment Variables** → **Edit**

Copia y pega EXACTAMENTE estas variables (marca las que dicen SECRET como **Encrypted**):

```
DJANGO_SETTINGS_MODULE=core.production_settings
SECRET_KEY=H8kL9mN2pQ4rS6tU7vX9yZ1aB3cD5eF7gH9jK1lM3nP5qR7sT9uV
DEBUG=False
ALLOWED_HOSTS=.ondigitalocean.app,.vercel.app
DATABASE_URL=${db.DATABASE_URL}
PORT=8000
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=300
ENVIRONMENT=production
```

### 🔐 API KEYS (marcar como ENCRYPTED):

```
OPENROUTER_API_KEY=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
GOOGLE_API_KEY=AIzaSyC0V18JMVm8fs3v1BuzBCXOyAITfZuIVw8
GOOGLE_DRIVE_FOLDER_ID=1wAYnaln3Dg-MnFy6rNhwqPlh7Ouc4EP8
```

### 🔑 Google OAuth (marcar como ENCRYPTED y en UNA SOLA LÍNEA):

```
GOOGLE_CREDENTIALS_JSON={"installed":{"client_id":"22562789891-i5fr08se064ifl0dnkn25167j59s54lv.apps.googleusercontent.com","project_id":"nisira-assistance","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"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","redirect_uris":["http://localhost"]}}
```

## 4. Variables de Entorno del FRONTEND

Click en **frontend** service → **Environment Variables** → **Edit**

```
REACT_APP_API_URL=${backend.PUBLIC_URL}
```

## 5. Deploy!

1. Click **Next** → **Review**
2. Verifica que todo esté correcto:
   - ✅ Backend: 2 GB RAM
   - ✅ Frontend: 512 MB RAM
   - ✅ Database: PostgreSQL 16
   - ✅ Total estimado: **$24/month**
3. Click **Create Resources**

## 6. Esperar Deployment (10-15 minutos)

Digital Ocean va a:
1. ✅ Crear la base de datos PostgreSQL
2. ✅ Construir las imágenes Docker
3. ✅ Ejecutar migraciones
4. ✅ Desplegar los servicios

Puedes ver los logs en tiempo real clickeando en cada service.

## 7. Verificar

Una vez que todo esté "Running":

1. Abre la URL de tu app: `https://nisira-assistant-xxxxx.ondigitalocean.app`
2. Verifica que el login funcione
3. Prueba hacer una pregunta al assistant

## 💰 Costos

- Backend (2 GB): $12/month
- Frontend: $5/month
- PostgreSQL: $7/month
- **Total: $24/month**
- **Con tus $200 de créditos estudiantiles: ~8 meses gratis!**

---

## ❓ Si algo falla

**Logs del Backend:**
```
Digital Ocean > Apps > nisira-assistant > backend > Runtime Logs
```

**Problemas comunes:**
1. **Base de datos no conecta**: Verifica que `DATABASE_URL` esté configurada como `${db.DATABASE_URL}`
2. **Migraciones fallan**: Los logs mostrarán el error específico
3. **API keys inválidas**: Verifica que copiaste correctamente sin espacios extras

---

## 🎯 Siguiente paso: Ejecuta el comando de git en la terminal
