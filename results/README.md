# Resultados

Salida real y sin editar de las ejecuciones: logs, respuestas de los modelos, métricas, capturas.

Convención de nombres: `AAAA-MM-DD-<qué>.<ext>` (por ejemplo `2026-09-24-run.log`, `2026-09-24-metricas.csv`). Cada fecha debe tener su sección en `../ENV.md`.

Nunca se editan a mano ni se "limpian": si una ejecución falla, su log también es un resultado. Única excepción: los identificadores de cuenta que devuelve NVIDIA en los errores 404 se sustituyen por `<redacted>` (con `sed`, desde `scripts/run.sh`).

## Ficheros

| Fichero | Qué contiene |
|---|---|
| `smoke-proxy.jsonl` | Primera prueba de OpenCode a través del proxy (`openai/gpt-oss-120b`, 410). |
| `smoke-alive*-<modelo>.jsonl` | Una petición mínima a cada candidato inicial. |
| `2026-09-24-audit.jsonl` | Auditoría: una petición mínima a cada uno de los 62 modelos gratuitos con tool calling de Models.dev. |
| `2026-09-24-audit.jsonl.models-dev.json` | La entrada de Models.dev usada en la auditoría. |
| `2026-09-24-summary.csv` | Una fila por ejecución de la tarea: fase, modelo, versión de OpenCode, duración, salida de OpenCode y de pytest, tests superados y si los tests quedaron intactos. |
| `2026-09-24-<fase>-<modelo>.events.jsonl` | Eventos de `opencode run --format json`: pasos, llamadas a herramientas y texto. |
| `2026-09-24-<fase>-<modelo>.opencode.log` | Log de OpenCode (`--print-logs`). |
| `2026-09-24-<fase>-<modelo>.pytest.log` | Salida de pytest al terminar. |
| `2026-09-24-<fase>-<modelo>.diff` | Cambios que hizo el agente en el espacio de trabajo. |
| `2026-09-24-proxy.jsonl` | Una línea por petición de OpenCode a NVIDIA: fase, modelo, parámetros, código HTTP y duración. |
| `2026-09-24-ratelimit.jsonl` | Prueba del límite: 60 peticiones mínimas seguidas. |
