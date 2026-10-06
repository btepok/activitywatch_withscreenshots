from __future__ import annotations

import logging
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .archive import usage, write_zip

logger = logging.getLogger(__name__)

LOCAL_PORT = 5617


class _Handler(BaseHTTPRequestHandler):
    directory: Path

    def do_GET(self):  # noqa: N802
        path = urlsplit(self.path).path
        if path in ("/info", "/info/"):
            self._send_info()
            return
        if path in ("/screenshots.zip", "/screenshots.zip/"):
            self._send_zip()
            return
        self.send_error(404)

    def _send_info(self) -> None:
        import json

        body = json.dumps(usage(self.directory)).encode("utf-8")
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_zip(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            write_zip(self.directory, tmp_path)
            size = tmp_path.stat().st_size
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", 'attachment; filename="screenshots.zip"')
            self.send_header("Content-Length", str(size))
            self.end_headers()
            with tmp_path.open("rb") as src:
                while True:
                    chunk = src.read(256 * 1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        finally:
            tmp_path.unlink(missing_ok=True)

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")

    def log_message(self, fmt: str, *args) -> None:
        logger.info("screenshot http: " + fmt, *args)


def serve_screenshot_http(directory: Path, port: int = LOCAL_PORT) -> None:
    handler = type("ScreenshotHandler", (_Handler,), {"directory": directory})
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError:
        logger.exception("screenshot download server failed on port %s", port)
        return
    logger.info("screenshot download server on http://127.0.0.1:%s", port)
    server.serve_forever()
