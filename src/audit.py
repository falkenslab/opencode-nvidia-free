"""Auditoría del catálogo gratuito de NVIDIA Build que ofrece OpenCode.

Toma de Models.dev (el catálogo del que OpenCode saca sus proveedores) los modelos del
proveedor `nvidia` con tool calling y coste 0, y lanza una petición mínima (max_tokens=1)
a cada uno contra la API de NVIDIA. Registra si responde, si está retirado (410) y cuánto tarda.

Ritmo: como mucho una petición nueva cada PACE_S segundos (por defecto 2 s, ~30/min, por
debajo del límite gratuito) y hasta WORKERS en paralelo, con REQ_TIMEOUT segundos de espera.

Uso: python audit.py <salida.jsonl>
Requiere NVIDIA_API_KEY. Guarda también la entrada de Models.dev usada en <salida>.models-dev.json.
"""
import http.client
import json
import os
import re
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

out = sys.argv[1]
key = os.environ["NVIDIA_API_KEY"]
PACE_S = float(os.environ.get("PACE_S", "2"))
WORKERS = int(os.environ.get("WORKERS", "6"))
REQ_TIMEOUT = int(os.environ.get("REQ_TIMEOUT", "60"))

req = urllib.request.Request("https://models.dev/api.json", headers={"User-Agent": "opencode-nvidia-free-audit/1.0"})
with urllib.request.urlopen(req, timeout=60) as r:
    catalog = json.load(r)["nvidia"]
models = {k: v for k, v in catalog["models"].items()
          if v.get("tool_call") and (v.get("cost") or {}).get("input", 0) == 0
          and (v.get("cost") or {}).get("output", 0) == 0}
with open(out + ".models-dev.json", "w", encoding="utf-8") as f:
    json.dump({"fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "provider": {k: v for k, v in catalog.items() if k != "models"},
               "models": models}, f, ensure_ascii=False, indent=1)
print(f"{len(models)} modelos gratuitos con tool calling en Models.dev", flush=True)

lock = threading.Lock()
next_slot = [time.monotonic()]


def wait_turn():
    with lock:
        now = time.monotonic()
        slot = max(now, next_slot[0])
        next_slot[0] = slot + PACE_S
    time.sleep(max(0, slot - time.monotonic()))


def probe(model_id: str) -> dict:
    wait_turn()
    meta = models[model_id]
    entry = {"model": model_id, "models_dev_status": meta.get("status"),
             "release_date": meta.get("release_date"), "context": (meta.get("limit") or {}).get("context"),
             "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    body = json.dumps({"model": model_id, "messages": [{"role": "user", "content": "ok"}], "max_tokens": 1})
    conn = http.client.HTTPSConnection("integrate.api.nvidia.com", timeout=REQ_TIMEOUT)
    t0 = time.monotonic()
    try:
        conn.request("POST", "/v1/chat/completions", body=body,
                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        resp = conn.getresponse()
        data = resp.read()
        entry["status"] = resp.status
        if resp.status >= 400:
            text = data[:500].decode("utf-8", "replace")
            entry["error_body"] = text
            m = re.search(r"end of life on (\d{4}-\d{2}-\d{2})", text)
            if m:
                entry["end_of_life"] = m.group(1)
    except Exception as exc:
        entry["status"] = None
        entry["error"] = repr(exc)
    finally:
        conn.close()
    entry["latency_s"] = round(time.monotonic() - t0, 2)
    state = ("vivo" if entry["status"] == 200 else "retirado" if entry["status"] == 410
             else "sin respuesta" if entry["status"] is None else f"error {entry['status']}")
    entry["state"] = state
    print(f"{state:14} {entry['latency_s']:7.2f}s  {model_id}", flush=True)
    return entry


with ThreadPoolExecutor(WORKERS) as pool:
    results = list(pool.map(probe, sorted(models)))

with open(out, "w", encoding="utf-8") as f:
    for e in results:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

counts = {}
for e in results:
    counts[e["state"]] = counts.get(e["state"], 0) + 1
print(f"\nResumen: {counts} de {len(results)}")
