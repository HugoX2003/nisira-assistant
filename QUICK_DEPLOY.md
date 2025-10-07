# 🚀 Despliegue Rápido - Nisira Assistant

## ⚡ Despliegue en 10 minutos

### 1️⃣ Backend en Railway (5 min)

```bash
# 1. Crear cuenta en Railway.app
https://railway.app

# 2. New Project > Deploy from GitHub > nisira-assistant

# 3. Variables de entorno (Settings > Variables):
DJANGO_SECRET_KEY=genera_con_comando_abajo
OPENROUTER_API_KEY=tu_clave_openrouter
ALLOWED_HOSTS=*.railway.app
DEBUG=False

# 4. Agregar volumen (Settings > Volumes):
Mount Path: /app/data
Size: 1GB

# 5. Deploy automático ✅
```

**Generar SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2️⃣ Frontend en Vercel (3 min)

```bash
# 1. Crear cuenta en Vercel.com
https://vercel.com

# 2. New Project > Import nisira-assistant

# 3. Configuración:
Root Directory: frontend
Framework: Create React App
Build Command: npm run build
Output Directory: build

# 4. Variables de entorno:
REACT_APP_API_URL=https://tu-backend.railway.app

# 5. Deploy ✅
```

### 3️⃣ Verificar (2 min)

```bash
# Backend health check
curl https://tu-backend.railway.app/api/health/

# Frontend
https://tu-app.vercel.app
```

## 💰 Costo Total

- Railway: **$0/mes** (plan gratuito)
- Vercel: **$0/mes** (ilimitado)
- OpenRouter: **~$0.10/mes** (uso moderado)

**Total: $0.10/mes** 🎉

## 📚 Documentación Completa

Ver `DEPLOYMENT_GUIDE.md` para guía detallada.

## 🐛 Troubleshooting

### ChromaDB no persiste
✅ Agregar volumen en Railway: Settings > Volumes > /app/data

### Error 502
✅ Aumentar timeout en railway.json a 300s

### CORS error
✅ Agregar dominio Vercel a CORS_ALLOWED_ORIGINS en production_settings.py

## 🔗 Enlaces Útiles

- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
- Soporte: GitHub Issues