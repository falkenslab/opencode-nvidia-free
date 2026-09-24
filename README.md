# OpenCode con los LLM gratuitos de NVIDIA Build

> Experimento del [Cuaderno del Dr. Falken](https://falkenslab.github.io/falkens-notebook). Idea original: falkenslab/falkens-notebook#15

## Idea

NVIDIA Build (build.nvidia.com) ofrece acceso gratuito, para prototipado, a decenas de modelos abiertos a través de una API compatible con OpenAI. OpenCode trae `nvidia` como proveedor predefinido vía Models.dev, con 62 modelos de chat gratuitos y con tool calling. ¿Sirven de verdad como agente de código, y con qué límites?

Tres preguntas:

1. ¿Funciona el proveedor `nvidia` predefinido tal cual? Hay un fallo abierto (anomalyco/opencode#49240): la V2 de OpenCode envía `prompt_cache_key` y NVIDIA lo rechaza.
2. ¿Qué modelos gratuitos completan una tarea de código como agente, usando herramientas?
3. ¿Aguanta el límite del acceso gratuito (unas 40 peticiones por minuto, según terceros)?

## Hipótesis

- Con OpenCode estable (1.18.32), el proveedor `nvidia` funciona configurando solo `NVIDIA_API_KEY`.
- **Al menos 3 de los 5 modelos** completan la tarea (los tests pasan al terminar) sin recibir errores 429 por límite de peticiones.
- Con la V2 (canal `dev` de npm), las peticiones fallan por `prompt_cache_key`, y quitar el parámetro con un proxy lo arregla.
- El límite gratuito está en torno a 40 peticiones por minuto: la petición 41 dentro del mismo minuto devuelve 429.

Se confirma o se refuta con: `pytest` al final de cada ejecución, los códigos HTTP y parámetros registrados por el proxy, y el número de peticiones por minuto.

## Requisitos

- **Docker Desktop** (todo se ejecuta en contenedores; nada se instala en el sistema anfitrión).
- **`NVIDIA_API_KEY`** en el entorno del anfitrión: cuenta gratuita en build.nvidia.com → *Get API Key*. Se pasa al contenedor con `-e` y nunca se escribe en el repo.
- Conexión a internet. No hace falta GPU.
- Modelos (gratuitos y con tool calling según Models.dev, septiembre de 2026):
  - `moonshotai/kimi-k3` (en lugar de `kimi-k2.6`, que Models.dev marca como obsoleto y OpenCode ya no ofrece)
  - `qwen/qwen3-coder-480b-a35b-instruct`
  - `z-ai/glm-5.3`
  - `openai/gpt-oss-120b`
  - `nvidia/nemotron-3-nano-30b-a3b`
- Consumo estimado: 150-400 peticiones en total.

## Cómo ejecutar

Requiere Docker y `NVIDIA_API_KEY` en el entorno (en Windows, el script la lee de las variables de usuario sin mostrarla).

```bash
git clone https://github.com/falkenslab/opencode-nvidia-free
cd opencode-nvidia-free
bash scripts/run.sh                 # las cuatro fases
bash scripts/run.sh audit stable    # o solo algunas: audit, stable, dev, ratelimit
```

| Fase | Qué hace |
|---|---|
| `audit` | `src/audit.py`: una petición mínima (`max_tokens=1`) a cada modelo gratuito con tool calling del proveedor `nvidia` de Models.dev, a unas 30 peticiones por minuto. |
| `stable` | Construye OpenCode 1.18.32 (`src/runner/Dockerfile`) y ejecuta la tarea con cada modelo de `MODELS` a través del proxy (`src/proxy/proxy.py`). |
| `dev` | Lo mismo con OpenCode del canal `dev` de npm, primero tal cual y después con el proxy quitando `prompt_cache_key`. |
| `ratelimit` | `src/ratelimit.py`: 60 peticiones mínimas seguidas contra un modelo, directamente a la API. |

La tarea está en `task/`: implementar `slugify()` para que pasen los 15 tests de `test_slugify.py`. Cada modelo la recibe en un espacio de trabajo limpio con este prompt, en `opencode run --pure --auto --format json`:

> Implementa la función slugify en slugify.py para que pasen todos los tests de test_slugify.py. Ejecuta pytest para comprobarlo y corrige hasta que pasen. No modifiques test_slugify.py.

Dentro del contenedor OpenCode tiene todos los permisos (`src/runner/opencode.json`) y el proveedor `nvidia` apunta al proxy (`baseURL: {env:NVIDIA_BASE_URL}`). Después de cada ejecución se pasa `pytest` y se comprueba que `test_slugify.py` no ha cambiado.

## Resultados

Ejecución del 2026-09-24 (entorno en [`ENV.md`](ENV.md), salida completa en [`results/`](results/)).

**1. El proveedor `nvidia` funciona tal cual.** Con OpenCode 1.18.32 basta con `NVIDIA_API_KEY`: ninguna petición falló por configuración. Ni la 1.18.32 ni la compilación `dev` (`0.0.0-dev-202609241927`) envían `prompt_cache_key` (`2026-09-24-proxy.jsonl`), así que el fallo de anomalyco/opencode#49240 no se reproduce; quitar el parámetro con el proxy no cambia nada.

**2. El catálogo gratuito que ofrece OpenCode está muy desfasado.** De los 62 modelos gratuitos con tool calling que Models.dev lista para `nvidia` (`2026-09-24-audit.jsonl`):

| Estado | Modelos |
|---|---|
| Responde (200) | 6 |
| Retirado (410 Gone, con fecha de fin de vida entre mayo y septiembre de 2026) | 39 |
| No encontrado para la cuenta (404) | 11 |
| Sin respuesta en 60 s | 4 |
| Error del servidor (500 y 503) | 2 |

Entre los retirados están `openai/gpt-oss-120b` (3 de septiembre), `qwen/qwen3-coder-480b-a35b-instruct` (11 de junio), `nvidia/nemotron-3-nano-30b-a3b` (1 de septiembre) y `meta/llama-3.1-8b-instruct` (26 de agosto). Kimi K3 respondió en una prueba aparte, pero tardó 162 s en devolver un token.

**3. Cuatro de los cinco modelos vivos completan la tarea como agente** (`2026-09-24-summary.csv`):

| Modelo | Tests | Tiempo | Peticiones | Llamadas a herramientas |
|---|---|---|---|---|
| `z-ai/glm-5.3` | 15/15 | 38 s | 5 | 4 |
| `nvidia/nemotron-3.5-lightning-30b-a3b` | 15/15 | 93 s | 10 | 10 |
| `z-ai/glm-5.3-flash` | 15/15 | 106 s | 5 | 4 |
| `poolside/laguna-xs-2.1` | 15/15 | 305 s | 15 | 6 |
| `meta/muse-glimmer-30b` | 0/15 | 13 s | 2 | 0 |

Ningún modelo modificó los tests. Muse Glimmer no llegó a usar herramientas: devolvió la llamada como texto con etiquetas mal formadas (`<atem:parameter name="filePath">…`) en lugar de `tool_calls`, y OpenCode lo tomó como respuesta final.

La V2 (`dev`) con Nemotron 3.5 Lightning también completó la tarea (15/15 en 152 s, y 41 s en la repetición con el proxy quitando `prompt_cache_key`).

**4. El límite gratuito no molesta a un agente.** Durante la tarea ningún modelo pasó de 10 peticiones en un minuto, y no hubo ningún 429. En la prueba del límite, 60 peticiones seguidas en 58 s a `meta/llama-3.2-11b-vision-instruct` devolvieron todas 200 (`2026-09-24-ratelimit.jsonl`). La API no devuelve cabeceras de rate limit.

## Conclusiones

- **La hipótesis se confirma en lo importante**: el proveedor `nvidia` de OpenCode funciona sin configurar nada más que la clave, y 4 de 5 modelos gratuitos resuelven una tarea de código real como agentes, con GLM 5.3 como el más rápido.
- **Se refuta en dos puntos**: el fallo de `prompt_cache_key` ya no ocurre (ni en estable ni en `dev`), y el límite de 40 peticiones por minuto que repiten los artículos no aparece a 60 por minuto.
- **La sorpresa es el catálogo**: de "62 modelos gratis", solo 6 responden. La mayoría están retirados por NVIDIA pero siguen en Models.dev, y OpenCode los ofrece igual; al elegir uno, el error es un 410 que no explica nada en la interfaz. Hay que comprobar el catálogo real en build.nvidia.com/models antes de elegir modelo.
- **"Tool calling nativo" en la ficha no garantiza que funcione con un agente**: Muse Glimmer lo anuncia y no lo hace bien a través del endpoint alojado.
- **Queda por probar**: tareas más largas (donde el límite sí podría notarse), el consumo de créditos (la API no lo informa) y modelos que NVIDIA ya sirve pero Models.dev aún no lista, como `deepseek-ai/deepseek-v4.1-flash`, declarándolos a mano en `opencode.json`.
