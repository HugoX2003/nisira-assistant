# Runbook de Disponibilidad

Este documento describe los procedimientos para monitorear la salud del asistente, atender incidentes y programar ventanas de mantenimiento. El objetivo es sostener un uptime ≥ 95 % en horario laboral.

## 1. Componentes Clave

| Servicio        | Healthcheck                | Acción correctiva primaria                          |
|-----------------|----------------------------|------------------------------------------------------|
| API Django      | `GET /status/` → `services.api`  | Revisar logs de Django (`backend/logs`), reiniciar gunicorn/uvicorn |
| Worker Drive    | `GET /status/` → `services.worker` | Validar credenciales Google Drive, renovar token con `python manage.py start_drive_sync --action setup` |
| Base de datos   | `GET /status/` → `services.database` | Verificar instancia MySQL/SQLite, restablecer conexión, ejecutar migraciones |
| Vector DB       | `GET /status/` → `services.vector_db` | Confirmar permisos sobre `backend/chroma_db`, rehidratar colección y reiniciar servicio |

## 2. Monitoreo y Alertas

1. Configurar un monitor HTTP (UptimeRobot, BetterStack, etc.) apuntando a `https://<host>/status/`.
2. Activar alerta crítica si `status != "healthy"` o el campo degradado coincide con `database` o `vector_db` durante más de 5 minutos.
3. Objetivo SLO: disponibilidad ≥ 95 % (expuesto como `uptime_slo_target` en el endpoint).

## 3. Procedimiento de Incidentes

1. **Detección:** Alertas del monitor externo o dashboards internos muestran `status` degradado.
2. **Clasificación:** Usar la matriz del punto 1 para identificar el componente afectado.
3. **Mitigación rápida:**
   - API caída → reiniciar servicio (`systemctl restart nisira-api` o `docker compose restart backend`).
   - Worker sin autenticación → regenerar token (`python manage.py start_drive_sync --action setup`).
   - DB sin respuesta → restaurar conexión, verificar credenciales, aplicar migraciones.
   - Vector DB degradado → validar disco, ejecutar `python manage.py rag_manage reindex` si es necesario.
4. **Comunicación:** Registrar en el canal de incidentes con hora de inicio, causa provisional y acciones.
5. **Resolución:** Confirmar `status == "healthy"` y adjuntar captura del endpoint.
6. **Post-mortem:** Documentar causa raíz y medidas preventivas en la herramienta de seguimiento (backlog).

## 4. Ventanas de Mantenimiento

- **Frecuencia sugerida:** semanal, fuera de horario laboral (20:00–22:00).
- **Aviso previo:** comunicar con 24 h de anticipación el detalle de trabajos.
- **Checklist:**
  1. Ejecutar `python manage.py check` y `npm run lint` (si aplica) antes de iniciar trabajos.
  2. Respaldar `backend/chroma_db` y `backend/db.sqlite3`.
  3. Aplicar migraciones y despliegue.
  4. Validar `GET /status/` y pruebas de humo del chat.
  5. Documentar tiempos reales en el backlog.

## 5. Pruebas de Caos Básicas

Se automatizaron escenarios unitarios para verificar la detección de fallos:

```bash
cd backend
venv\Scripts\python.exe manage.py test api.tests.ChaosHealthChecksTests
```

Escenarios cubiertos:
- Caída del Vector DB (simulada) → el endpoint marca `vector_db.ok = False`.
- Caída del motor de base de datos (simulada) → `database.ok = False` con detalle del error.
- Validación del estado agregado (`healthy`, `degraded`, `down`).

Como prueba manual adicional, se recomienda detener temporalmente la base de datos o renombrar `backend/chroma_db` (con backup previo) en un entorno de staging para validar la respuesta del monitor externo.

## 6. Evidencias Requeridas

Para cerrar incidentes o auditorías, guardar:
- Captura del endpoint `/status/` (antes y después).
- Logs relevantes (`backend/logs` o consola de despliegue).
- Resultado de los tests de caos (captura de la consola con el comando anterior).
- Registro del backlog con tiempos de intervención y responsables.
