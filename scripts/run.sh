#!/usr/bin/env bash
# Ejecuta las fases del experimento desde el anfitrión.
# Uso: scripts/run.sh [stable] [dev] [ratelimit]   (sin argumentos: las tres)
#
# Necesita Docker y NVIDIA_API_KEY. Si la variable no está en el entorno y estamos en
# Windows, se lee de las variables de usuario sin mostrarla.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -z "${NVIDIA_API_KEY:-}" ] && command -v powershell.exe >/dev/null; then
  NVIDIA_API_KEY="$(powershell.exe -NoProfile -Command "[Environment]::GetEnvironmentVariable('NVIDIA_API_KEY','User')" | tr -d '\r')"
fi
: "${NVIDIA_API_KEY:?Define NVIDIA_API_KEY}"
export NVIDIA_API_KEY
export RUN_DATE="${RUN_DATE:-$(date +%F)}"
export MSYS_NO_PATHCONV=1

MODELS=(
  moonshotai/kimi-k3
  qwen/qwen3-coder-480b-a35b-instruct
  z-ai/glm-5.3
  openai/gpt-oss-120b
  nvidia/nemotron-3-nano-30b-a3b
)
DEV_MODEL="moonshotai/kimi-k3"
RATELIMIT_MODEL="meta/llama-3.1-8b-instruct"
PAUSE_S="${PAUSE_S:-65}"   # pausa entre ejecuciones para empezar cada una con la ventana de un minuto limpia

phase_start() {  # $1 = etiqueta del proxy, $2 = parámetros a quitar
  export PROXY_TAG="$1" STRIP_PARAMS="${2:-}"
  docker compose up -d --force-recreate proxy >/dev/null
  sleep 2
}
phase_end() { docker compose stop proxy >/dev/null; }

run_stable() {
  export OPENCODE_VERSION=1.18.32
  docker compose build runner
  phase_start stable
  for m in "${MODELS[@]}"; do
    docker compose run --rm runner run_model "$m" stable || true
    sleep "$PAUSE_S"
  done
  phase_end
}

run_dev() {
  export OPENCODE_VERSION=dev
  docker compose build --no-cache runner
  phase_start dev
  docker compose run --rm runner run_model "$DEV_MODEL" dev || true
  phase_end
  sleep "$PAUSE_S"
  phase_start dev-strip prompt_cache_key
  docker compose run --rm runner run_model "$DEV_MODEL" dev-strip || true
  phase_end
}

run_ratelimit() {
  sleep "$PAUSE_S"
  docker compose run --rm --no-deps -e NVIDIA_API_KEY proxy \
    python -u /app/ratelimit.py "$RATELIMIT_MODEL" 60 "/results/${RUN_DATE}-ratelimit.jsonl"
}

PHASES=("$@")
[ ${#PHASES[@]} -eq 0 ] && PHASES=(stable dev ratelimit)
for p in "${PHASES[@]}"; do
  echo "=== fase: $p ($(date -u +%H:%M:%SZ))"
  "run_$p"
done
docker compose down >/dev/null 2>&1 || true
echo "=== fin ($(date -u +%H:%M:%SZ)). Resultados en results/${RUN_DATE}-*"
