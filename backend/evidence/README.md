# Evidencias del Feedback Loop

Este directorio se generó automáticamente ejecutando:

```powershell
cd "C:\Users\amaya\Downloads\10mo Ciclo\nisira-assistant\backend"
C:/Users/amaya/AppData/Local/Microsoft/WindowsApps/python3.13.exe manage.py shell -c "import evidence.generate_feedback_evidence"
```

El script `generate_feedback_evidence.py` siembra datos mínimos y exporta los artefactos necesarios para documentar el estado del feedback loop.

## Artefactos producidos

- `rating_summary.json`: snapshot del endpoint `/api/ratings/summary/` incluyendo métricas agragadas, breakdown por issue_tag y el último experimento registrado.
- `ratings_export.json`: exportación en formato JSON del endpoint `/api/ratings/export/`.
- `ratings_export.csv`: exportación en formato CSV del endpoint `/api/ratings/export/`.
- `guardrail_status.json`: resultado del endpoint `/api/guardrails/status/` con el estado actual de los guardrails.

Cada archivo está listo para adjuntar como evidencia en el backlog (historia EP-005). Si necesitas regenerarlos, vuelve a ejecutar el comando anterior.
