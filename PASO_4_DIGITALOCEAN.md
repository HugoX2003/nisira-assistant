# 🚀 PASO 4: Configurar DigitalOcean (CRÍTICO)

## ✅ Cambios Completados en el Código

1. ✅ **Git LFS deshabilitado** - Las carpetas `backend/data/` y `backend/chroma_db/` están ignoradas
2. ✅ **Drive Manager corregido** - Ahora acepta Service Account correctamente
3. ✅ **RAG init activado** - El servidor generará embeddings al iniciar
4. ✅ **Código subido** a GitHub (origin y myfork)

---

## 🎯 PASO CRÍTICO: Configurar Tiempo y Memoria en DigitalOcean

**⚠️ ESTO ES LO MÁS IMPORTANTE - Sin esto, el servidor fallará otra vez**

### Opción A: Desde el Dashboard (Más Fácil)

1. **Ve a DigitalOcean App Platform**:
   - URL: https://cloud.digitalocean.com/apps

2. **Selecciona tu app** `nisira-assistant`

3. **⚙️ Ir a Settings (Configuración)**

4. **Editar el componente Backend**:
   - Busca el componente `nisira-assistant` o `backend`
   - Click en los **3 puntos** (⋮) → **Edit**

5. **🔧 Aumentar la RAM** (CRÍTICO):
   - Sección **"Resources"** o **"Size"**
   - Cambiar de `basic-xxs` a **`basic-xs`** (512 MB RAM) o mejor **`professional-xs`** (1 GB RAM)
   - **Recomendado**: `professional-xs` (1 GB RAM, $12/mes) para estar seguro

6. **⏱️ Aumentar el Timeout** (CRÍTICO):
   - Sección **"Environment Variables"**
   - Buscar `GUNICORN_TIMEOUT`
   - Cambiar valor de `300` a **`10800`** (3 horas)
   - Si no existe, añadirla:
     ```
     Key: GUNICORN_TIMEOUT
     Value: 10800
     ```

7. **📝 Añadir variable de inicialización**:
   - En la misma sección "Environment Variables"
   - Añadir nueva variable:
     ```
     Key: INIT_RAG
     Value: true
     ```

8. **💾 Guardar cambios**:
   - Click en **"Save"**
   - DigitalOcean se redesplegará automáticamente

---

## 🔍 Qué Pasará Durante el Deploy

### Fase 1: Build (2-5 minutos)
```
📦 Instalando dependencias de Python...
✅ Build completado
```

### Fase 2: Startup (1-2 horas) ⏳
```
🛠️ Starting Nisira Assistant Backend
📦 Port: 8000
👷 Workers: 2
⏱️ Timeout: 10800s  ← Verifica que sea 10800, no 300
⏳ Waiting for database...
✅ Database is ready
📦 Running migrations...
🔄 Initializing RAG system...  ← ESTE PASO TARDARÁ 1-2 HORAS
```

**Durante la inicialización del RAG verás:**
```
🔑 Usando Service Account credentials
✅ Service Account: nisira-prod-server@nisira-assistance.iam.gserviceaccount.com
📁 Total: X archivos en Google Drive
⬇️ Descargando documentos...
📄 Procesando documentos (PDF → chunks)...
🧮 Generando embeddings (13,000+ vectores)... ← ESTO ES LO QUE TOMA TIEMPO
💾 Almacenando en ChromaDB...
✅ RAG system initialized successfully
```

### Fase 3: Running (después de 1-2 horas)
```
🚀 Launching Gunicorn on port 8000
✅ Backend activo y listo
```

---

## 📊 Monitorear el Progreso

### 1. Ver Logs en Tiempo Real:
- En DigitalOcean dashboard → tu app → pestaña **"Logs"**
- O desde CLI:
  ```bash
  doctl apps logs <app-id> --follow --type RUN
  ```

### 2. Verificar que NO falle:
- ❌ **MAL**: Si ves `Worker timeout (pid:123)` → El timeout es muy corto
- ✅ **BIEN**: Si ves `🔄 Initializing RAG system...` y continúa ejecutando

### 3. Paciencia:
- ⏱️ El proceso puede tardar **1-2 horas**
- 🚫 **NO lo interrumpas** ni reinicies la app
- ☕ Ve por un café, da un paseo, etc.

---

## ✅ Verificar que Funcionó

Una vez que el deploy termine (status "Live" en DigitalOcean):

### 1. Probar el endpoint de salud:
```bash
curl https://<tu-app>-backend.ondigitalocean.app/api/health/
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "database": "ok",
  "rag_system": "initialized",
  "embeddings_count": 13000
}
```

### 2. Verificar en el frontend:
- Actualizar la URL del backend en Heroku:
  ```bash
  heroku config:set REACT_APP_API_URL=https://<tu-app>-backend.ondigitalocean.app
  ```
- Abrir: https://nisira-assistant-frontend-2ae5b156ad38.herokuapp.com/
- Hacer login
- Enviar una pregunta en el chat
- Debe responder con información de los documentos

---

## 🐛 Troubleshooting

### Problema: "Worker timeout" en logs
**Causa**: `GUNICORN_TIMEOUT` muy bajo  
**Solución**: 
1. Settings → Environment Variables
2. Cambiar `GUNICORN_TIMEOUT` a `10800`
3. Save → Redeploy

### Problema: "Out of memory" / App crashed
**Causa**: RAM insuficiente  
**Solución**:
1. Settings → Resources
2. Cambiar a `professional-xs` (1 GB) o `professional-s` (2 GB)
3. Save → Redeploy

### Problema: "Service Account detectada. Cambiando a OAuth..."
**Causa**: El código antiguo de `drive_manager.py` sigue en el servidor  
**Solución**: 
- Verificar que el último commit está desplegado
- En DigitalOcean → Settings → Source → verificar que branch sea `main`
- Forzar redeploy: Settings → General → **"Force Rebuild and Deploy"**

### Problema: "file is not a database" (ChromaDB)
**Causa**: Archivos LFS corruptos aún están en el repo  
**Solución**:
- Verificar que `.gitignore` tiene `backend/data/` y `backend/chroma_db/`
- Verificar que los commits locales no incluyen esos archivos:
  ```bash
  git ls-files | grep "chroma_db"  # No debe mostrar nada
  git ls-files | grep "data/documents"  # No debe mostrar nada
  ```

---

## 📝 Checklist Final

Antes de hacer el deploy en DigitalOcean, verifica:

- [ ] Commit de "chore: Ignorar carpetas de datos locales" está en origin/main
- [ ] Commit de "fix: Arreglar Drive Manager..." está en origin/main
- [ ] Variable `GUNICORN_TIMEOUT` configurada en **10800**
- [ ] Variable `INIT_RAG` configurada en **true**
- [ ] Tamaño de instancia mínimo: **basic-xs** (512 MB) o mejor **professional-xs** (1 GB)
- [ ] Service Account JSON guardada en local: `backend/credentials.json`
- [ ] Carpeta `backend/data/` está en `.gitignore` (no se sube al repo)
- [ ] Carpeta `backend/chroma_db/` está en `.gitignore` (no se sube al repo)

---

## 🎉 Una Vez que Funcione

### Para futuras actualizaciones del corpus:

1. **Subir documentos nuevos a Google Drive** (carpeta configurada)

2. **Regenrar embeddings**:
   - Opción A: Reiniciar la app en DigitalOcean (tarda 1-2 horas)
   - Opción B: Ejecutar comando manual:
     ```bash
     doctl apps exec <app-id> --component backend
     # Dentro del contenedor:
     python manage.py rag_manage init
     ```

3. **Para cambios de código** (sin regenerar embeddings):
   - Simplemente hacer `git push origin main`
   - DigitalOcean se redesplega automáticamente
   - Cambia `INIT_RAG` a `false` en las variables de entorno

---

## 🚀 ¡ADELANTE!

**Ahora ve a DigitalOcean y configura el timeout + RAM como se indicó arriba.**

Una vez configurado, DigitalOcean hará el redeploy automáticamente y tu backend estará listo en 1-2 horas. 🎊
