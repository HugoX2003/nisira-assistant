# 🔀 GUÍA DE DESPLIEGUE CON REPOSITORIO FORKEADO

## 📋 SITUACIÓN: No eres dueño del repositorio original

### ✅ SOLUCIÓN: Fork + Deploy

---

## 🔀 PASO 1: HACER FORK DEL REPOSITORIO

### Opción A: Fork en GitHub (RECOMENDADO)

```bash
1. Ir a: https://github.com/HugoX2003/nisira-assistant

2. Click en "Fork" (botón arriba a la derecha)

3. Seleccionar tu cuenta como destino

4. Click "Create fork"

5. ¡Ahora tienes tu propia copia!
   https://github.com/TU_USUARIO/nisira-assistant
```

### Opción B: Clonar y crear nuevo repo

```bash
# 1. Clonar el repo original
git clone https://github.com/HugoX2003/nisira-assistant.git
cd nisira-assistant

# 2. Cambiar el remote
git remote remove origin
git remote add origin https://github.com/TU_USUARIO/nisira-assistant.git

# 3. Crear nuevo repo en GitHub (vacío)
# Ve a GitHub: New Repository → nisira-assistant

# 4. Push a tu nuevo repo
git push -u origin main
```

---

## 🚀 PASO 2: DESPLEGAR DESDE TU FORK

### Backend en Railway

```bash
1. Ir a railway.app

2. New Project → Deploy from GitHub

3. Seleccionar TU repositorio:
   TU_USUARIO/nisira-assistant (no el original)

4. Continuar con configuración normal...
```

### Frontend en Vercel

```bash
1. Ir a vercel.com

2. New Project → Import

3. Seleccionar TU repositorio:
   TU_USUARIO/nisira-assistant (no el original)

4. Continuar con configuración normal...
```

---

## 🔄 MANTENER ACTUALIZADO CON EL ORIGINAL

Si el dueño original (HugoX2003) actualiza el código:

```bash
# 1. Agregar el repo original como "upstream"
git remote add upstream https://github.com/HugoX2003/nisira-assistant.git

# 2. Fetch cambios del original
git fetch upstream

# 3. Merge cambios a tu fork
git checkout main
git merge upstream/main

# 4. Push a tu fork
git push origin main

# Railway y Vercel auto-deployarán los cambios ✅
```

---

## 🔐 PERMISOS Y COLABORACIÓN

### Si tienes acceso directo al repo original:

**Opción 1: Deploy directo (si tienes permisos)**
```bash
# Railway y Vercel pueden deployar repos que no son tuyos
# Solo necesitas:
- Ser colaborador del repo
- O que el repo sea público
```

**Opción 2: Branch separado**
```bash
# Crear tu propio branch
git checkout -b mi-despliegue

# Push tu branch
git push origin mi-despliegue

# Deployar desde ese branch en Railway/Vercel
```

---

## ⚠️ CONSIDERACIONES IMPORTANTES

### 🔒 Con Fork (Tu copia):
- ✅ Control total
- ✅ Puedes modificar libremente
- ✅ No afectas el original
- ✅ Puedes mantener privado o público
- ⚠️ Debes sincronizar manualmente con original

### 🤝 Con Acceso Directo (Como colaborador):
- ✅ Trabajas en el repo original
- ✅ Cambios automáticos para todos
- ⚠️ Requiere permisos del dueño
- ⚠️ Debes coordinar con el equipo

---

## 🎯 RECOMENDACIÓN SEGÚN TU CASO

### Caso 1: Solo quieres deployar (sin modificar código)
```bash
✅ Hacer Fork
✅ Deploy desde tu fork
✅ No sincronizar (a menos que el original mejore)
```

### Caso 2: Vas a modificar y contribuir
```bash
✅ Hacer Fork
✅ Hacer cambios en tu fork
✅ Pull Request al original
✅ Deploy desde tu fork
```

### Caso 3: Eres colaborador oficial
```bash
✅ Clonar directo
✅ Crear branch de deploy
✅ Deploy desde el repo original
✅ Coordinar con el equipo
```

---

## 📝 PASOS RÁPIDOS RECOMENDADOS

```bash
# 1. Fork en GitHub
Ir a GitHub → Fork button

# 2. Clonar TU fork
git clone https://github.com/TU_USUARIO/nisira-assistant.git
cd nisira-assistant

# 3. Deploy Backend (Railway)
- New Project → tu fork
- Config variables
- Deploy ✅

# 4. Deploy Frontend (Vercel)
- New Project → tu fork
- Config variables
- Deploy ✅

# 5. ¡Listo! Tu sistema desplegado desde TU fork
```

---

## 🔄 FLUJO DE TRABAJO CON FORK

```
Original Repo (HugoX2003)
         ↓ Fork
    Tu Fork (TU_USUARIO)
         ↓ Deploy
    Railway + Vercel
         ↓ URLs
    Tu sistema en producción ✅
```

---

## 💡 TIPS ADICIONALES

### Para mantener ChromaDB actualizada:
```bash
# Si el original tiene documentos nuevos:
1. Pull cambios del upstream
2. Re-procesar PDFs localmente
3. Subir nueva ChromaDB a Railway
```

### Para personalizar tu fork:
```bash
# Puedes cambiar:
- Nombre del proyecto
- Colores del frontend
- Documentos específicos
- Configuraciones
- ¡Todo sin afectar el original!
```

---

## 🆘 TROUBLESHOOTING

### Error: "Repository not found"
✅ Verifica que hiciste fork correctamente
✅ Verifica que el fork es público (o conectaste Railway/Vercel)

### Error: "Permission denied"
✅ Usa TU fork, no el original
✅ Verifica que conectaste tu cuenta GitHub en Railway/Vercel

### Error: "Out of sync with original"
✅ Fetch upstream
✅ Merge cambios
✅ Push a tu fork

---

## ✅ CHECKLIST PARA FORK

- [ ] Fork hecho en GitHub
- [ ] Fork clonado localmente
- [ ] Remote origin apunta a TU fork
- [ ] Upstream agregado (opcional, para actualizaciones)
- [ ] Railway conectado a TU fork
- [ ] Vercel conectado a TU fork
- [ ] Variables de entorno configuradas
- [ ] Deploy exitoso
- [ ] Sistema funcionando

---

## 📞 RECURSOS

- GitHub Fork Docs: https://docs.github.com/en/get-started/quickstart/fork-a-repo
- Railway Deploy: https://docs.railway.app/deploy/deployments
- Vercel Import: https://vercel.com/docs/concepts/git

---

**🎉 ¡Ahora puedes deployar desde TU propia copia del repositorio!**