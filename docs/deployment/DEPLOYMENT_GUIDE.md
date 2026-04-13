# 🚀 GUÍA DE DESPLIEGUE - NISIRA ASSISTANT
## Backend (Digital Ocean) + Frontend (Heroku)

---

## 📦 BACKEND - DIGITAL OCEAN

### App Digital Ocean: `nisira-assistant`
**URL:** https://nisira-assistant-8dq2a.ondigitalocean.app

### Configuración en Digital Ocean:

1. **Source → GitHub:**
   - Repository: `HugoX2003/nisira-assistant`
   - Branch: `main`
   - Auto-deploy: ✅ Habilitado

2. **Settings → App-Level → Resources:**
   - **Source Directory:** `/backend`  ⚠️ **IMPORTANTE: Configurar esto**
   - **Dockerfile Path:** `backend/Dockerfile`
   
3. **Environment Variables (ya configuradas):**
   ```
   DJANGO_SETTINGS_MODULE=core.production_settings
   SECRET_KEY=<tu-secret-key>
   DATABASE_URL=${db.DATABASE_URL}
   GOOGLE_CREDENTIALS_JSON=<json-completo>
   ALLOWED_HOSTS=.ondigitalocean.app
   DEBUG=False
   PORT=8000
   GUNICORN_WORKERS=2
   GUNICORN_TIMEOUT=300
   ```

4. **Health Check:**
   - Path: `/api/health/`
   - Port: 8000

---

## 🎨 FRONTEND - HEROKU

### App Heroku: `nisira-assistant-frontend`
**URL:** https://nisira-assistant-frontend.herokuapp.com
**Dashboard:** https://dashboard.heroku.com/apps/nisira-assistant-frontend

### Configuración en Heroku:

#### 1. Conectar GitHub:
```bash
# En el Dashboard de Heroku:
Deploy → Deployment method → GitHub
→ Connect to GitHub
→ Buscar: "HugoX2003/nisira-assistant"
→ Connect
→ Enable Automatic Deploys (branch: main)
```

#### 2. Configurar Buildpacks:
```bash
# En Settings → Buildpacks → Add buildpack:
1. heroku/nodejs
```

#### 3. Configurar App Directory:
```bash
# En Settings → Config Vars → Añadir:
APP_BASE = frontend
```

O en terminal:
```bash
heroku login
heroku git:remote -a nisira-assistant-frontend
heroku config:set APP_BASE=frontend
```

#### 4. Variables de Entorno (Config Vars):
```bash
# En Settings → Config Vars → Añadir:
REACT_APP_API_URL = https://nisira-assistant-8dq2a.ondigitalocean.app/api
REACT_APP_API_BASE = https://nisira-assistant-8dq2a.ondigitalocean.app
GENERATE_SOURCEMAP = false
NODE_ENV = production
```

O en terminal:
```bash
heroku config:set REACT_APP_API_URL=https://nisira-assistant-8dq2a.ondigitalocean.app/api
heroku config:set REACT_APP_API_BASE=https://nisira-assistant-8dq2a.ondigitalocean.app
heroku config:set GENERATE_SOURCEMAP=false
heroku config:set NODE_ENV=production
```

#### 5. Configurar subdirectorio (si no está configurado):

**Opción A - Usando Heroku CLI:**
```bash
cd "c:\Users\amaya\Downloads\10mo Ciclo\nisira-assistant"
git subtree push --prefix frontend heroku main
```

**Opción B - Configurar monorepo en Heroku:**
Crear `heroku.yml` en el root del proyecto:
```yaml
build:
  languages:
    - nodejs
  config:
    NODE_ENV: production
    NPM_CONFIG_PRODUCTION: false
  docker:
    web:
      dockerfile: frontend/Dockerfile
      target: production
run:
  web: cd frontend && serve -s build -l $PORT
```

**Opción C - Usar buildpack subdir (RECOMENDADO):**
```bash
heroku buildpacks:add -a nisira-assistant-frontend https://github.com/timanovsky/subdir-heroku-buildpack
heroku buildpacks:add -a nisira-assistant-frontend heroku/nodejs
heroku config:set PROJECT_PATH=frontend -a nisira-assistant-frontend
```

---

## 🔄 PASOS PARA DESPLEGAR

### 1. Backend (Digital Ocean) - YA CONFIGURADO ✅
El backend se desplegará automáticamente cuando pushees a `main`.

**Verificar que esté configurado:**
- Ve a Digital Ocean Dashboard
- nisira-assistant → Settings → App-Level
- **Source Directory:** Debe ser `/backend`
- Si no está configurado, edítalo y guarda

### 2. Frontend (Heroku) - CONFIGURAR AHORA

#### Paso 1: Conectar GitHub en Heroku
1. Ve a: https://dashboard.heroku.com/apps/nisira-assistant-frontend
2. Click en tab **"Deploy"**
3. En "Deployment method" → Click **"GitHub"**
4. Click **"Connect to GitHub"**
5. Busca: `nisira-assistant`
6. Click **"Connect"**
7. Scroll down y click **"Enable Automatic Deploys"** (branch: main)

#### Paso 2: Configurar buildpack para subdirectorio
```bash
# Abre PowerShell/Terminal y ejecuta:
cd "c:\Users\amaya\Downloads\10mo Ciclo\nisira-assistant"

# Login a Heroku
heroku login

# Conectar el remote de Heroku
heroku git:remote -a nisira-assistant-frontend

# Agregar buildpack para subdirectorio
heroku buildpacks:add https://github.com/timanovsky/subdir-heroku-buildpack

# Agregar buildpack de Node.js
heroku buildpacks:add heroku/nodejs

# Configurar el subdirectorio
heroku config:set PROJECT_PATH=frontend

# Configurar variables de entorno
heroku config:set REACT_APP_API_URL=https://nisira-assistant-8dq2a.ondigitalocean.app/api
heroku config:set REACT_APP_API_BASE=https://nisira-assistant-8dq2a.ondigitalocean.app
heroku config:set GENERATE_SOURCEMAP=false

# Forzar un deploy
git commit --allow-empty -m "Trigger Heroku deploy"
git push origin main
```

#### Paso 3: Verificar deployment
```bash
# Ver logs de Heroku en tiempo real
heroku logs --tail -a nisira-assistant-frontend

# Verificar que esté corriendo
heroku ps -a nisira-assistant-frontend

# Abrir en navegador
heroku open -a nisira-assistant-frontend
```

---

## 🧪 TESTING

### Backend (Digital Ocean):
```bash
# Health check
curl https://nisira-assistant-8dq2a.ondigitalocean.app/api/health/

# API info
curl https://nisira-assistant-8dq2a.ondigitalocean.app/api/

# RAG status
curl https://nisira-assistant-8dq2a.ondigitalocean.app/api/rag/status/
```

### Frontend (Heroku):
```bash
# Abrir en navegador
https://nisira-assistant-frontend.herokuapp.com

# Verificar que cargue la página de login
# Verificar que pueda hacer registro
# Verificar que pueda hacer login
# Verificar que pueda hacer consultas al backend
```

---

## 🔍 TROUBLESHOOTING

### Backend no responde:
```bash
# Ver logs de Digital Ocean
# En dashboard → Runtime Logs
```

### Frontend muestra error de conexión:
```bash
# Verificar variables de entorno
heroku config -a nisira-assistant-frontend

# Verificar buildpacks
heroku buildpacks -a nisira-assistant-frontend

# Debería mostrar:
# 1. https://github.com/timanovsky/subdir-heroku-buildpack
# 2. heroku/nodejs
```

### Frontend no despliega (subdirectorio):
```bash
# Opción alternativa: push manual del subdirectorio
cd "c:\Users\amaya\Downloads\10mo Ciclo\nisira-assistant"
git subtree push --prefix frontend https://git.heroku.com/nisira-assistant-frontend.git main
```

---

## 📝 CHECKLIST

### Digital Ocean (Backend):
- [x] Repository conectado
- [ ] **Source Directory = `/backend`** ⚠️ VERIFICAR ESTO
- [x] Variables de entorno configuradas
- [x] Auto-deploy habilitado
- [ ] Health check OK

### Heroku (Frontend):
- [ ] Repository conectado
- [ ] Buildpack subdirectorio agregado
- [ ] Buildpack Node.js agregado
- [ ] Variable PROJECT_PATH=frontend
- [ ] Variables REACT_APP_API_URL configuradas
- [ ] Auto-deploy habilitado
- [ ] App corriendo OK

---

## 🎯 RESULTADO ESPERADO

**Backend (Digital Ocean):**
- ✅ https://nisira-assistant-8dq2a.ondigitalocean.app/api/ → JSON con info de API
- ✅ https://nisira-assistant-8dq2a.ondigitalocean.app/admin/ → Django Admin
- ✅ https://nisira-assistant-8dq2a.ondigitalocean.app/api/health/ → Status OK

**Frontend (Heroku):**
- ✅ https://nisira-assistant-frontend.herokuapp.com/ → Página de Login/Register
- ✅ Puede conectarse al backend y hacer queries
- ✅ Chat funcional con RAG

---

## 🚨 IMPORTANTE

1. **Digital Ocean:** Asegúrate de configurar **Source Directory = `/backend`** en Settings
2. **Heroku:** Debes configurar el buildpack de subdirectorio ANTES de hacer deploy
3. **CORS:** Ya está configurado en backend para aceptar requests de Heroku
4. **API Keys:** Las variables de entorno ya están en Digital Ocean

---

## 📞 COMANDOS ÚTILES

```bash
# Ver logs de Heroku en tiempo real
heroku logs --tail -a nisira-assistant-frontend

# Ver status de Heroku
heroku ps -a nisira-assistant-frontend

# Reiniciar dyno de Heroku
heroku restart -a nisira-assistant-frontend

# Ver variables de entorno
heroku config -a nisira-assistant-frontend

# Ejecutar comando en Heroku
heroku run bash -a nisira-assistant-frontend
```

---

¡Todo listo! Ahora solo necesitas seguir los pasos de configuración en Heroku. 🚀
