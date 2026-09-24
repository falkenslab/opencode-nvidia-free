# Entorno de ejecución

## Ejecución 2026-09-24

Pruebas de humo (`results/smoke-*`), auditoría del catálogo, tarea de código con 5 modelos, comparación con la V2 y prueba del límite (`results/2026-09-24-*`). Todo entre las 20:00 y las 23:05 UTC del 2026-09-24.

- **Sistema operativo (anfitrión):** Microsoft Windows 11 Education 10.0.26200, con Docker Desktop sobre WSL2 (kernel 6.6.87.2-microsoft-standard-WSL2).
- **CPU:** Intel Core i5-8265U @ 1,60 GHz (8 hilos visibles para Docker).
- **RAM:** 8 GB asignados a Docker.
- **GPU / VRAM:** ninguna. Toda la inferencia ocurre en NVIDIA Build (`https://integrate.api.nvidia.com/v1`).
- **Herramientas y versiones:**
  - Docker Engine 29.6.2 (linux/amd64).
  - Imagen de OpenCode: `node:22-bookworm-slim` (Node 22.23.3), Python 3.11.2, pytest 7.2.1.
  - OpenCode **1.18.32** (última estable, `npm install -g opencode-ai@1.18.32`) y **0.0.0-dev-202609241927** (canal `dev` de npm).
  - Proxy y scripts de auditoría y límite: `python:3.12-slim`.
- **Cuenta:** cuenta gratuita del NVIDIA Developer Program; clave `nvapi-…` pasada por variable de entorno.
- **Modelos:** ids de NVIDIA Build, servidos por NVIDIA (sin información de cuantización salvo GLM 5.3, que la ficha describe como NVFP4):
  - Tarea: `z-ai/glm-5.3`, `nvidia/nemotron-3.5-lightning-30b-a3b`, `poolside/laguna-xs-2.1`, `meta/muse-glimmer-30b`, `z-ai/glm-5.3-flash`.
  - V2: `nvidia/nemotron-3.5-lightning-30b-a3b`.
  - Límite: `meta/llama-3.2-11b-vision-instruct`.
  - Auditoría: los 62 modelos gratuitos con tool calling del proveedor `nvidia` en Models.dev (copia en `results/2026-09-24-audit.jsonl.models-dev.json`).
- **Observaciones:**
  - Los mensajes de error 404 de NVIDIA incluyen un identificador de la cuenta; se ha sustituido por `<redacted>` en los ficheros de resultados.
  - Entre fases se dejaron 65 s de pausa para empezar cada una con la ventana de un minuto limpia.
  - Los tiempos dependen de la carga del servicio gratuito en ese momento; pueden variar mucho de un día a otro.
