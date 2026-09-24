#!/usr/bin/env bash
# Ejecuta la tarea con un modelo y verifica el resultado.
# Uso: run_model <modelo> <fase>
#   <modelo>  id de NVIDIA Build, p. ej. moonshotai/kimi-k2.6 (se usa como nvidia/<modelo>)
#   <fase>    etiqueta para los ficheros de resultados, p. ej. stable o dev
# Variables: RUN_DATE (AAAA-MM-DD), TIMEOUT_S (por defecto 900).
set -u

MODEL="$1"
PHASE="$2"
SLUG="$(echo "$MODEL" | tr '/.' '--')"
OUT="/results/${RUN_DATE}-${PHASE}-${SLUG}"
WORK="/work/${PHASE}-${SLUG}"
TIMEOUT_S="${TIMEOUT_S:-900}"
PROMPT="Implementa la función slugify en slugify.py para que pasen todos los tests de test_slugify.py. Ejecuta pytest para comprobarlo y corrige hasta que pasen. No modifiques test_slugify.py."

rm -rf "$WORK" && cp -r /task "$WORK" && cd "$WORK"
git init -q && git add -A && git commit -qm "estado inicial"
TESTS_SHA_BEFORE="$(sha256sum test_slugify.py | cut -d' ' -f1)"

OPENCODE_VERSION="$(opencode --version 2>/dev/null | tail -1)"
START_ISO="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
START="$(date +%s)"
timeout "$TIMEOUT_S" opencode run --pure --auto --format json --print-logs -m "nvidia/${MODEL}" "$PROMPT" > "${OUT}.events.jsonl" 2> "${OUT}.opencode.log"
RC=$?
END="$(date +%s)"
END_ISO="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

python3 -m pytest -q -p no:cacheprovider > "${OUT}.pytest.log" 2>&1
PYTEST_RC=$?
PASSED="$(grep -oE '[0-9]+ passed' "${OUT}.pytest.log" | awk '{s+=$1} END {print s+0}')"
FAILED="$(grep -oE '[0-9]+ (failed|errors?)' "${OUT}.pytest.log" | awk '{s+=$1} END {print s+0}')"
TESTS_SHA_AFTER="$(sha256sum test_slugify.py | cut -d' ' -f1)"
TESTS_UNTOUCHED=$([ "$TESTS_SHA_BEFORE" = "$TESTS_SHA_AFTER" ] && echo yes || echo no)
git diff > "${OUT}.diff"

SUMMARY="/results/${RUN_DATE}-summary.csv"
[ -f "$SUMMARY" ] || echo "phase,model,opencode_version,start_utc,end_utc,duration_s,opencode_exit,pytest_exit,passed,failed,tests_untouched" > "$SUMMARY"
echo "${PHASE},${MODEL},${OPENCODE_VERSION},${START_ISO},${END_ISO},$((END-START)),${RC},${PYTEST_RC},${PASSED:-0},${FAILED:-0},${TESTS_UNTOUCHED}" >> "$SUMMARY"

echo "[${PHASE}] ${MODEL}: opencode=${RC} pytest=${PYTEST_RC} passed=${PASSED:-0} tests_untouched=${TESTS_UNTOUCHED} ($((END-START)) s)"
