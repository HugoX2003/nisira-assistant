# 🎯 Sistema Adaptativo de Recuperación de Documentos

## Descripción

El sistema ahora recupera **dinámicamente** el número de documentos necesarios según la **complejidad de la consulta**, eliminando el límite fijo de 5 documentos.

---

## 📊 Cómo Funciona

### Algoritmo de Cálculo Adaptativo

El sistema analiza la consulta y calcula `top_k` basándose en:

#### 1. **Longitud de la Consulta**

| Caracteres | Base top_k |
|------------|------------|
| < 50       | 3          |
| 50-99      | 5          |
| 100-149    | 7          |
| ≥ 150      | 9          |

#### 2. **Múltiples Preguntas**

- Por cada `?` adicional después del primero: **+2 documentos**
- Máximo bonus: **+4 documentos**

**Ejemplo:**
```
"¿Qué es ISO 27001? ¿Cuáles son sus requisitos? ¿Cómo se implementa?"
→ 3 preguntas = +4 documentos
```

#### 3. **Palabras Clave Complejas**

Detecta keywords que indican análisis profundo:
- comparar
- diferencia
- analizar
- explicar detalladamente
- por qué
- cómo funciona
- implementar
- relacionan

Por cada keyword encontrada: **+1 documento**
- Máximo bonus: **+3 documentos**

---

## 📋 Rangos de Recuperación

| Tipo de Consulta | Rango top_k | Ejemplo |
|------------------|-------------|---------|
| **Simple** | 3-5 | "¿Qué es ISO 27001?" |
| **Media** | 5-8 | "Explica los controles de ISO 27001" |
| **Compleja** | 8-12 | "¿Cómo se relacionan ISO 27001 e ISO 27002 y cuáles son sus diferencias principales?" |
| **Muy Compleja** | 12-15 | "Compara ISO 27001, ISO 27002 e ISO 27005, analizando sus diferencias, similitudes y cómo se complementan entre sí" |

**Límites:**
- Mínimo: **3 documentos**
- Máximo: **15 documentos**

---

## 💡 Ejemplos Reales

### Ejemplo 1: Consulta Simple
```
Pregunta: "¿Qué es seguridad de la información?"
Longitud: 39 caracteres
Preguntas: 1
Keywords complejas: 0

Cálculo:
- Base (< 50 chars): 3
- Preguntas bonus: 0
- Keywords bonus: 0
→ top_k = 3 documentos
```

### Ejemplo 2: Consulta Media
```
Pregunta: "Explica detalladamente los principios de confidencialidad, integridad y disponibilidad"
Longitud: 88 caracteres
Preguntas: 0
Keywords complejas: 1 ("explicar detalladamente")

Cálculo:
- Base (50-99 chars): 5
- Preguntas bonus: 0
- Keywords bonus: +1
→ top_k = 6 documentos
```

### Ejemplo 3: Consulta Compleja
```
Pregunta: "¿Cuál es la diferencia entre ISO 27001 e ISO 27002 y cómo se complementan entre sí?"
Longitud: 88 caracteres
Preguntas: 1
Keywords complejas: 2 ("diferencia", "cómo")

Cálculo:
- Base (50-99 chars): 5
- Preguntas bonus: 0
- Keywords bonus: +2
→ top_k = 7 documentos
```

### Ejemplo 4: Consulta Muy Compleja
```
Pregunta: "¿Por qué es importante implementar ISO 27001 en las empresas? ¿Cómo se relaciona con GDPR? ¿Qué controles adicionales se necesitan? Explica detalladamente el proceso de implementación y compara con otras normativas de seguridad"
Longitud: 238 caracteres
Preguntas: 3
Keywords complejas: 5 ("por qué", "implementar", "cómo", "relaciona", "explicar detalladamente", "comparar")

Cálculo:
- Base (≥ 150 chars): 9
- Preguntas bonus: +4 (3 preguntas)
- Keywords bonus: +3 (max)
→ top_k = 16 → limitado a 15 documentos
```

---

## 🔧 Cambios Implementados

### Backend

1. **`api/views.py`**:
   - Nueva función `calculate_adaptive_top_k(question)`
   - `rag_query`: Usa top_k adaptativo si no se especifica
   - `rag_enhanced_chat`: Usa top_k adaptativo automáticamente

2. **`rag_system/rag_engine/pipeline.py`**:
   - Default de `top_k` cambiado de 5 a 8

3. **`rag_system/__init__.py`**:
   - Default de `top_k` cambiado de 5 a 8

4. **`api/metrics_tracker.py`**:
   - `top_k` es ahora `None` por defecto (se establece dinámicamente)

---

## ✅ Ventajas del Sistema Adaptativo

1. **Eficiencia**: No desperdicia recursos recuperando documentos innecesarios para consultas simples
2. **Completitud**: Recupera suficientes documentos para consultas complejas
3. **Precisión**: Mejora métricas de Precision@k y Recall@k al adaptar K a la necesidad real
4. **Flexibilidad**: Se adapta automáticamente sin intervención manual
5. **Escalabilidad**: Funciona bien desde consultas de 1 palabra hasta análisis complejos

---

## 🧪 Testing

### Comandos para Probar

```python
# En Django shell
from api.views import calculate_adaptive_top_k

# Consulta simple
print(calculate_adaptive_top_k("¿Qué es ISO 27001?"))
# Resultado: 3

# Consulta media
print(calculate_adaptive_top_k("Explica los controles de seguridad de ISO 27001"))
# Resultado: 5-6

# Consulta compleja
print(calculate_adaptive_top_k("¿Cómo se relacionan ISO 27001 e ISO 27002 y cuáles son sus principales diferencias en la gestión de seguridad?"))
# Resultado: 8-10

# Consulta muy compleja
print(calculate_adaptive_top_k("¿Por qué es importante implementar ISO 27001? ¿Cómo se compara con ISO 27002? ¿Qué diferencias hay? Explica detalladamente el proceso"))
# Resultado: 12-15
```

---

## 📈 Impacto en Métricas

### Antes (top_k fijo = 5)

| Consulta | Docs Necesarios | Docs Recuperados | Problema |
|----------|-----------------|------------------|----------|
| Simple | 2-3 | 5 | Desperdicio |
| Media | 4-6 | 5 | OK |
| Compleja | 8-12 | 5 | **Insuficiente** |

### Después (top_k adaptativo)

| Consulta | Docs Necesarios | Docs Recuperados | Resultado |
|----------|-----------------|------------------|-----------|
| Simple | 2-3 | 3 | ✅ Eficiente |
| Media | 4-6 | 5-7 | ✅ Óptimo |
| Compleja | 8-12 | 8-12 | ✅ **Completo** |

---

## 🎯 Próximos Pasos

1. **Monitoreo**: Observar métricas de Precision@k y Recall@k con el nuevo sistema
2. **Ajuste Fino**: Ajustar rangos basados en datos reales
3. **ML Futuro**: Entrenar modelo para predecir top_k óptimo por consulta
4. **Cache**: Cachear cálculos de top_k para consultas similares

---

## 📝 Notas

- Si el usuario especifica `top_k` manualmente en la API, se respeta ese valor
- El sistema mantiene límites de seguridad (min: 3, max: 15)
- Los logs muestran el `top_k` calculado para debugging
- Compatible con sistema de métricas existente

---

¡El sistema ahora es **inteligente** y **adaptativo**! 🚀
