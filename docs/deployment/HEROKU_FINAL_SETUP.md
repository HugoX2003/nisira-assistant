# Configuración Final de Heroku (Estrategia Dual)

## 📋 Resumen de la Estrategia

Debido a limitaciones de Git LFS en Heroku, se implementó una **estrategia dual**:

1. **Repositorio principal (GitHub)**: Incluye embeddings precalculados con Git LFS
2. **Rama de Heroku** (`heroku-deploy`): Excluye embeddings, los genera en el primer deploy

---

## 🎯 Estado Actual del Deploy

### ✅ Frontend Desplegado
- **URL**: https://nisira-assistant-frontend-2ae5b156ad38.herokuapp.com/
- **Rama**: `heroku-deploy` (sin archivos LFS)
- **Buildpacks**: 
  - `timanovsky/subdir-heroku-buildpack` (para `frontend/`)
  - `heroku/nodejs`

### ⚠️ Backend Pendiente
El backend debe desplegarse en una plataforma que soporte mejor los embeddings:
- **Opción 1**: DigitalOcean App Platform (con `.do/app.yaml` configurado)
- **Opción 2**: Railway (con soporte nativo de Git LFS)
- **Opción 3**: Render (similar a Railway)

---

## 🚀 Comandos Ejecutados

### 1. Configuración de Buildpacks
```bash
heroku buildpacks:clear
heroku buildpacks:add https://github.com/timanovsky/subdir-heroku-buildpack
heroku buildpacks:add heroku/nodejs
```

### 2. Creación de Rama sin LFS
```bash
git checkout -b heroku-deploy
# Modificar backend/.dockerignore para excluir chroma_db/ y data/documents/
git add backend/.dockerignore
git commit -m "heroku: exclude LFS files, generate embeddings on deploy"
```

### 3. Deploy a Heroku
```bash
git push heroku heroku-deploy:main --force
```

---

## 🔧 Próximos Pasos

### Para el Backend en DigitalOcean

1. **Configurar variables de entorno** en el dashboard de DigitalOcean:
   ```
   GOOGLE_API_KEY=<tu-api-key>
   OPENROUTER_API_KEY=<tu-api-key>
   SECRET_KEY=<tu-secret-key>
   DATABASE_URL=<postgresql-url>
   ENABLE_GOOGLE_DRIVE=false
   ```

2. **Añadir credenciales de Google** (opcional, si activas Drive):
   ```
   GOOGLE_CREDENTIALS_JSON=<contenido-completo-de-credentials.json>
   ```

3. **Conectar repositorio**:
   - Rama: `main` (con LFS configurado)
   - El archivo `.do/app.yaml` ya tiene los comandos de `git lfs fetch`

4. **Deploy automático**: DigitalOcean descargará los embeddings LFS durante el build

---

## 📊 Comparación de Estrategias

| Aspecto | Heroku (rama heroku-deploy) | DigitalOcean (rama main) |
|---------|----------------------------|--------------------------|
| Embeddings | Genera al iniciar | Descarga desde LFS |
| RAM inicial | ~2GB pico | ~500MB |
| Tiempo primer boot | ~10-15 min | ~2-3 min |
| Actualizaciones corpus | Regenerar desde Drive | `git pull` + LFS fetch |
| Complejidad | Media | Baja |

---

## 🐛 Troubleshooting

### Si el backend en DigitalOcean falla con "file is not a database"
Significa que Git LFS no descargó los archivos. Verificar:
```bash
# En el entorno de build de DigitalOcean
git lfs ls-files | head -n 5
# Deberían mostrarse archivos con hash completo, no "Git LFS pointer"
```

Solución: Asegurarse que `.do/app.yaml` tiene:
```yaml
build_command: |
  apt-get update && apt-get install -y git-lfs
  git lfs install
  git lfs fetch --all
  git lfs checkout
```

### Si Heroku se queda sin memoria al generar embeddings
Opciones:
1. Usar dyno de mayor capacidad (Standard 2X: 1GB RAM)
2. Reducir el tamaño del corpus en `backend/data/documents/`
3. Migrar el backend a otra plataforma (recomendado)

---

## 📝 Notas Finales

- La rama `main` en GitHub contiene los embeddings completos con LFS
- La rama `heroku-deploy` es solo para el frontend en Heroku
- **No hacer merge** de `heroku-deploy` a `main` (son estrategias independientes)
- Para actualizar el frontend en Heroku: trabajar en `heroku-deploy` y push
- Para actualizar el backend en DigitalOcean: trabajar en `main` y push

---

## ✅ Deploy Completado

**Frontend**: ✅ Funcionando en Heroku  
**Backend**: ⏳ Pendiente de desplegar en DigitalOcean o alternativa  
**Corpus LFS**: ✅ Subido a GitHub (950 MB en 396 objetos)  
**Documentación**: ✅ Actualizada

🎉 **El sistema está listo para producción dual**: frontend en Heroku, backend en plataforma con LFS.
