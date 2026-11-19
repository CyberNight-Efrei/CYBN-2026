#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone
import json
import logging
from pathlib import Path

HOST = "0.0.0.0"
PORT = 8888

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


class Handler(BaseHTTPRequestHandler):

    def send_body(self, status, body, content_type="text/plain; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # GET /
    def do_GET(self):

        # Healthcheck
        if self.path == "/healthcheck":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
            return

        # Téléchargement du fichier présent à côté du serveur
        if self.path == "/":
            malware = Path(__file__).resolve().parent / "malware.ps1"

            if not malware.is_file():
                self.send_error(404, "malware.ps1 not found")
                return

            content = malware.read_bytes()

            logging.info(
                "FILE DOWNLOAD | filename=malware.ps1 | size=%d",
                len(content)
            )

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/octet-stream"
            )
            self.send_header(
                "Content-Disposition",
                'attachment; filename="malware.ps1"'
            )
            self.send_header(
                "Content-Length",
                str(len(content))
            )
            self.end_headers()
            self.wfile.write(content)
            return

        self.send_error(404, "Not found")

    # POST /heartbeat
    def do_POST(self):

        if self.path != "/heartbeat":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))

            if length <= 0 or length > 8192:
                self.send_error(413)
                return

            data = json.loads(self.rfile.read(length).decode("utf-8"))

            if not isinstance(data, dict):
                self.send_error(400)
                return

            event = {
                "received_utc": datetime.now(timezone.utc).isoformat(),
                "computer": str(data.get("computer", "unknown"))[:128],
                "user": str(data.get("user", "unknown"))[:128],
                "timestamp": str(data.get("timestamp", "unknown"))[:64],
                "type": str(data.get("type", "unknown"))[:64]
            }

            logging.info(
                "HEARTBEAT | Computer=%s | User=%s | Type=%s",
                event["computer"],
                event["user"],
                event["type"]
            )

            self.send_body(204, b"")

        except (ValueError, UnicodeDecodeError):
            self.send_error(400, "Invalid JSON")

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":

    server = ThreadingHTTPServer((HOST, PORT), Handler)

    print(f"HTTP server listening on http://{HOST}:{PORT}")
    print("GET  /            -> Download malware.ps1")
    print("GET  /healthcheck -> OK")
    print("POST /heartbeat   -> Receive heartbeat")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
    finally:
        server.server_close()
