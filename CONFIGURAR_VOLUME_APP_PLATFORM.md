# 🎯 GUÍA PASO A PASO: Configurar Volume en App Platform

## ⚠️ IMPORTANTE: Estás en el lugar equivocado

La captura de pantalla muestra **Volumes Block Storage** (para Droplets).

Tu app está en **App Platform** (diferente servicio).

---

## ✅ Pasos Correctos para App Platform

### 1. Ir a tu App

```
Dashboard → Apps (menú izquierdo) → Click en "nisira-assistant"
```

**NO** ir a "Volumes Block Storage"

---

### 2. Configurar el Componente Backend

Una vez en tu app:

```
1. Click en la pestaña "Settings" (arriba)
2. Scroll hacia abajo hasta ver tus componentes
3. Verás algo como:
   
   Components:
   ├─ backend (Web Service)
   └─ ...

4. Click en "backend" (o el nombre de tu componente Python)
```

---

### 3. Editar el Componente

Dentro de la configuración del componente backend:

```
1. Buscar la sección "Resources" o "Resource Size"
2. Scroll hacia abajo
3. Encontrarás una sección llamada "Mounts" o "Volumes"
4. Click en "Add Mount" o "Add Volume"
```

**Nota:** Si NO ves "Mounts" o "Volumes", puede que necesites hacerlo desde el archivo de especificación (siguiente opción).

---

### 4. Opción Alternativa: Editar app.yaml

Si no encuentras la opción de Volumes en la interfaz:

**4.1. Descargar especificación actual:**

```
Settings → App Spec → Click en "Edit" → Copiar el YAML
```

**4.2. Agregar la sección de volume:**

Busca la sección de tu componente backend y agrega:

```yaml
name: nisira-assistant
services:
- name: backend
  # ... configuración existente ...
  
  # AGREGAR ESTAS LÍNEAS:
  mounts:
  - path: /app/chroma_db
    size: 1GB
  
  # ... resto de la configuración ...
```

**4.3. Guardar y deployar:**

```
1. Pegar el YAML modificado
2. Click "Save"
3. La app se redeployará automáticamente
```

---

## 📸 Guía Visual

### Dónde DEBES estar:

```
DigitalOcean Dashboard
└─ Apps (menú izquierdo)
   └─ nisira-assistant (tu app)
      └─ Settings
         └─ Components
            └─ backend
               └─ Mounts/Volumes ← AQUÍ
```

### Dónde NO debes estar:

```
DigitalOcean Dashboard
└─ Manage (menú izquierdo)
   └─ Volumes Block Storage ← NO AQUÍ (es para Droplets)
```

---

## 🔧 Configuración Exacta del Mount

Cuando encuentres la opción, configura:

```yaml
Mount Path: /app/chroma_db
Size: 1 GB
Name: embeddings-storage (opcional)
```

**Explicación:**
- `Mount Path`: Ruta donde se montará dentro del contenedor
- `Size`: 1GB es suficiente para ~20,000 documentos
- `Name`: Nombre descriptivo (opcional)

---

## ⚡ Si App Platform No Soporta Volumes

**DigitalOcean App Platform tiene limitaciones:**

Algunas configuraciones de App Platform NO permiten volumes persistentes en el plan básico.

**Alternativa 1: Usar PostgreSQL como Storage** (Más complejo)
- Guardar embeddings en la base de datos
- Requiere modificar código de ChromaDB

**Alternativa 2: Usar DigitalOcean Spaces** (S3-compatible)
- Almacenar chroma_db en Spaces
- Requiere modificar código para sincronizar

**Alternativa 3: Migrar a Droplet** (Recomendado si necesitas persistencia)
- Crear un Droplet (VPS)
- Usar docker-compose.yml que ya tienes
- Configurar volume local (como en desarrollo)

---

## 🎯 Recomendación Inmediata

**Opción más simple para verificar soporte:**

1. **Ir a:** Apps → nisira-assistant → Settings
2. **Buscar:** "Persistent Storage" o "Mounts" o "Volumes"
3. **Si NO existe:** App Platform Basic no soporta volumes persistentes

**En ese caso, tienes 2 opciones:**

### Opción A: Upgrade a Professional Plan ($12/mes)
- Incluye persistent storage
- Configurar volume como explicado arriba

### Opción B: Migrar a Droplet ($6-12/mes)
- Control total
- Docker Compose funciona directo
- Volume persistente nativo

---

## 📞 ¿Qué Hacer Ahora?

**Paso 1:** Verifica si tu plan actual soporta volumes

```
Apps → nisira-assistant → Settings → Ver si hay opción "Mounts"
```

**Paso 2:** Si NO hay opción de Mounts:

Tienes que decidir:
- [ ] Upgrade a Professional plan ($12/mes)
- [ ] Migrar a Droplet ($6/mes) + más control
- [ ] Implementar solución alternativa (S3 Spaces)

**Paso 3:** Si SÍ hay opción de Mounts:

Configurar:
```yaml
path: /app/chroma_db
size: 1GB
```

---

## 🆘 Necesitas Ayuda Ahora

**Dime qué ves en tu pantalla:**

1. Ve a: Apps → nisira-assistant → Settings
2. Scroll por todas las opciones del componente backend
3. Toma captura de pantalla
4. Busca palabras clave: "Mount", "Volume", "Storage", "Persistent"

**Con eso puedo decirte exactamente qué configurar o si necesitas cambiar de plan.**

---

## 📋 Resumen

| Servicio | Ubicación | Tipo de Volume |
|----------|-----------|----------------|
| **App Platform** | Apps → tu-app → Settings → Components | Mounts (si disponible) |
| **Droplets** | Manage → Volumes Block Storage | Block Storage |

**Tu app está en App Platform**, no uses Volumes Block Storage.
