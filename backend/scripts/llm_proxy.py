"""
Proxy local que traduz chamadas OpenAI SDK (httpx) para requests.
Resolve incompatibilidade httpx↔OmniRouter.
Roda em http://127.0.0.1:11435/v1
"""
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

UPSTREAM = os.environ.get("OMNIROUTE_URL", "http://localhost:20128/v1")
API_KEY = os.environ.get("OMNIROUTE_API_KEY", "")


class ProxyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        # Parse body and force stream=false
        try:
            data = json.loads(body)
            data["stream"] = False
        except (json.JSONDecodeError, UnicodeDecodeError):
            data = None

        # Forward to upstream
        upstream_url = UPSTREAM + self.path.replace("/v1", "", 1) if self.path.startswith("/v1") else UPSTREAM + self.path
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "Connection": "close",
        }

        try:
            resp = requests.post(
                upstream_url,
                json=data if data else None,
                data=body if data is None else None,
                headers=headers,
                timeout=300,
            )
            self.send_response(resp.status_code)
            for k, v in resp.headers.items():
                if k.lower() not in ("transfer-encoding", "connection", "content-encoding"):
                    self.send_header(k, v)
            content = resp.content
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            error = json.dumps({"error": {"message": str(e), "type": "proxy_error"}}).encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(error)))
            self.end_headers()
            self.wfile.write(error)

    def do_GET(self):
        upstream_url = UPSTREAM + self.path.replace("/v1", "", 1) if self.path.startswith("/v1") else UPSTREAM + self.path
        headers = {"Authorization": f"Bearer {API_KEY}", "Connection": "close"}
        try:
            resp = requests.get(upstream_url, headers=headers, timeout=30)
            self.send_response(resp.status_code)
            content = resp.content
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            error = json.dumps({"error": str(e)}).encode()
            self.send_response(502)
            self.send_header("Content-Length", str(len(error)))
            self.end_headers()
            self.wfile.write(error)

    def log_message(self, format, *args):
        pass  # Silenciar logs


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 11435
    server = HTTPServer(("127.0.0.1", port), ProxyHandler)
    print(f"LLM Proxy rodando em http://127.0.0.1:{port}/v1 -> {UPSTREAM}")
    sys.stdout.flush()
    server.serve_forever()
