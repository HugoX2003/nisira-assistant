# 🎯 Configurar Volume via App Spec (YAML)

## Paso 1: Editar App Spec

1. En la pantalla actual, scroll hacia abajo
2. Busca la sección **"App Spec"**
3. Click en **"Edit"**

---

## Paso 2: Encontrar tu componente backend

Busca una sección que se vea así:

```yaml
services:
- name: nisira-assistant
  # o 
- name: backend
  # o similar
```

---

## Paso 3: Agregar el storage

**DENTRO** de tu servicio backend, agrega esto:

```yaml
services:
- name: nisira-assistant  # Tu nombre puede variar
  # ... configuración existente ...
  
  # AGREGAR ESTAS LÍNEAS:
  volumes:
  - name: embeddings-storage
    mount_path: /app/chroma_db
    size_gb: 1
```

---

## 📄 Ejemplo Completo

Si tu App Spec se ve así:

```yaml
name: nisira-assistant
region: atl
services:
- name: nisira-assistant
  environment_slug: python
  github:
    branch: main
    deploy_on_push: true
    repo: HugoX2003/nisira-assistant
  http_port: 8000
  instance_count: 1
  instance_size_slug: basic-xs
  source_dir: /backend
```

**Debe quedar así:**

```yaml
name: nisira-assistant
region: atl
services:
- name: nisira-assistant
  environment_slug: python
  github:
    branch: main
    deploy_on_push: true
    repo: HugoX2003/nisira-assistant
  http_port: 8000
  instance_count: 1
  instance_size_slug: basic-xs
  source_dir: /backend
  
  # ✨ AGREGAR ESTO:
  volumes:
  - name: embeddings-storage
    mount_path: /app/chroma_db
    size_gb: 1
```

---

## ⚠️ Importante

- **Indentación correcta:** Las líneas deben estar al mismo nivel que `source_dir`, `http_port`, etc.
- **YAML es sensible a espacios:** Usa 2 espacios para indentar
- **No uses tabs:** Solo espacios

---

## Paso 4: Guardar

1. Click en **"Save"**
2. La app se redeployará automáticamente
3. Espera 5-10 minutos

---

## Paso 5: Verificar Logs

Después del deploy:

1. Ve a **"Runtime Logs"**
2. Busca líneas como:
   - `"⚠️ No se detectaron embeddings"` → Primera vez (normal)
   - `"🔄 Sincronizando documentos..."` → Generando embeddings (1-2 horas)
   - `"✅ Sistema RAG inicializado: N documentos"`

---

## 🔧 Si sale error de sintaxis YAML

Usa esta herramienta para validar:
https://www.yamllint.com/

Copia tu YAML completo y verifica errores.

---

## 💡 Alternativa: Plan Professional

Si el Basic plan NO soporta volumes (puede pasar):

**Opción 1:** Upgrade a Professional ($12/mes)
- Incluye volumes garantizados

**Opción 2:** Migrar a Droplet ($6/mes)
- Docker Compose funciona directo
- Volume nativo con `-v ./chroma_db:/app/chroma_db`

---

## 📞 Siguiente Paso

**Copia tu App Spec actual completo** (todo el YAML) y pégalo aquí.

Te ayudo a agregar el volume en el lugar correcto con la sintaxis exacta.
