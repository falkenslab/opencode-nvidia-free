"""Proxy de registro entre OpenCode y la API de NVIDIA Build.

Reenvía cada petición a UPSTREAM (sin tocarla, salvo los parámetros de STRIP_PARAMS),
devuelve la respuesta en streaming y añade una línea JSON por petición a PROXY_LOG:
hora, modelo, código HTTP, duración, parámetros del cuerpo, cabeceras de rate limit y,
si hay error, el principio del cuerpo de la respuesta.

Nunca registra la cabecera Authorization ni el contenido de los mensajes.

Variables de entorno:
  UPSTREAM      URL base del servicio real (por defecto https://integrate.api.nvidia.com)
  STRIP_PARAMS  parámetros del cuerpo JSON a eliminar, separados por comas (p. ej. prompt_cache_key)
  PROXY_LOG     fichero JSONL de registro (por defecto /results/proxy.jsonl)
  PROXY_TAG     etiqueta que se añade a cada línea (fase del experimento)
"""
import http.client
import json
import os
import ssl
import threading
import time
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM = urllib.parse.urlsplit(os.environ.get("UPSTREAM", "https://integrate.api.nvidia.com"))
STRIP = [p.strip() for p in os.environ.get("STRIP_PARAMS", "").split(",") if p.strip()]
LOG_PATH = os.environ.get("PROXY_LOG", "/results/proxy.jsonl")
TAG = os.environ.get("PROXY_TAG", "")
HOP_BY_HOP = {"connection", "keep-alive", "transfer-encoding", "te", "trailer", "upgrade",
              "proxy-authorization", "proxy-authenticate", "host", "content-length", "accept-encoding"}
_lock = threading.Lock()


def log(entry: dict) -> None:
    line = json.dumps(entry, ensure_ascii=False)
    with _lock, open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # silencia el log por defecto de http.server
        pass

    def _proxy(self):
        started = time.monotonic()
        entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"), "tag": TAG,
                 "method": self.command, "path": self.path}
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))

        if body and "json" in (self.headers.get("Content-Type") or ""):
            try:
                payload = json.loads(body)
                entry["model"] = payload.get("model")
                entry["stream"] = payload.get("stream")
                entry["params"] = sorted(k for k in payload if k != "messages")
                entry["n_messages"] = len(payload.get("messages") or [])
                entry["n_tools"] = len(payload.get("tools") or [])
                stripped = [p for p in STRIP if p in payload]
                for p in stripped:
                    payload.pop(p)
                if stripped:
                    entry["stripped"] = stripped
                    body = json.dumps(payload).encode()
            except ValueError:
                entry["body_parse_error"] = True

        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP_BY_HOP}
        headers["Host"] = UPSTREAM.netloc
        headers["Accept-Encoding"] = "identity"
        headers["Content-Length"] = str(len(body))

        conn_cls = http.client.HTTPSConnection if UPSTREAM.scheme == "https" else http.client.HTTPConnection
        kwargs = {"context": ssl.create_default_context()} if UPSTREAM.scheme == "https" else {}
        conn = conn_cls(UPSTREAM.hostname, UPSTREAM.port, timeout=600, **kwargs)
        try:
            conn.request(self.command, self.path, body=body or None, headers=headers)
            resp = conn.getresponse()
        except Exception as exc:  # error de red contra el upstream
            entry.update(status=502, error=repr(exc), duration_s=round(time.monotonic() - started, 3))
            log(entry)
            self.send_error(502, "upstream error")
            return

        entry["status"] = resp.status
        entry["ratelimit"] = {k.lower(): v for k, v in resp.getheaders()
                              if "ratelimit" in k.lower() or k.lower() == "retry-after"}
        self.send_response(resp.status)
        for k, v in resp.getheaders():
            if k.lower() not in HOP_BY_HOP:
                self.send_header(k, v)
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

        sent = 0
        head = b""
        try:
            while True:
                chunk = resp.read1(65536)
                if not chunk:
                    break
                if resp.status >= 400 and len(head) < 2000:
                    head += chunk
                sent += len(chunk)
                self.wfile.write(b"%x\r\n%s\r\n" % (len(chunk), chunk))
                self.wfile.flush()
            self.wfile.write(b"0\r\n\r\n")
        except (BrokenPipeError, ConnectionResetError):
            entry["client_disconnected"] = True
        finally:
            conn.close()

        entry["bytes"] = sent
        entry["duration_s"] = round(time.monotonic() - started, 3)
        if resp.status >= 400:
            entry["error_body"] = head[:1000].decode("utf-8", "replace")
        log(entry)

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = _proxy


if __name__ == "__main__":
    print(f"proxy → {UPSTREAM.geturl()} | strip={STRIP or '-'} | log={LOG_PATH} | tag={TAG or '-'}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
