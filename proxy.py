#!/usr/bin/env python3
"""
proxy.py — Proxy inverso para el Asistente de Metadatos CKAN
=============================================================
Resuelve el problema de CORS al actuar como intermediario entre
el browser y la API de CKAN (test.catalogodatos.gub.uy).

Uso:
    python proxy.py                  # Puerto por defecto: 8080
    python proxy.py --port 3000      # Puerto personalizado
    python proxy.py --host 0.0.0.0   # Escuchar en todas las interfaces

Dependencias (solo stdlib + requests):
    pip install requests
"""

import argparse
import json
import logging
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, urlencode, parse_qs

try:
    import requests
except ImportError:
    print("❌  Falta la dependencia 'requests'. Instalala con:\n    pip install requests")
    sys.exit(1)

# ── Configuración ──────────────────────────────────────────────────────────────
CKAN_BASE    = "https://test.catalogodatos.gub.uy"
HTML_FILE    = Path(__file__).parent / "index.html"
DEFAULT_PORT = 8080
DEFAULT_HOST = "127.0.0.1"

CORS_HEADERS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, X-CKAN-API-Key, Authorization",
    "Access-Control-Max-Age":       "86400",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("proxy")

# ── Handler ────────────────────────────────────────────────────────────────────
class ProxyHandler(BaseHTTPRequestHandler):

    # ── Silenciar log por defecto del BaseHTTPRequestHandler ──────────────────
    def log_message(self, fmt, *args):
        pass  # Usamos nuestro propio logger

    # ── Cabeceras CORS en toda respuesta ──────────────────────────────────────
    def _send_cors(self):
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)

    # ── Preflight OPTIONS ─────────────────────────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors()
        self.end_headers()
        log.info("OPTIONS  %s  → 204 preflight OK", self.path)

    # ── GET ───────────────────────────────────────────────────────────────────
    def do_GET(self):
        parsed = urlparse(self.path)

        # Servir la aplicación HTML
        if parsed.path in ("/", "/index.html"):
            self._serve_html()
            return

        # Proxy de la API CKAN
        if parsed.path.startswith("/api/"):
            self._proxy_request("GET", parsed)
            return

        # Proxy de recursos estáticos del catálogo (CSS, imágenes, etc.)
        if parsed.path.startswith("/images/") or parsed.path.startswith("/css/") \
                or parsed.path.startswith("/webassets/"):
            self._proxy_static(parsed)
            return

        self._send_404()

    # ── POST ──────────────────────────────────────────────────────────────────
    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self._proxy_request("POST", parsed)
            return
        self._send_404()

    # ── Servir HTML local ─────────────────────────────────────────────────────
    def _serve_html(self):
        if not HTML_FILE.exists():
            log.error("No se encontró %s", HTML_FILE)
            self.send_response(404)
            self._send_cors()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"index.html no encontrado. Verifica que este en el mismo directorio que proxy.py")
            return

        content = HTML_FILE.read_bytes()
        self.send_response(200)
        self._send_cors()
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)
        log.info("GET      /  → 200 (index.html, %d bytes)", len(content))

    # ── Proxy API ─────────────────────────────────────────────────────────────
    def _proxy_request(self, method, parsed):
        target_url = f"{CKAN_BASE}{parsed.path}"
        if parsed.query:
            target_url += f"?{parsed.query}"

        # Reenviar headers relevantes (incluyendo X-CKAN-API-Key)
        forward_headers = {}
        for h in ("X-CKAN-API-Key", "Authorization", "Content-Type"):
            val = self.headers.get(h)
            if val:
                forward_headers[h] = val

        # Leer body si es POST
        body = None
        if method == "POST":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else None

        log.info("→ %s  %s", method, target_url)

        try:
            resp = requests.request(
                method,
                target_url,
                headers=forward_headers,
                data=body,
                timeout=30,
                verify=True,
            )

            # Leer respuesta
            resp_body = resp.content

            log.info("← %s  %d  (%d bytes)", target_url.split("/")[-1].split("?")[0],
                     resp.status_code, len(resp_body))

            # Enviar respuesta al browser con CORS
            self.send_response(resp.status_code)
            self._send_cors()

            # Content-Type de la respuesta original
            ct = resp.headers.get("Content-Type", "application/json")
            self.send_header("Content-Type", ct)
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)

        except requests.exceptions.SSLError as e:
            self._send_error(502, f"Error SSL al conectar con CKAN: {e}")
        except requests.exceptions.ConnectionError as e:
            self._send_error(502, f"No se pudo conectar con {CKAN_BASE}: {e}")
        except requests.exceptions.Timeout:
            self._send_error(504, f"Timeout al conectar con {CKAN_BASE}")
        except Exception as e:
            self._send_error(500, f"Error inesperado en el proxy: {e}")

    # ── Proxy recursos estáticos (CSS, imágenes) ──────────────────────────────
    def _proxy_static(self, parsed):
        target_url = f"{CKAN_BASE}{parsed.path}"
        try:
            resp = requests.get(target_url, timeout=15, verify=True)
            ct   = resp.headers.get("Content-Type", "application/octet-stream")
            self.send_response(resp.status_code)
            self._send_cors()
            self.send_header("Content-Type", ct)
            self.send_header("Content-Length", str(len(resp.content)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(resp.content)
            log.info("STATIC   %s  → %d", parsed.path, resp.status_code)
        except Exception as e:
            log.warning("No se pudo obtener recurso estático %s: %s", parsed.path, e)
            self._send_404()

    # ── Respuestas de error ────────────────────────────────────────────────────
    def _send_404(self):
        body = json.dumps({"error": "Not found"}).encode()
        self.send_response(404)
        self._send_cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, code, message):
        log.error("Error %d: %s", code, message)
        body = json.dumps({"error": message}).encode()
        self.send_response(code)
        self._send_cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Proxy inverso para el Asistente de Metadatos CKAN"
    )
    parser.add_argument("--host",  default=DEFAULT_HOST, help=f"Host (default: {DEFAULT_HOST})")
    parser.add_argument("--port",  default=DEFAULT_PORT, type=int, help=f"Puerto (default: {DEFAULT_PORT})")
    parser.add_argument("--ckan",  default=CKAN_BASE, help=f"URL base del catálogo CKAN (default: {CKAN_BASE})")
    args = parser.parse_args()

    # Permitir cambiar el target CKAN desde la línea de comandos
    global CKAN_BASE
    CKAN_BASE = args.ckan.rstrip("/")

    if not HTML_FILE.exists():
        log.warning("⚠  No se encontró index.html en %s", HTML_FILE.parent)
        log.warning("   Asegurate de que index.html esté en el mismo directorio que proxy.py")

    server = HTTPServer((args.host, args.port), ProxyHandler)

    print()
    print("=" * 60)
    print("  🚀  Proxy CKAN iniciado")
    print("=" * 60)
    print(f"  Aplicación:  http://{args.host}:{args.port}/")
    print(f"  API proxy:   http://{args.host}:{args.port}/api/3/action/...")
    print(f"  CKAN target: {CKAN_BASE}")
    print()
    print("  En el campo 'ID del dataset' de la app usá el")
    print("  UUID o nombre-slug del conjunto de datos.")
    print()
    print("  Ctrl+C para detener el servidor.")
    print("=" * 60)
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n  ⏹  Servidor detenido.")
        server.server_close()


if __name__ == "__main__":
    main()
