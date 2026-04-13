# 🚀 Guía Completa: Despliegue en Digital Ocean App Platform

## ✅ TODO ESTÁ LISTO - Solo Sigue Estos Pasos

### 📋 **Lo Que Ya Está Preparado:**

✅ Dockerfiles optimizados (backend y frontend)
✅ Variables de entorno configuradas
✅ `app.yaml` para Digital Ocean
✅ Base de datos PostgreSQL configurada
✅ Health checks implementados
✅ Credenciales de Google Drive

---

## 🎯 PASO 1: Subir a GitHub (5 minutos)

### 1.1 Inicializar Git (si no lo has hecho)

```bash
cd "c:\Users\amaya\Downloads\10mo Ciclo\nisira-assistant"

# Inicializar repositorio
git init

# Agregar todos los archivos
git add .

# Primer commit
git commit -m "Initial commit - Ready for Digital Ocean"
```

### 1.2 Crear Repositorio en GitHub

1. Ve a https://github.com/new
2. **Repository name**: `nisira-assistant`
3. **Description**: Sistema RAG con Google Drive
4. **Visibility**: **Private** (recomendado para API keys)
5. Click **Create repository**

### 1.3 Subir el Código

```bash
# Conectar con GitHub (reemplaza con tu usuario)
git remote add origin https://github.com/HugoX2003/nisira-assistant.git

# Subir código
git branch -M main
git push -u origin main
```

✅ **Verificar:** Tu código debe estar en GitHub ahora

---

## 🌊 PASO 2: Crear Cuenta en Digital Ocean (2 minutos)

### 2.1 Registrarse

1. Ve a https://www.digitalocean.com
2. Click **Sign Up**
3. Usa tu email de estudiante (.edu) para obtener créditos gratis

### 2.2 Aplicar Créditos de Estudiante

1. Ve a https://www.digitalocean.com/github-students
2. Conecta tu cuenta de GitHub
3. Obtendrás **$200 en créditos** (válidos por 1 año)

✅ **Verificar:** Debes ver "$200.00" en tu billing

---

## 🚀 PASO 3: Desplegar en App Platform (10 minutos)

### 3.1 Crear Nueva App

1. En Digital Ocean, click **Create > Apps**
2. Click **Launch Your App**

### 3.2 Conectar GitHub

1. **Source Provider**: GitHub
2. Click **Manage Access**
3. Autoriza Digital Ocean en GitHub
4. Selecciona tu repositorio: `HugoX2003/nisira-assistant`
5. **Branch**: `main`
6. Click **Next**

### 3.3 Configurar Recursos

Digital Ocean detectará automáticamente tus Dockerfiles. Configuración:

#### **Backend Service:**
- **Name**: `backend`
- **Type**: Web Service
- **Dockerfile Path**: `backend/Dockerfile`
- **HTTP Port**: `8000`
- **Instance Size**: Basic ($5/mes) - suficiente para empezar
- **Instance Count**: 1

#### **Frontend Service:**
- **Name**: `frontend`
- **Type**: Static Site
- **Dockerfile Path**: `frontend/Dockerfile`
- **Output Directory**: `build`
- **Instance Size**: Basic ($5/mes)

### 3.4 Agregar Base de Datos

1. Click **Add Resource > Database**
2. **Engine**: PostgreSQL
3. **Version**: 16
4. **Plan**: Basic ($7/mes)
5. **Name**: `db`
6. Digital Ocean creará automáticamente la variable `${db.DATABASE_URL}`

### 3.5 Configurar Variables de Entorno

En el backend, agrega estas variables (click **Edit** en backend > **Environment Variables**):

```bash
# Django
DJANGO_SETTINGS_MODULE=core.production_settings
SECRET_KEY=H8kL9mN2pQ4rS6tU7vX9yZ1aB3cD5eF7gH9jK1lM3nP5qR7sT9uV  # Marcar como SECRET
DEBUG=False

# Database (auto-generada por Digital Ocean)
DATABASE_URL=${db.DATABASE_URL}

# APIs (marcar como SECRET)
OPENROUTER_API_KEY=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
GOOGLE_API_KEY=AIzaSyC0V18JMVm8fs3v1BuzBCXOyAITfZuIVw8
GOOGLE_DRIVE_FOLDER_ID=1wAYnaln3Dg-MnFy6rNhwqPlh7Ouc4EP8

# Gunicorn
PORT=8000
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=300
```

En el frontend:

```bash
REACT_APP_API_URL=${backend.PUBLIC_URL}
```

### 3.6 Configurar credentials.json

**⚠️ IMPORTANTE:** `credentials.json` no debe estar en Git por seguridad.

**Opción 1: Variable de Entorno (Recomendado)**
1. En backend > Environment Variables
2. Agregar: `GOOGLE_CREDENTIALS_JSON`
3. Pegar el contenido COMPLETO de tu `credentials.json`
4. Marcar como **SECRET**

**Opción 2: Usar Digital Ocean Spaces (Avanzado)**
Subir `credentials.json` a un bucket privado y descargarlo en runtime.

### 3.7 Lanzar

1. **App Info**:
   - **Name**: `nisira-assistant`
   - **Region**: New York (más cercana)
2. **Review**: Verifica todo
3. Click **Create Resources**

🎉 Digital Ocean empezará a construir y desplegar tu app!

---

## ⏳ PASO 4: Esperar el Despliegue (5-10 minutos)

Digital Ocean hará automáticamente:

1. ✅ Clonar tu repositorio
2. ✅ Construir imágenes Docker
3. ✅ Crear base de datos PostgreSQL
4. ✅ Ejecutar migraciones (`python manage.py migrate`)
5. ✅ Configurar SSL/HTTPS
6. ✅ Asignar dominio: `https://nisira-assistant-xxxxx.ondigitalocean.app`

**Ver progreso:**
- Click en tu app
- Ver **Deployment Logs** (logs en tiempo real)

---

## ✅ PASO 5: Verificar que Funciona (2 minutos)

### 5.1 URLs de tu App

Digital Ocean te dará URLs como:

- **Frontend**: `https://nisira-assistant-xxxxx.ondigitalocean.app`
- **Backend**: `https://backend-xxxxx.ondigitalocean.app`

### 5.2 Probar Endpoints

```bash
# Health check
curl https://backend-xxxxx.ondigitalocean.app/api/health/

# Deberías ver: {"status": "healthy"}
```

### 5.3 Probar en el Navegador

1. Abre tu frontend URL
2. Intenta registrarte
3. Haz login
4. Prueba el chat

✅ **Si todo funciona:** ¡Felicidades! Tu app está en producción 🎉

---

## 🔧 PASO 6: Configuración Adicional (Opcional)

### 6.1 Dominio Personalizado

Si tienes tu propio dominio:

1. En Digital Ocean > Settings > Domains
2. Click **Add Domain**
3. Ingresa: `tu-dominio.com`
4. Agrega estos registros DNS en tu proveedor:

```
Tipo: A
Nombre: @
Valor: [IP de Digital Ocean]

Tipo: CNAME
Nombre: www
Valor: nisira-assistant-xxxxx.ondigitalocean.app
```

### 6.2 Auto-Deploy

Ya está configurado! Cada vez que hagas `git push` a `main`, Digital Ocean re-desplegará automáticamente.

```bash
# Hacer cambios
git add .
git commit -m "Update feature"
git push origin main

# Digital Ocean detecta el push y re-despliega automáticamente
```

### 6.3 Monitoreo

En Digital Ocean > Insights:
- Ver CPU/RAM usage
- Ver requests por segundo
- Ver logs en tiempo real

---

## 💰 Costos Estimados (con tus $200 de créditos)

- **Backend**: $5/mes
- **Frontend**: $5/mes
- **PostgreSQL**: $7/mes
- **Bandwidth**: Gratis hasta 1TB
- **SSL**: Gratis
- **TOTAL**: ~$17/mes

Con $200 de créditos = **~11 meses gratis** 🎉

---

## 🐛 Troubleshooting

### Backend no inicia

```bash
# Ver logs
Digital Ocean > Apps > nisira-assistant > backend > Logs

# Común: Falta variable de entorno
# Solución: Verificar Environment Variables
```

### Frontend no puede conectar al backend

```bash
# Verificar REACT_APP_API_URL
# Debe ser: ${backend.PUBLIC_URL}

# Si no funciona, usar la URL completa:
REACT_APP_API_URL=https://backend-xxxxx.ondigitalocean.app
```

### Migraciones fallan

```bash
# Conectar a la base de datos
Digital Ocean > Databases > db > Connection Details

# Ejecutar migraciones manualmente desde Console
```

### credentials.json no encontrado

```bash
# Opción 1: Agregar como variable de entorno
GOOGLE_CREDENTIALS_JSON={contenido del json}

# Opción 2: Modificar código para leer de variable
import os
import json

creds = json.loads(os.getenv('GOOGLE_CREDENTIALS_JSON'))
```

---

## 📊 Comandos Útiles

### Ver Logs en Tiempo Real

1. Digital Ocean > Apps > nisira-assistant
2. Click en **Runtime Logs**
3. Selecciona servicio (backend/frontend)

### Acceder a Consola

1. Digital Ocean > Apps > nisira-assistant > backend
2. Click **Console**
3. Ejecutar comandos Django:

```bash
python manage.py shell
python manage.py createsuperuser
python manage.py dbshell
```

### Reiniciar Servicios

1. Digital Ocean > Apps > nisira-assistant
2. Click **Actions > Force Rebuild and Deploy**

---

## 🎯 Resumen de URLs

Después del despliegue tendrás:

- ✅ **Frontend**: https://nisira-assistant-xxxxx.ondigitalocean.app
- ✅ **Backend API**: https://backend-xxxxx.ondigitalocean.app/api/
- ✅ **Admin Django**: https://backend-xxxxx.ondigitalocean.app/api/admin/
- ✅ **Health Check**: https://backend-xxxxx.ondigitalocean.app/api/health/
- ✅ **PostgreSQL**: Acceso interno automático

---

## 🎉 ¡Felicidades!

Tu aplicación Nisira Assistant ahora está:
- ✅ En producción en Digital Ocean
- ✅ Con HTTPS/SSL automático
- ✅ Con base de datos PostgreSQL
- ✅ Con auto-deploy desde GitHub
- ✅ Con monitoreo integrado
- ✅ Escalable y profesional

**Próximos pasos:**
1. Compartir la URL con usuarios
2. Monitorear uso y logs
3. Escalar recursos si es necesario
4. Agregar dominio personalizado

---

**¿Dudas?** Revisa los logs en Digital Ocean o contacta su soporte (excelente para estudiantes).
