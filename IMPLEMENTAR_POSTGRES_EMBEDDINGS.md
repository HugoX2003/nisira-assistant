# 🎯 Implementación: Embeddings en PostgreSQL

## ✅ Archivos Creados

He implementado el almacenamiento de embeddings en PostgreSQL. Los archivos nuevos son:

1. **`backend/api/migrations/0003_add_pgvector_embeddings.py`**
   - Migración de Django para crear la tabla `rag_embeddings`

2. **`backend/rag_system/vector_store/postgres_store.py`**
   - Implementación completa del vector store en PostgreSQL
   - API compatible con ChromaDB

3. **Modificaciones en:**
   - `backend/rag_system/config.py` - Configuración del vector store
   - `backend/rag_system/rag_engine/pipeline.py` - Selección automática del backend

---

## 📋 Pasos para Implementar

### 1. Commit y Push de los Cambios

```powershell
cd "c:\Users\amaya\Downloads\10mo Ciclo\nisira-assistant"

git add .
git commit -m "feat: Implementar almacenamiento de embeddings en PostgreSQL

- Agregar PostgresVectorStore compatible con ChromaDB
- Migración para tabla rag_embeddings  
- Configuración para seleccionar backend (postgres/chroma)
- Validaciones de registro mejoradas
- Upload con procesamiento automático de embeddings"

git push origin main
```

### 2. Deploy en DigitalOcean

El deploy se hará automáticamente al hacer push (tienes `deploy_on_push: true`).

### 3. Verificar Logs del Deploy

1. Ve a tu app en DigitalOcean
2. Click en "Runtime Logs"
3. Busca:

```
✅ Usando PostgreSQL como vector store
✅ Conectado a PostgreSQL para embeddings
✅ Tabla rag_embeddings lista
```

### 4. Esperar Sincronización Inicial

**Primera vez (sin embeddings en PostgreSQL):**
```
🔄 Initializing RAG system...
⚠️ No se detectaron embeddings persistentes  
🔄 Sincronizando documentos desde Google Drive...
📥 Descargando 389 archivos...
🧮 Generando embeddings...
✅ N documentos insertados en PostgreSQL
✅ Sistema RAG inicializado: N documentos
```

**Tiempo estimado:** 1-2 horas (solo la primera vez)

### 5. Reinicios Posteriores

```
🔄 Initializing RAG system...
✅ Embeddings persistentes detectados: N documentos
✅ Usando PostgreSQL como vector store
✅ Sistema RAG listo en 5 segundos
```

---

## 🔧 Cómo Funciona

### Tabla en PostgreSQL

```sql
CREATE TABLE rag_embeddings (
    id UUID PRIMARY KEY,
    chunk_text TEXT NOT NULL,
    embedding_vector JSONB,          -- Array de 768 floats
    metadata JSONB,                   -- {file_name, page, chunk_id, etc}
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Búsqueda de Similitud

El sistema calcula la similitud coseno entre vectores:

```python
similarity = 1 - distance
distance = cosine_distance(query_vector, stored_vector)
```

### Storage Estimado

- **Por embedding:** ~3 KB (768 floats en JSON)
- **13,000 chunks:** ~39 MB
- **Metadata adicional:** ~5 MB
- **Total:** ~45 MB

---

## 🎮 Cambiar Entre Backends

Si en el futuro quieres volver a ChromaDB:

```bash
# En DigitalOcean → Settings → Environment Variables
VECTOR_STORE_BACKEND=chroma  # Por defecto: postgres
```

---

## ✅ Ventajas de PostgreSQL

1. ✅ **Persistencia garantizada** - Backups automáticos de DigitalOcean
2. ✅ **Sin costos extra** - Usas la BD que ya tienes
3. ✅ **Escalable** - PostgreSQL maneja millones de vectores
4. ✅ **Sin volumes** - No necesitas configuración especial
5. ✅ **Backups automáticos** - Tus embeddings están protegidos

---

## 🧪 Probar Localmente (Opcional)

Si quieres probar antes de hacer deploy:

```powershell
# 1. Aplicar migración
python manage.py migrate

# 2. Probar con PostgreSQL local
$env:VECTOR_STORE_BACKEND="postgres"
$env:DATABASE_URL="postgresql://usuario:pass@localhost:5432/nisira"

python manage.py rag_manage init
```

---

## 🆘 Troubleshooting

### Error: "psycopg2 no disponible"

Ya está en `requirements.txt`, pero si falla:

```txt
psycopg2-binary==2.9.9
```

### Error: "tabla rag_embeddings no existe"

Ejecutar migración manualmente:

```bash
# En DigitalOcean Runtime → Console
python manage.py migrate
```

### Embeddings no se cargan tras reinicio

Verificar:
1. Logs: "Usando PostgreSQL como vector store"
2. Query:
```sql
SELECT COUNT(*) FROM rag_embeddings;
```

---

## 📊 Monitoreo

### Ver cantidad de embeddings:

```python
from rag_system.vector_store.postgres_store import PostgresVectorStore

store = PostgresVectorStore()
stats = store.get_collection_stats()
print(stats)
# {'ready': True, 'total_documents': 13457, 'table_size': '45 MB'}
```

### Verificar desde admin panel:

- Ve a: `https://tu-app.ondigitalocean.app/admin/panel/`
- RAG Management → Status
- Debe mostrar: "Storage: PostgreSQL"

---

## 🎯 Resultado Final

### Métricas Esperadas:

| Escenario | Tiempo | Costo API |
|-----------|--------|-----------|
| **Primera inicialización** | 1-2 horas | $0.30 (una vez) |
| **Reinicio app** | 5-10 seg | $0.00 |
| **Deploy nuevo código** | 5-10 seg | $0.00 |
| **Agregar documento** | 5-30 seg | $0.001 |

### Storage en PostgreSQL:

- **Tamaño actual:** ~45 MB
- **Límite PostgreSQL:** 25 GB (plan DigitalOcean)
- **Capacidad:** ~7 millones de chunks

---

## ✨ Próximos Pasos

1. **Hacer commit y push** (arriba)
2. **Esperar deploy** (5-10 min)
3. **Ver logs** - Verificar que usa PostgreSQL
4. **Esperar sincronización inicial** (1-2 horas)
5. **Probar consulta** - Debe funcionar instantáneamente

**Después de la primera sincronización, los embeddings PERSISTIRÁN entre deploys. ✅**
