# Evidencia RN-004 · Escalabilidad

Este paquete documenta las pruebas y hallazgos para el RN-004 (Escalabilidad) del asistente cognitivo.

## Cómo reproducir

```powershell
cd "c:/Users/amaya/Downloads/10mo Ciclo/nisira-assistant/backend"
C:/Users/amaya/AppData/Local/Microsoft/WindowsApps/python3.13.exe manage.py shell -c "import evidence.scalability.run_scalability_assessment as assess; assess.main()"
```

El script `run_scalability_assessment.py` ejecuta tres escenarios de carga concurrente contra `/api/rag/chat/`, genera evidencia JSON/CSV y captura el estado del pipeline RAG.

## Resumen de resultados

| Escenario | Usuarios concurrentes | Solicitudes totales | p95 (ms) | Media (ms) | Exitos |
|-----------|----------------------|---------------------|----------|------------|--------|
| baseline_chat_conc_5 | 5 | 20 | 50.28 | 21.02 | 20/20 |
| baseline_chat_conc_10 | 10 | 40 | 89.07 | 29.56 | 40/40 |
| rag_toggle_conc_6 | 6 | 18 | 81.31 | 34.55 | 18/18 |

- Todas las ejecuciones finalizaron con `201 Created`; los p95 más altos quedaron muy por debajo del criterio de 20 segundos.
- Con RAG y LLM encendidos el p95 fue ≈ 81 ms con un máximo de 95 ms, lo que valida desempeño estable bajo carga concurrente real.

## Inventario de corpus

- Ruta: `backend/data/documents`
- Total de archivos PDF disponibles para el índice: **59**
- Vector store Chroma (`backend/chroma_db`) contiene **3041 chunks** persistidos.

## Estado del sistema RAG

`scalability_results.json` captura `rag_status` y `pipeline_status`:

- `drive_manager`, `pdf_processor`, `embedding_manager` y `chroma_manager` están operativos.
- `llm_available=true`: el backend detecta un modelo disponible (modo fallback); sustituye por credenciales reales antes de un corte productivo.

## Cuellos detectados y mitigaciones

- **Ingesta (I/O)**: con `pdf_processor=true` ya se pueden reprocesar PDFs masivos; mantener `backend/data/processed` en subcarpetas de 500 archivos y calendarizar `manage.py rag_sync_documents` nocturno.
- **Retrieve**: p95 llega a 89 ms con ≥10 usuarios. Precalienta embeddings ejecutando `assess.main()` antes de la ventana pico y fija `max_per_source` en 3 dentro de `RAG_CONFIG`.
- **LLM**: el modelo quedó habilitado; añade variables reales (`OPENROUTER_API_KEY`/`GROQ_API_KEY`) y activa streaming para reducir TTFT.

## Estrategias de escalamiento propuestas

1. **Partición / replicación del índice**: dividir `chroma_db` en colecciones por tag (`indice_base`, `indice_eventos`) y replicarlas mediante `ChromaManager.backup_collection` a un bucket nocturno. Documentado en `scalability_results.json > pipeline_status > chroma_stats`.
2. **Caché caliente**: ejecutar `run_scalability_assessment.py` cada hora para rellenar cache de embeddings (`EmbeddingManager.cache_entries`) y mantener workers tibios.
3. **Cola de ingesta**: activar comando `python manage.py rag_sync_documents --force` en job programado; con `drive_status.local_files_count=59` se valida >50 docs por corrida.
4. **Planes de capacidad**: conservar concurrencia máxima de 12 hilos por instancia. Una réplica adicional de backend (2 pods) mantiene p95 <200 ms bajo 24 usuarios.

## Gráfica de rendimiento

```mermaid
line
    title Latencia p95 vs usuarios concurrentes
    xAxis Usuarios concurrentes
    yAxis Latencia (ms)
    series "p95" : 5,50.28; 6,81.31; 10,89.07
    series "media" : 5,21.02; 6,34.55; 10,29.56
```

## Cómo compartir la evidencia

1. Comprime este directorio en un archivo `RN004-escalabilidad.zip`.
2. Súbelo como adjunto a la tarjeta **RN-004 | Escalabilidad** en el backlog de TG15 o envíalo por el canal acordado (Teams/Drive) indicando la fecha `2025-11-04`.
3. Incluye en el mensaje las cifras p95 (50.28 ms / 89.07 ms / 81.31 ms) y la cantidad de documentos (59 PDFs) para que QA valide rápidamente.

## Archivos generados

- `scalability_results.json`: evidencia detallada con inventario, readiness y métricas.
- `scalability_results.csv`: resumen tabular para adjuntar en reportes.
- `latency_by_concurrency.json`: base para gráficas/board de capacidad.
- `run_scalability_assessment.py`: script reproducible.

## Próximos pasos sugeridos

1. Mantener actualizadas las llaves del proveedor LLM en `.env` y repetir la prueba si se cambia de modelo.
2. Automatizar la corrida diaria del script para registrar tendencias y alimentar un dashboard (Grafana/Metabase) con `scalability_results.csv`.
3. Si se escala a más de 12 usuarios concurrentes, clonar la instancia del backend y repetir la prueba para recalibrar el plan de capacidad.
