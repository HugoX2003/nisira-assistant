# Nisira Assistant - Sistema RAG con Google Drive

Sistema inteligente de asistencia académica que procesa documentos desde Google Drive usando RAG (Retrieval-Augmented Generation).

## 🚀 Características

- 📚 **Procesamiento automático de PDFs** desde Google Drive
- 🤖 **Chat inteligente** con IA (Gemini/OpenRouter)
- 🔍 **Búsqueda semántica** con ChromaDB
- 📊 **Métricas y evaluación** de calidad de respuestas
- 👥 **Sistema de usuarios** con JWT
- ⭐ **Ratings y feedback** de usuarios
- 🐳 **Completamente dockerizado**

## 🛠️ Stack Tecnológico

### Backend
- Django 5.2 + DRF
- PostgreSQL (producción) / MySQL (desarrollo)
- ChromaDB (base de datos vectorial)
- LangChain + Google Gemini / OpenRouter
- HuggingFace Embeddings (all-mpnet-base-v2)

### Frontend
- React 18
- Axios
- CSS moderno

### Infraestructura
- Docker + Docker Compose
- Nginx (reverse proxy)
- Gunicorn (WSGI server)

## 📦 Instalación

### Desarrollo Local

1. **Clonar repositorio**
```bash
git clone https://github.com/tu-usuario/nisira-assistant.git
cd nisira-assistant
```

2. **Configurar variables de entorno**
```bash
cp backend/.env.example backend/.env
# Editar backend/.env con tus API keys
```

3. **Iniciar con Docker**
```bash
docker-compose up -d --build
```

4. **Acceder a la aplicación**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/
- Admin Django: http://localhost:8000/api/admin/

### Producción (Digital Ocean)

Ver [DEPLOYMENT.md](./DEPLOYMENT.md) para instrucciones detalladas.

**Resumen rápido:**

```bash
# En el servidor
cd /opt
git clone https://github.com/tu-usuario/nisira-assistant.git
cd nisira-assistant

# Configurar
cp .env.production.example .env.production
nano .env.production

# Desplegar
chmod +x deploy.sh
./deploy.sh
```

## 🔑 Configuración

### Variables de Entorno Requeridas

```bash
# Django
SECRET_KEY=tu-clave-secreta
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com

# Base de datos
DATABASE_URL=postgresql://user:pass@host:5432/db

# APIs
OPENROUTER_API_KEY=sk-or-v1-xxxxx
GOOGLE_API_KEY=AIzaSyxxxxx
GOOGLE_DRIVE_FOLDER_ID=xxxxx

# Frontend
REACT_APP_API_URL=https://tu-dominio.com
```

### Credenciales de Google Drive

1. Crear proyecto en [Google Cloud Console](https://console.cloud.google.com)
2. Habilitar Google Drive API
3. Crear credenciales OAuth 2.0 (Desktop app)
4. Descargar `credentials.json` y colocarlo en `backend/`

## 📚 Documentación

- [Guía de Despliegue](./DEPLOYMENT.md)
- [Comandos Docker](./DOCKER_COMMANDS.md)
- [Optimizaciones](./backend/OPTIMIZACIONES.md)
- [Informe Técnico](./backend/INFORME_TECNICO.md)

## 🔧 Comandos Útiles

### Desarrollo
```bash
# Ver logs
docker-compose logs -f

# Reiniciar servicio
docker-compose restart backend

# Entrar al contenedor
docker-compose exec backend bash

# Ejecutar migraciones
docker-compose exec backend python manage.py migrate

# Crear superusuario
docker-compose exec backend python manage.py createsuperuser
```

### Producción
```bash
# Ver logs
docker compose -f docker-compose.production.yml logs -f

# Reiniciar
docker compose -f docker-compose.production.yml restart

# Backup BD
docker compose -f docker-compose.production.yml exec db pg_dump -U postgres rag_asistente > backup.sql
```

## 🏗️ Estructura del Proyecto

```
nisira-assistant/
├── backend/                 # Django Backend
│   ├── api/                # REST API
│   ├── core/               # Configuración Django
│   ├── rag_system/         # Sistema RAG
│   │   ├── document_processing/
│   │   ├── embeddings/
│   │   ├── vector_store/
│   │   ├── rag_engine/
│   │   └── drive_sync/
│   ├── data/               # Documentos y datos
│   └── chroma_db/          # Base de datos vectorial
├── frontend/               # React Frontend
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── styles/
│   └── public/
├── nginx/                  # Configuración Nginx
├── docker-compose.yml      # Desarrollo
├── docker-compose.production.yml  # Producción
└── deploy.sh              # Script de despliegue
```

## 🐛 Troubleshooting

### Backend no conecta a la BD
```bash
# Verificar conexión
docker-compose exec backend python manage.py dbshell
```

### Frontend no puede acceder al backend
Verificar `REACT_APP_API_URL` en `.env` o `.env.production`

### ChromaDB vacío
```bash
# Inicializar RAG
docker-compose exec backend python manage.py rag_manage init
```

### Errores de permisos
```bash
# Fix permisos en volúmenes
sudo chown -R 1000:1000 backend/data backend/chroma_db
```

## 📊 Métricas y Monitoreo

- **QueryMetrics**: Latencia, tokens, costos
- **Ratings**: Valoraciones de usuarios
- **Health Check**: `/api/health/`

## 🔐 Seguridad

- JWT para autenticación
- CORS configurado
- Variables de entorno para secretos
- HTTPS recomendado (Certbot + Let's Encrypt)
- Usuario no-root en contenedores

## 📦 Despliegue con Git LFS (Embeddings Precalculados)

Este proyecto usa **Git LFS** para almacenar embeddings y documentos precalculados (~950 MB), evitando regenerarlos en cada deploy y ahorrando RAM/CPU.

### ⚙️ DigitalOcean App Platform

El archivo `.do/app.yaml` ya incluye los comandos necesarios. Al hacer deploy:

1. DigitalOcean detectará `.do/app.yaml` automáticamente
2. Instalará Git LFS antes del build
3. Descargará los embeddings (`backend/chroma_db/`)
4. Tu app arrancará con los datos listos ✅

**Variables de entorno requeridas:**
```
ENABLE_GOOGLE_DRIVE=false
GOOGLE_API_KEY=tu_api_key
OPENROUTER_API_KEY=tu_api_key (opcional)
SECRET_KEY=tu_secret_django
```

### 🟣 Heroku

Heroku requiere un buildpack adicional para Git LFS. Ver instrucciones detalladas en [HEROKU_LFS_SETUP.md](./HEROKU_LFS_SETUP.md).

**Resumen rápido:**

```bash
# Añadir buildpack de Git LFS (ANTES del de Python)
heroku buildpacks:add --index 1 https://github.com/raxod502/heroku-buildpack-git-lfs

# Verificar orden
heroku buildpacks

# Deploy
git push heroku main
```

### 🔍 Verificar que LFS funcionó

Después del deploy, confirma que los embeddings se descargaron:

```bash
# DigitalOcean
doctl apps logs <app-id> --type build | grep "LFS"

# Heroku
heroku run bash
file /app/backend/chroma_db/chroma.sqlite3  # Debe decir "SQLite 3.x database"
```

Si dice `ASCII text`, los objetos LFS no se descargaron. Revisa que el buildpack/comando LFS esté configurado.

### 🚨 Importante: Historia Git Reescrita

El proyecto migró a Git LFS, lo que reescribió la historia de `main`. Si tienes un clon local:

```bash
# Actualizar tu clon local
git fetch --all
git reset --hard origin/main
git lfs install
git lfs pull
```

O reclonar:

```bash
git clone https://github.com/HugoX2003/nisira-assistant.git
cd nisira-assistant
git lfs install
git lfs pull
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama: `git checkout -b feature/nueva-caracteristica`
3. Commit: `git commit -m 'Add nueva caracteristica'`
4. Push: `git push origin feature/nueva-caracteristica`
5. Abrir Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver [LICENSE](LICENSE)

## 👥 Autores

- **Hugo Amaya** - [HugoX2003](https://github.com/HugoX2003)

## 🙏 Agradecimientos

- LangChain por el framework RAG
- OpenRouter por el acceso a modelos LLM
- Google por Gemini API
- HuggingFace por embeddings gratuitos

---

**¿Necesitas ayuda?** Abre un [Issue](https://github.com/tu-usuario/nisira-assistant/issues)
