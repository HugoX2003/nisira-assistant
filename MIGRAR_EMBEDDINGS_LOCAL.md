# 🚀 Migración de Embeddings Existentes

## ✅ Migrar en lugar de Regenerar

Tienes embeddings locales en `backend/chroma_db/` → Podemos migrarlos a PostgreSQL.

**Ventaja:** Deploy instantáneo sin esperar 1-2 horas.

---

## 📋 Pasos para Migrar

### 1. Verificar que tienes embeddings locales

```powershell
cd "c:\Users\amaya\Downloads\10mo Ciclo\nisira-assistant\backend"

# Verificar ChromaDB local
python manage.py rag_manage status
```

**Debe mostrar:**
```
✅ vector_store: True
Total documentos: 13,457 (o similar)
```

### 2. Configurar DATABASE_URL local

**Opción A: Usar tu PostgreSQL local**

```powershell
# En tu .env local
DATABASE_URL=postgresql://usuario:password@localhost:5432/nisira_db
```

**Opción B: Conectar temporalmente a DigitalOcean**

```powershell
# Usar la URL de producción (obtenerla desde DigitalOcean Dashboard → Databases)
$env:DATABASE_URL="postgresql://usuario:password@host:puerto/defaultdb?sslmode=require"
```

### 3. Ejecutar migración

```powershell
cd backend

# Aplicar migración de Django primero
python manage.py migrate

# Migrar embeddings de ChromaDB → PostgreSQL
python migrate_embeddings_to_postgres.py
```

**Output esperado:**
```
🔄 Iniciando migración de embeddings...
📂 Conectando a ChromaDB local...
✅ ChromaDB listo: 13,457 documentos encontrados
🐘 Conectando a PostgreSQL...
✅ PostgreSQL listo
📥 Obteniendo 13,457 documentos de ChromaDB...
💾 Insertando en PostgreSQL...
Migrando: 100%|████████████| 135/135 [02:34<00:00]

📊 Resumen de migración:
   Total documentos: 13,457
   ✅ Exitosos: 13,457
   ❌ Fallidos: 0

🐘 PostgreSQL ahora tiene: 13,457 documentos
   Tamaño en disco: 45 MB

✅ Migración EXITOSA
```

### 4. Verificar migración

```powershell
python migrate_embeddings_to_postgres.py --verify
```

**Output:**
```
📊 Comparación:
   ChromaDB:   13,457 documentos
   PostgreSQL: 13,457 documentos
   ✅ Migración verificada correctamente
```

### 5. Commit y Push

```powershell
cd ..

git add .
git commit -m "feat: Migrar embeddings existentes a PostgreSQL

- Script de migración automática
- Embeddings persistentes en PostgreSQL
- Sin necesidad de regeneración en deploy"

git push origin main
```

### 6. Deploy en DigitalOcean

**Comportamiento esperado:**

```
🔄 Initializing RAG system...
✅ Usando PostgreSQL como vector store
✅ Embeddings persistentes detectados: 13,457 documentos
✅ Sistema RAG listo en 5 segundos
```

**NO** verás:
```
⚠️ No se detectaron embeddings
🔄 Sincronizando desde Drive... ← ESTO NO PASARÁ
```

---

## ⚡ Tiempos Estimados

| Paso | Tiempo |
|------|--------|
| **Migración local** | 2-5 minutos |
| **Upload a PostgreSQL** | Ya está |
| **Deploy en DigitalOcean** | 5-10 seg |
| **Total** | ~10 minutos |

vs.

| Alternativa | Tiempo |
|-------------|--------|
| **Regenerar en DigitalOcean** | 1-2 horas |

---

## 🎯 Estrategia Recomendada

### Opción 1: Migrar Directamente a Producción (RECOMENDADO)

```powershell
# Conectar a PostgreSQL de producción
$env:DATABASE_URL="postgresql://doadmin:AVNS_...@db-postgresql-nyc1-21414..."

# Migrar
python backend/migrate_embeddings_to_postgres.py

# Verificar
python backend/migrate_embeddings_to_postgres.py --verify

# Deploy
git push origin main
```

**Ventaja:** Deploy instantáneo, embeddings ya están en la nube.

### Opción 2: Probar Local Primero

```powershell
# 1. PostgreSQL local
$env:DATABASE_URL="postgresql://localhost/nisira_test"

# 2. Migrar localmente
python backend/migrate_embeddings_to_postgres.py

# 3. Probar
python manage.py rag_manage status

# 4. Migrar a producción (repetir con DATABASE_URL de prod)
```

---

## 🔧 Troubleshooting

### Error: "ChromaDB no está disponible"

```powershell
# Verificar que existe chroma_db local
dir backend\chroma_db\

# Debe tener: chroma.sqlite3 + carpetas UUID
```

### Error: "PostgreSQL no está disponible"

```powershell
# Verificar conexión
python -c "import psycopg2; psycopg2.connect('$env:DATABASE_URL'); print('OK')"
```

### Migración lenta

Es normal, cada batch de 100 documentos toma ~1 segundo:
- 13,000 docs = ~130 batches = 2-3 minutos

### Verificar embeddings migrados

```sql
-- En PostgreSQL
SELECT COUNT(*) FROM rag_embeddings;
-- Debe retornar: 13,457

SELECT pg_size_pretty(pg_total_relation_size('rag_embeddings'));
-- Debe retornar: ~45 MB
```

---

## ✅ Resultado Final

**Después de migrar:**

1. ✅ PostgreSQL tiene 13,457 embeddings
2. ✅ Deploy en DigitalOcean es INSTANTÁNEO
3. ✅ NO regenera embeddings
4. ✅ Sistema listo en 5 segundos
5. ✅ Persistencia garantizada

**Bonus:**
- ChromaDB local sigue funcionando (no se borra)
- Puedes cambiar entre backends con `VECTOR_STORE_BACKEND=chroma`
- Backups automáticos de DigitalOcean

---

## 🎉 Ventajas de Migrar

| Aspecto | Sin Migrar | Con Migración |
|---------|-----------|---------------|
| **Primera inicialización** | 1-2 horas | 5 segundos |
| **Reinicios** | 1-2 horas | 5 segundos |
| **Deploys** | 1-2 horas | 5 segundos |
| **Costos API** | $0.30/deploy | $0.00 |
| **Downtime** | 1-2 horas | 0 segundos |

---

## 📞 Próximos Pasos

¿Quieres que ejecute la migración ahora?

```powershell
# Opción 1: Migrar directo a producción (obtener URL desde DigitalOcean Dashboard)
$env:DATABASE_URL="<URL_POSTGRESQL_PRODUCCION>"
python backend/migrate_embeddings_to_postgres.py

# Opción 2: Probar local primero
$env:DATABASE_URL="postgresql://localhost/nisira_local"
python backend/migrate_embeddings_to_postgres.py
```

**Recomendación:** Migrar directo a producción y hacer push. Deploy será instantáneo.
