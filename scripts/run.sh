#!/usr/bin/env bash
# Ejecuta las fases del experimento desde el anfitrión.
# Uso: scripts/run.sh [audit] [stable] [dev] [ratelimit]   (sin argumentos: las cuatro)
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
  z-ai/glm-5.3
  nvidia/nemotron-3.5-lightning-30b-a3b
  poolside/laguna-xs-2.1
  meta/muse-glimmer-30b
  z-ai/glm-5.3-flash
)
DEV_MODEL="nvidia/nemotron-3.5-lightning-30b-a3b"
RATELIMIT_MODEL="meta/llama-3.2-11b-vision-instruct"
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

run_audit() {
  docker compose run --rm --no-deps -e NVIDIA_API_KEY proxy     python -u /app/audit.py "/results/${RUN_DATE}-audit.jsonl"
  redact
}

# Los errores 404 de NVIDIA incluyen un identificador de la cuenta: se anonimiza en los resultados.
redact() {
  sed -i -E "s/for account '[^']+'/for account '<redacted>'/g" results/${RUN_DATE}-*.jsonl results/${RUN_DATE}-*.log 2>/dev/null || true
}

run_ratelimit() {
  sleep "$PAUSE_S"
  docker compose run --rm --no-deps -e NVIDIA_API_KEY proxy \
    python -u /app/ratelimit.py "$RATELIMIT_MODEL" 60 "/results/${RUN_DATE}-ratelimit.jsonl"
}

PHASES=("$@")
[ ${#PHASES[@]} -eq 0 ] && PHASES=(audit stable dev ratelimit)
for p in "${PHASES[@]}"; do
  echo "=== fase: $p ($(date -u +%H:%M:%SZ))"
  "run_$p"
done
docker compose down >/dev/null 2>&1 || true
redact
echo "=== fin ($(date -u +%H:%M:%SZ)). Resultados en results/${RUN_DATE}-*"
