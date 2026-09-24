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

> Borrador: se concretará al implementar el experimento.

1. **Imagen**: `Dockerfile` con OpenCode en una versión fija (`OPENCODE_VERSION`: `1.18.32` o `dev`), Python y `pytest`. Dentro del contenedor, OpenCode con permisos totales para que no pida confirmaciones (está aislado).
2. **Proxy de registro** (`docker compose`): se interpone entre OpenCode y `https://integrate.api.nvidia.com/v1` y registra cada petición (hora, modelo, código HTTP, parámetros). Opcionalmente, quita `prompt_cache_key`.
3. **Tarea**: implementar una función pequeña en Python contra unos tests `pytest` ya escritos, en un espacio de trabajo limpio por modelo:

   ```bash
   docker compose run --rm -e NVIDIA_API_KEY opencode \
     opencode run -m nvidia/<modelo> "<tarea>"
   ```

   Tiempo máximo: 15 minutos por modelo. Después, `pytest` para verificar.
4. **V2**: repetir la tarea con un modelo y `OPENCODE_VERSION=dev`, con y sin el proxy que quita `prompt_cache_key`.
5. **Límite**: ráfaga de unas 60 peticiones mínimas en un minuto contra un modelo, registrando en qué petición aparece el 429.
6. Guardar todo en `results/` (logs de OpenCode, log del proxy, salida de `pytest`, CSV resumen) y el entorno en `ENV.md`.

## Resultados

Resumen de lo que salió. La salida completa y sin editar está en [`results/`](results/); el entorno exacto en [`ENV.md`](ENV.md).

## Conclusiones

Qué se aprende. ¿Se confirma la hipótesis? ¿Qué sorprendió? ¿Qué quedaría por probar?
