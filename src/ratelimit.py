"""Prueba del límite de peticiones del acceso gratuito de NVIDIA Build.

Lanza N peticiones mínimas (max_tokens=1), una detrás de otra y lo más rápido posible,
directamente contra la API (sin proxy), y registra por petición: número, segundos desde
el inicio, código HTTP, cabeceras de rate limit y, si hay error, el principio del cuerpo.

Uso: python ratelimit.py <modelo> <n_peticiones> <fichero_salida.jsonl>
Requiere NVIDIA_API_KEY en el entorno.
"""
import http.client
import json
import os
import sys
import time

model, n, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
key = os.environ["NVIDIA_API_KEY"]
body = json.dumps({"model": model, "messages": [{"role": "user", "content": "ok"}], "max_tokens": 1})
start = time.monotonic()
codes = {}

with open(out, "w", encoding="utf-8") as f:
    for i in range(1, n + 1):
        conn = http.client.HTTPSConnection("integrate.api.nvidia.com", timeout=int(os.environ.get("REQ_TIMEOUT", "60")))
        t0 = time.monotonic()
        try:
            conn.request("POST", "/v1/chat/completions", body=body,
                         headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            resp = conn.getresponse()
            data = resp.read()
            entry = {"i": i, "t_s": round(t0 - start, 3), "status": resp.status,
                     "latency_s": round(time.monotonic() - t0, 3),
                     "ratelimit": {k.lower(): v for k, v in resp.getheaders()
                                   if "ratelimit" in k.lower() or k.lower() == "retry-after"}}
            if resp.status >= 400:
                entry["error_body"] = data[:500].decode("utf-8", "replace")
        except Exception as exc:
            entry = {"i": i, "t_s": round(t0 - start, 3), "status": None, "error": repr(exc)}
        finally:
            conn.close()
        codes[entry["status"]] = codes.get(entry["status"], 0) + 1
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        f.flush()
        print(f'{i:3d}  t={entry["t_s"]:6.2f}s  status={entry["status"]}', flush=True)

first_429 = None
with open(out, encoding="utf-8") as f:
    for line in f:
        e = json.loads(line)
        if e.get("status") == 429:
            first_429 = e
            break
print(f"\nResumen: {codes} en {time.monotonic() - start:.1f} s")
print(f"Primer 429: petición {first_429['i']} a los {first_429['t_s']} s" if first_429 else "Sin 429")
