# 🚀 DESPLIEGUE INMEDIATO - 3 Comandos

## ✅ Todo está listo. Solo ejecuta:

### 1️⃣ Subir a GitHub (2 minutos)

```bash
cd "c:\Users\amaya\Downloads\10mo Ciclo\nisira-assistant"

git init
git add .
git commit -m "Initial commit - Ready for Digital Ocean"
git remote add origin https://github.com/HugoX2003/nisira-assistant.git
git push -u origin main
```

### 2️⃣ Digital Ocean (10 minutos)

1. Ve a https://cloud.digitalocean.com/apps
2. Click **Create App**
3. Conecta GitHub > Selecciona `nisira-assistant`
4. Digital Ocean detectará automáticamente los Dockerfiles
5. Agrega estas variables de entorno en el backend:

```bash
SECRET_KEY=tu_secret_key_aqui_generar_uno_largo_y_aleatorio
DEBUG=False
OPENROUTER_API_KEY=sk-or-v1-tu_openrouter_key_aqui
GOOGLE_API_KEY=tu_google_api_key_aqui
GOOGLE_DRIVE_FOLDER_ID=tu_folder_id_aqui
DATABASE_URL=${db.DATABASE_URL}
PORT=8000
GUNICORN_WORKERS=2
```

6. Agrega PostgreSQL: Click **Add Resource > Database > PostgreSQL**
7. Click **Create Resources**

### 3️⃣ ¡Listo! (5 minutos de espera)

Digital Ocean te dará una URL como:
```
https://nisira-assistant-xxxxx.ondigitalocean.app
```

---

## 📚 Guías Detalladas

- **DIGITAL_OCEAN_GUIDE.md** - Guía completa paso a paso
- **DEPLOYMENT_CHECKLIST.md** - Checklist con verificaciones
- **DEPLOYMENT.md** - Alternativa con Droplets

---

## 💰 Costos con $200 de Créditos

- Backend: $5/mes
- Frontend: $5/mes
- PostgreSQL: $7/mes
- **Total**: $17/mes = **~11 meses gratis** 🎉

---

## 🎯 Características

✅ Dockerizado completamente
✅ Auto-deploy desde GitHub
✅ SSL/HTTPS automático
✅ PostgreSQL administrada
✅ Health checks
✅ Monitoreo integrado
✅ Escalable

---

**¿Dudas?** Lee `DIGITAL_OCEAN_GUIDE.md`
