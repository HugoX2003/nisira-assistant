# ✅ CHECKLIST DE DESPLIEGUE

## 📋 Pre-Despliegue

- [ ] Código funcionando localmente
- [ ] Crear repositorio en GitHub
- [ ] Subir código a GitHub
- [ ] Crear cuenta Railway.app
- [ ] Crear cuenta Vercel.com
- [ ] Obtener API key de OpenRouter

## 🔧 Configuración Backend (Railway)

- [ ] Crear proyecto en Railway
- [ ] Conectar repositorio GitHub
- [ ] Seleccionar directorio: `/backend`
- [ ] Configurar variables de entorno:
  - [ ] `DJANGO_SECRET_KEY`
  - [ ] `OPENROUTER_API_KEY`
  - [ ] `ALLOWED_HOSTS=*.railway.app`
  - [ ] `DEBUG=False`
- [ ] Agregar volumen persistente:
  - [ ] Mount path: `/app/data`
  - [ ] Size: 1GB
- [ ] Verificar build completado
- [ ] Verificar deploy exitoso
- [ ] Probar endpoint: `/api/health/`

## 🎨 Configuración Frontend (Vercel)

- [ ] Crear proyecto en Vercel
- [ ] Importar repositorio GitHub
- [ ] Configurar root directory: `frontend`
- [ ] Configurar variable de entorno:
  - [ ] `REACT_APP_API_URL=https://tu-backend.railway.app`
- [ ] Verificar build completado
- [ ] Verificar deploy exitoso
- [ ] Probar aplicación web

## 🔐 Configuración de Seguridad

- [ ] Actualizar `CORS_ALLOWED_ORIGINS` en `production_settings.py`
- [ ] Actualizar `CSRF_TRUSTED_ORIGINS` en `production_settings.py`
- [ ] Verificar que `DEBUG=False` en producción
- [ ] Verificar SSL habilitado (Railway lo hace automático)

## 🗄️ Configuración de Base de Datos

- [ ] Verificar que ChromaDB persiste (volumen /app/data)
- [ ] Procesar PDFs iniciales:
  - Opción A: Procesar localmente y subir ChromaDB
  - Opción B: Procesar en Railway (puede tardar)
- [ ] Verificar que hay documentos en ChromaDB

## 🧪 Pruebas Post-Despliegue

- [ ] Health check responde: `GET /api/health/`
- [ ] Login funciona
- [ ] Crear conversación funciona
- [ ] Enviar mensaje funciona
- [ ] Consulta RAG funciona
- [ ] Respuestas del LLM funcionan
- [ ] Frontend se conecta al backend
- [ ] CORS configurado correctamente

## 📊 Monitoreo

- [ ] Verificar logs en Railway Dashboard
- [ ] Verificar métricas en Railway
- [ ] Configurar alertas (opcional)
- [ ] Documentar URL de producción

## 🎉 Finalización

- [ ] Documentar URLs finales:
  - Backend: `https://_____.railway.app`
  - Frontend: `https://_____.vercel.app`
- [ ] Compartir acceso con equipo
- [ ] Configurar dominio personalizado (opcional)
- [ ] Configurar backups automáticos (opcional)

---

## 🆘 Si algo falla

1. Revisar logs en Railway Dashboard
2. Verificar variables de entorno
3. Verificar que el volumen está montado
4. Consultar `DEPLOYMENT_GUIDE.md` sección Troubleshooting
5. Crear issue en GitHub

---

**Fecha de despliegue:** ________________
**Desplegado por:** ________________
**URLs producción:**
- Backend: ________________
- Frontend: ________________