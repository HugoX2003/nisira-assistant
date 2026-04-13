# 📊 Sistema de Métricas del Asistente RAG

## ✅ Cambios Realizados

### **RAGAS Eliminado** ❌
- ❌ Dependencia de `ragas` removida
- ❌ Ya no requiere API keys (OpenAI/OpenRouter)
- ❌ Sin problemas de compatibilidad

### **Sistema Personalizado Implementado** ✅
- ✅ Evaluación sin dependencias externas
- ✅ Métricas calculadas localmente
- ✅ Sin costos de API

---

## 📈 Métricas Disponibles

### 🚀 **Métricas de Rendimiento** (Ya funcionando)

#### 1. **Tiempo de Respuesta Promedio** (`avgResponseTime`)
- **Qué mide**: Latencia total desde pregunta hasta respuesta completa
- **Fuente**: Base de datos `QueryMetrics`
- **Campo**: `total_latency`

#### 2. **Velocidad de Procesamiento** (`timeToFirstToken`)
- **Qué mide**: Tiempo hasta que el usuario ve el primer token de la respuesta
- **Fuente**: Base de datos `QueryMetrics`
- **Campo**: `time_to_first_token`
- **Importancia**: Usuario percibe rapidez si este valor es bajo

#### 3. **Tiempo de Resolución de Consultas Complejas** (`complexQueryTime`)
- **Qué mide**: Latencia promedio solo para consultas clasificadas como complejas
- **Fuente**: Base de datos `QueryMetrics` WHERE `is_complex_query=True`
- **Campo**: `total_latency`
- **Clasificación**: Automática basada en longitud, palabras clave, múltiples preguntas

---

### 🎯 **Métricas de Precisión** (Sistema Personalizado)

#### 4. **Precision@k** (`precisionAtK`)
- **Qué mide**: ¿Cuántos de los K documentos recuperados fueron realmente útiles?
- **Rango**: 0.0 - 1.0 (mayor es mejor)
- **Método**: 
  - Calcula overlap semántico (Jaccard similarity) entre cada contexto y la respuesta
  - Si overlap > 20%, el documento se considera relevante
  - `Precision@k = (documentos relevantes) / k`
- **Ejemplo**: Si k=5 y 4 documentos fueron útiles → Precision@5 = 0.80

#### 5. **Recall@k** (`recallAtK`)
- **Qué mide**: ¿La respuesta cubre información de múltiples contextos relevantes?
- **Rango**: 0.0 - 1.0 (mayor es mejor)
- **Método**:
  - Extrae frases clave de cada contexto (n-gramas de 3 palabras)
  - Verifica cuántos contextos tienen frases presentes en la respuesta
  - `Recall@k = (contextos cubiertos) / k`
- **Ejemplo**: Si k=5 y la respuesta usa info de 3 contextos → Recall@5 = 0.60

#### 6. **Faithfulness / Fidelidad** (`faithfulness`)
- **Qué mide**: ¿La respuesta está respaldada por el contexto? (sin inventar información)
- **Rango**: 0.0 - 1.0 (mayor es mejor)
- **Método**:
  - Divide la respuesta en oraciones
  - Para cada oración, extrae palabras clave
  - Verifica si >60% de las palabras clave están en el contexto
  - `Faithfulness = (oraciones respaldadas) / (total oraciones)`
- **Ejemplo**: Si 8 de 10 oraciones están respaldadas → Faithfulness = 0.80

#### 7. **Tasa de Alucinación** (`hallucinationRate`)
- **Qué mide**: ¿Cuánta información inventó el sistema?
- **Rango**: 0.0 - 1.0 (menor es mejor)
- **Fórmula**: `Hallucination Rate = 1.0 - Faithfulness`
- **Ejemplo**: Si Faithfulness = 0.80 → Hallucination Rate = 0.20 (20% inventado)

#### 8. **Answer Relevancy** (`answer_relevancy`)
- **Qué mide**: ¿La respuesta aborda la pregunta planteada?
- **Rango**: 0.0 - 1.0 (mayor es mejor)
- **Método**:
  - Extrae palabras clave de la pregunta
  - Verifica cuántas keywords están en la respuesta
  - Bonus si la respuesta tiene longitud razonable (20-300 palabras)
- **Ejemplo**: Si 7 de 10 keywords están presentes → Relevancy ≈ 0.70

#### 9. **WER (Word Error Rate)** (`wer`) - NUEVO ⭐
- **Qué mide**: Calidad de generación de texto comparado con referencia
- **Rango**: 0.0 - ∞ (menor es mejor, 0.0 es perfecto)
- **Método**: Distancia de Levenshtein entre texto generado y referencia
- **Fórmula**: `WER = (Sustituciones + Inserciones + Eliminaciones) / Palabras en referencia`
- **Uso**: Solo cuando hay ground truth disponible
- **Ejemplo**: Si hay 5 errores en 50 palabras → WER = 0.10

---

## 🔧 Implementación Técnica

### Archivos Modificados

1. **`api/custom_evaluator.py`** (NUEVO)
   - Clase `CustomMetricsEvaluator`
   - Métodos: `calculate_precision_at_k()`, `calculate_recall_at_k()`, `calculate_faithfulness()`, `calculate_wer()`
   - Sin dependencias externas, solo Python estándar

2. **`api/metrics_tracker.py`** (MODIFICADO)
   - Importa `custom_evaluator` en lugar de `ragas_evaluator`
   - Guarda métricas personalizadas en `RAGASMetrics` (nombre legacy)
   - Incluye WER cuando hay ground truth

3. **`api/models.py`** (MODIFICADO)
   - `RAGASMetrics` ahora incluye campo `wer_score`
   - Campos con defaults para evitar errores
   - Comentarios actualizados

4. **`api/admin_views.py`** (MODIFICADO)
   - Endpoint `/api/admin/metrics/` actualizado
   - Metadata indica `dataSource: "real_database_custom_metrics"`

### Base de Datos

```sql
-- Nueva columna agregada
ALTER TABLE api_ragasmetrics 
ADD COLUMN wer_score FLOAT NULL;

-- Campos actualizados con defaults
ALTER TABLE api_ragasmetrics 
ALTER COLUMN precision_at_k SET DEFAULT 0.0,
ALTER COLUMN recall_at_k SET DEFAULT 0.0,
ALTER COLUMN faithfulness_score SET DEFAULT 0.0,
ALTER COLUMN answer_relevancy SET DEFAULT 0.0,
ALTER COLUMN hallucination_rate SET DEFAULT 0.0;
```

---

## 📊 Cómo Ver las Métricas

### 1. **Panel de Administración** (Frontend)
```
http://localhost:3000/admin
Usuario: admin
Pestaña: 📊 Métricas
```

**Visualización:**
- ⏱️ Tiempo de Respuesta Promedio: `2.34s`
- ⚡ Velocidad de Procesamiento: `0.45s`
- 🧠 Tiempo Consultas Complejas: `3.12s`
- 🎯 Precision@k: `85%`
- 📋 Recall@k: `78%`
- ✅ Fidelidad (Faithfulness): `92%`
- ⚠️ Tasa de Alucinación: `8%`

### 2. **API Endpoint**
```http
GET /api/admin/metrics/
Authorization: Bearer <JWT_TOKEN>
```

**Respuesta:**
```json
{
  "success": true,
  "metrics": {
    "performance": {
      "avgResponseTime": 2.34,
      "timeToFirstToken": 0.45,
      "complexQueryTime": 3.12,
      "totalQueries": 156
    },
    "precision": {
      "precisionAtK": 0.85,
      "recallAtK": 0.78,
      "hallucinationRate": 0.08,
      "faithfulness": 0.92
    },
    "metadata": {
      "lastUpdated": "2025-11-14T03:50:00",
      "dataSource": "real_database_custom_metrics",
      "kValue": 5,
      "isRealData": true
    }
  }
}
```

### 3. **Base de Datos Directamente**
```python
from api.models import QueryMetrics, RAGASMetrics

# Ver métricas de rendimiento
QueryMetrics.objects.all().aggregate(
    avg_latency=Avg('total_latency'),
    avg_ttft=Avg('time_to_first_token')
)

# Ver métricas de precisión
RAGASMetrics.objects.all().aggregate(
    avg_precision=Avg('precision_at_k'),
    avg_faithfulness=Avg('faithfulness_score'),
    avg_wer=Avg('wer_score')
)
```

---

## 🧪 Cómo se Calculan (Ejemplo Real)

### Escenario: Usuario pregunta sobre ISO 27001

**Pregunta:** "¿Qué es ISO 27001 y cuáles son sus controles principales?"

**Respuesta generada:** "ISO 27001 es un estándar internacional de seguridad de la información..."

**Contextos recuperados (k=5):**
1. "ISO 27001 define requisitos para establecer, implementar..."
2. "Los controles de ISO 27001 incluyen gestión de acceso..."
3. "La norma ISO 27002 proporciona guías para implementar..."
4. "Documento sobre GDPR y privacidad de datos..."
5. "Manual de configuración de firewalls..."

### Cálculo de Métricas:

**Precision@5:**
- Contexto 1: Relevante ✅ (overlap 45%)
- Contexto 2: Relevante ✅ (overlap 38%)
- Contexto 3: Relevante ✅ (overlap 25%)
- Contexto 4: No relevante ❌ (overlap 5%)
- Contexto 5: No relevante ❌ (overlap 2%)
- **Resultado: 3/5 = 0.60** (60%)

**Recall@5:**
- Respuesta usa información de contextos 1, 2, 3
- **Resultado: 3/5 = 0.60** (60%)

**Faithfulness:**
- Respuesta tiene 8 oraciones
- 7 oraciones respaldadas por contextos
- 1 oración posiblemente inventada
- **Resultado: 7/8 = 0.875** (87.5%)

**Hallucination Rate:**
- **Resultado: 1 - 0.875 = 0.125** (12.5%)

**Answer Relevancy:**
- Pregunta tiene keywords: "ISO", "27001", "controles", "principales"
- Todas presentes en respuesta
- **Resultado: 4/4 = 1.0** (100%)

---

## ✨ Ventajas del Sistema Personalizado

1. ✅ **Sin API Keys**: No requiere OpenAI/OpenRouter
2. ✅ **Sin Costos**: Todo calculado localmente
3. ✅ **Rápido**: No hay latencia de llamadas a API externas
4. ✅ **Confiable**: Sin problemas de compatibilidad de versiones
5. ✅ **Transparente**: Código abierto, puedes ver cómo se calcula cada métrica
6. ✅ **Customizable**: Puedes ajustar thresholds y algoritmos
7. ✅ **Offline**: Funciona sin internet

---

## 🎓 Para tu Tesis

### Métricas Clave a Reportar:

**Rendimiento:**
- Tiempo de respuesta promedio: `X.XX segundos`
- Time to First Token: `X.XX segundos`
- Throughput: `XX consultas/minuto`

**Precisión:**
- Precision@5: `XX%` - Documentos recuperados relevantes
- Recall@5: `XX%` - Cobertura de información
- Faithfulness: `XX%` - Respuestas basadas en evidencia
- Hallucination Rate: `XX%` - Información inventada

**Calidad:**
- Answer Relevancy: `XX%` - Respuestas pertinentes
- WER: `X.XX` - Exactitud de generación (cuando aplique)

### Gráficas Sugeridas:
1. Line chart: Evolución de latencia en el tiempo
2. Bar chart: Comparación de precision/recall/faithfulness
3. Scatter plot: Relación entre complejidad de consulta y tiempo
4. Heatmap: Métricas por categoría de documento

---

## 🚀 Próximos Pasos

1. **Hacer consultas de prueba** para generar datos de métricas
2. **Verificar el panel de administración** para ver métricas en tiempo real
3. **Exportar datos** para análisis en tu tesis
4. **Ajustar thresholds** si es necesario (ej: cambiar 20% a 30% en precision)

---

## 📞 Soporte

- Documentación: Este archivo
- Código: `backend/api/custom_evaluator.py`
- Tests: Haz consultas y verifica en `/api/admin/metrics/`
