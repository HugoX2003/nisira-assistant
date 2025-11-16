# 🔍 Guía de Depuración - Sistema de Embeddings

## Problema Identificado

Los embeddings no se están almacenando correctamente en producción (Heroku). El panel de administración muestra 0 documentos a pesar de que los logs indican procesamiento exitoso.

## Cambios Implementados

### 1. Logs Detallados Agregados

Se han agregado logs extensivos en TODO el flujo de almacenamiento para identificar exactamente dónde falla la persistencia:

#### En `postgres_store.py`:
```python
🔵 PostgreSQL add_documents llamado con X docs, Y embeddings
🔵 DB connection status: True/False
🔵 DB URL configured: True/False
🔵 Preparados X valores para insertar en PostgreSQL
🔵 Muestra del primer valor: id=abc123..., texto_len=1234, metadata_keys=[...]
🔵 Ejecutando INSERT batch en PostgreSQL...
🔵 INSERT completado, ejecutando COMMIT...
✅ X documentos CONFIRMADOS en PostgreSQL (COMMIT exitoso)
📊 Total de documentos en tabla rag_embeddings: X
```

#### En `chroma_manager.py`:
```python
🟡 ChromaDB add_documents llamado con X docs, Y embeddings
🟡 Client status: True/False, Collection: rag_documents
🟡 Colección 'rag_documents' encontrada
```

#### En `admin_views.py`:
```python
🚀 generate_embeddings - Backend configurado: postgres/chroma
🚀 DATABASE_URL presente: True/False
📄 [X/Y] Procesando: archivo.pdf
   🔍 Extrayendo texto del PDF...
   ✂️  X chunks extraídos
   🧠 Generando embeddings para X chunks...
   ✅ Embeddings generados exitosamente
   💾 Llamando a add_documents con X documentos...
   💾 Vector store type: PostgresVectorStore/ChromaManager
   💾 Resultado de almacenamiento: True/False
   ✅ PDF 'archivo.pdf' procesado y ALMACENADO completamente
```

### 2. Detección Automática de Backend

Los endpoints ahora detectan automáticamente qué backend usar (PostgreSQL o ChromaDB):

```python
from rag_system.config import VECTOR_STORE_CONFIG
vector_backend = VECTOR_STORE_CONFIG.get('backend', 'postgres')
database_url = VECTOR_STORE_CONFIG.get('database_url')
```

### 3. Endpoints Actualizados

- `get_embeddings_status`: Muestra qué backend está activo
- `verify_embeddings`: Verifica el backend correcto
- `generate_embeddings`: Usa el backend configurado

## Qué Buscar en los Logs de Heroku

### 1. Al Iniciar el Servidor

```bash
heroku logs --tail -a nisira-assistant-backend
```

Busca estas líneas:
```
🚀 RAG PIPELINE MODULE LOADED
🔍 VECTOR_STORE_CONFIG: {'backend': 'postgres', 'database_url': 'postgresql://...'}
🔍 DATABASE_URL presente: True
✅ Usando PostgreSQL como vector store
✅ Conectado a PostgreSQL para embeddings
✅ Tabla rag_embeddings lista
```

❌ **SI NO VES ESTO**, el problema es de configuración de variables de entorno.

### 2. Al Generar Embeddings (Click en "Generar")

Busca esta secuencia completa:
```
🚀 generate_embeddings - Backend configurado: postgres
🚀 DATABASE_URL presente: True
✅ Usando PostgreSQL como vector store
🚀 INICIANDO GENERACIÓN DE EMBEDDINGS: 400 archivos totales (390 PDFs, 10 TXTs)
📄 [1/400] Procesando: archivo1.pdf
   🔍 Extrayendo texto del PDF...
   ✂️  15 chunks extraídos
   🧠 Generando embeddings para 15 chunks...
   ✅ Embeddings generados exitosamente
   💾 Guardando en PostgreSQL...
   💾 Llamando a add_documents con 15 documentos...
   💾 Vector store type: PostgresVectorStore
🔵 PostgreSQL add_documents llamado con 15 docs, 15 embeddings
🔵 DB connection status: True
🔵 DB URL configured: True
🔵 Preparados 15 valores para insertar en PostgreSQL
🔵 Ejecutando INSERT batch en PostgreSQL...
🔵 INSERT completado, ejecutando COMMIT...
✅ 15 documentos CONFIRMADOS en PostgreSQL (COMMIT exitoso)
📊 Total de documentos en tabla rag_embeddings: 15
   💾 Resultado de almacenamiento: True
   ✅ PDF 'archivo1.pdf' procesado y ALMACENADO completamente (15 chunks)
```

### 3. Identificar Fallos

#### Fallo en Conexión a PostgreSQL:
```
❌ Error conectando a PostgreSQL: connection refused
❌ PostgreSQL no está listo
   - PSYCOPG2_AVAILABLE: True
   - self.conn: None
```

**Solución**: Verificar variable `DATABASE_URL` en Heroku

#### Fallo en COMMIT:
```
🔵 Ejecutando INSERT batch en PostgreSQL...
❌ Error insertando documentos: permission denied for table rag_embeddings
```

**Solución**: Verificar permisos de la base de datos

#### Fallo en Embedding Manager:
```
❌ Error generando embeddings: API key not found
```

**Solución**: Verificar `GOOGLE_API_KEY` en Heroku

## Comandos de Verificación

### Verificar Variables de Entorno en Heroku

```bash
heroku config -a nisira-assistant-backend
```

Debe mostrar:
- `DATABASE_URL`: postgresql://...
- `GOOGLE_API_KEY`: AIza...
- `VECTOR_STORE_BACKEND`: postgres (opcional, por defecto es postgres)

### Verificar Contenido de la Base de Datos

```bash
heroku pg:psql -a nisira-assistant-backend
```

Luego ejecutar:
```sql
-- Ver si la tabla existe
\dt rag_embeddings

-- Contar documentos
SELECT COUNT(*) FROM rag_embeddings;

-- Ver últimos documentos insertados
SELECT id, created_at, LENGTH(chunk_text) as text_length, metadata->>'source' as source
FROM rag_embeddings
ORDER BY created_at DESC
LIMIT 10;
```

### Reiniciar Dynos (si es necesario)

```bash
heroku restart -a nisira-assistant-backend
```

## Flujo de Datos Correcto

```
Usuario → Panel Admin → Click "Generar"
↓
Backend recibe request → generate_embeddings()
↓
Detecta backend: VECTOR_STORE_CONFIG → 'postgres'
↓
Inicializa PostgresVectorStore(DATABASE_URL)
↓
Por cada archivo:
  1. Leer PDF/TXT
  2. Extraer chunks
  3. Generar embeddings (Google API)
  4. Llamar vector_store.add_documents()
  ↓
  5. PostgreSQL:
     - Preparar batch de datos
     - Ejecutar INSERT
     - COMMIT ✅
     - Verificar COUNT(*)
↓
Retornar success=True al frontend
↓
Frontend refresca status → Muestra X documentos
```

## Checklist de Verificación

- [ ] `heroku logs --tail` muestra "Conectado a PostgreSQL"
- [ ] `heroku config` muestra DATABASE_URL válido
- [ ] Al generar embeddings aparecen logs 🔵 de PostgreSQL
- [ ] Los logs muestran "COMMIT exitoso"
- [ ] Los logs muestran "Total de documentos: X" incrementándose
- [ ] `heroku pg:psql` muestra documentos en `rag_embeddings`
- [ ] Panel admin muestra documentos > 0

## Si Sigue Sin Funcionar

### Opción 1: Forzar ChromaDB Temporalmente

En Heroku Config Vars:
```bash
heroku config:set VECTOR_STORE_BACKEND=chroma -a nisira-assistant-backend
```

**Advertencia**: ChromaDB en Heroku no persiste entre reinicios (filesystem efímero)

### Opción 2: Verificar Extensión pgvector

```bash
heroku pg:psql -a nisira-assistant-backend
```

```sql
-- Verificar si pgvector está disponible
SELECT * FROM pg_available_extensions WHERE name = 'vector';

-- Si no está, el sistema debería funcionar igual con JSONB
-- (el código tiene fallback automático)
```

### Opción 3: Migración Manual

Si tienes embeddings en ChromaDB localmente:

```bash
# En tu máquina local
python manage.py migrate_embeddings_to_postgres
```

## Próximos Pasos

1. **Deploy** estos cambios a Heroku
2. **Reiniciar** los dynos
3. **Ir al panel admin** y click en "Generar"
4. **Copiar y pegar** TODOS los logs que aparezcan aquí
5. **Analizar** logs con esta guía

## Notas Importantes

- PostgreSQL es la configuración por defecto en producción
- ChromaDB solo se usa si `VECTOR_STORE_BACKEND=chroma` explícitamente
- Los logs son muy verbosos ahora para debugging
- Una vez identificado el problema, se pueden reducir los logs

---

**Fecha**: 16 de Noviembre de 2025  
**Objetivo**: Identificar por qué los embeddings no persisten en Heroku  
**Status**: Logs detallados implementados, esperando deployment
