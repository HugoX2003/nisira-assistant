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
SECRET_KEY=H8kL9mN2pQ4rS6tU7vX9yZ1aB3cD5eF7gH9jK1lM3nP5qR7sT9uV
DEBUG=False
OPENROUTER_API_KEY=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
GOOGLE_API_KEY=AIzaSyC0V18JMVm8fs3v1BuzBCXOyAITfZuIVw8
GOOGLE_DRIVE_FOLDER_ID=1wAYnaln3Dg-MnFy6rNhwqPlh7Ouc4EP8
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
