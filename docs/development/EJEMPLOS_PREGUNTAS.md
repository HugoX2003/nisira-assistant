# 📝 Ejemplos de Preguntas: Simples vs Complejas

## 🟢 Preguntas SIMPLES (Complejidad baja < 0.5)

Características:
- Una sola pregunta
- Información directa
- Respuesta breve esperada
- No requiere análisis profundo

### Ejemplos:

1. **¿Qué es ISO 27001?**
   - Score esperado: ~0.2
   - Respuesta directa de definición

2. **Dame ejemplos de controles de seguridad**
   - Score esperado: ~0.25
   - Lista simple de ejemplos

3. **¿Cuál es el objetivo de la norma ISO 27002?**
   - Score esperado: ~0.3
   - Pregunta directa sobre un objetivo

4. **Menciona 3 principios de seguridad de la información**
   - Score esperado: ~0.35
   - Lista específica y limitada

5. **¿Qué significa SGSI?**
   - Score esperado: ~0.15
   - Definición de acrónimo

---

## 🔴 Preguntas COMPLEJAS (Complejidad alta >= 0.5)

Características:
- Múltiples preguntas o aspectos
- Requiere análisis comparativo
- Palabras clave complejas (comparar, explicar detalladamente, por qué, cómo funciona)
- Respuesta extensa esperada
- Contexto multifacético

### Ejemplos:

1. **¿Cuál es la diferencia entre ISO 27001 e ISO 27002 y cómo se complementan?**
   - Score esperado: ~0.68
   - Factores: Múltiples preguntas, palabra clave "diferencia", comparación

2. **¿Cómo implementar un sistema de gestión de seguridad de la información según ISO 27001?**
   - Score esperado: ~0.82
   - Factores: Palabra clave "cómo funciona/implementar", proceso paso a paso

3. **Explica detalladamente el proceso de análisis y evaluación de riesgos en ISO 27001**
   - Score esperado: ~0.75
   - Factores: "Explica detalladamente", proceso complejo

4. **¿Por qué es importante la ISO 27001 para las empresas y qué beneficios aporta a nivel organizacional y técnico?**
   - Score esperado: ~0.85
   - Factores: Múltiples preguntas, "por qué", múltiples dimensiones

5. **Compara las metodologías de gestión de riesgos OCTAVE, MAGERIT y ISO 27005, analizando sus ventajas y desventajas**
   - Score esperado: ~0.95
   - Factores: "Comparar", "analizar", múltiples elementos, evaluación crítica

6. **¿Cómo se relacionan los controles del Anexo A de ISO 27001 con los requisitos de GDPR y qué controles adicionales se necesitan?**
   - Score esperado: ~0.88
   - Factores: Relación entre estándares, múltiples preguntas, análisis de gaps

---

## 🎯 Cómo el Sistema Calcula la Complejidad

El sistema analiza:

1. **Longitud de la consulta** (caracteres)
2. **Número de preguntas** (múltiples `?`)
3. **Palabras clave complejas**:
   - comparar / diferencia
   - analizar
   - explicar detalladamente
   - por qué
   - cómo funciona / cómo implementar

### Fórmula de Complejidad:

```
complexity_score = base_score + length_factor + keyword_bonus

donde:
- base_score: 0.1 - 0.4 (según longitud)
- length_factor: +0.1 por cada 50 caracteres extra
- keyword_bonus: +0.15 por cada palabra clave compleja encontrada
```

### Umbral de Complejidad:

- **Score < 0.5**: Consulta Simple 🟢
- **Score >= 0.5**: Consulta Compleja 🔴

---

## 💡 Recomendaciones para Testing

Para probar el sistema de métricas:

1. **Empieza con preguntas simples** para verificar tiempos base
2. **Prueba preguntas complejas** para ver diferencias en rendimiento
3. **Mezcla ambos tipos** para obtener estadísticas variadas
4. **Observa cómo cambian las métricas**:
   - Precision/Recall con preguntas específicas vs generales
   - Faithfulness con preguntas que requieren datos precisos
   - Answer Relevancy con preguntas bien vs mal formuladas

### Ejemplos de Test Rápido:

```
# Simple
"¿Qué es seguridad de la información?"

# Media
"Explica los 3 pilares de la seguridad: confidencialidad, integridad y disponibilidad"

# Compleja
"¿Cómo se relacionan los controles de ISO 27001 Anexo A con los requisitos de GDPR y qué controles adicionales se necesitan para cumplir con ambas normativas?"
```

---

## 📊 Métricas Esperadas por Tipo

| Métrica | Simple | Compleja |
|---------|--------|----------|
| Latencia Total | 2-5s | 5-15s |
| TTFT | 0.4-0.8s | 1.0-2.0s |
| Docs Recuperados | 3-5 | 5-8 |
| Precision | 60-80% | 40-70% |
| Recall | 40-60% | 60-80% |
| Faithfulness | 80-95% | 70-90% |
| Hallucination | 5-20% | 10-30% |
| Relevancy | 85-95% | 75-90% |

---

¡Usa estos ejemplos para probar el sistema de métricas detalladas! 🚀
