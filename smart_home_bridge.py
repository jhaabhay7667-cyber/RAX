
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from queue import Queue, Empty
import json

ALLOWED_ORIGIN = "https://venerable-tapioca-7a11ed.netlify.app"

commands = Queue()
_server = None


class BridgeHandler(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/next":
            try:
                command = commands.get_nowait()
            except Empty:
                command = None

            self.send_json({"command": command})
        else:
            self.send_json({"error": "Not found"}, 404)

    def log_message(self, format, *args):
        pass


def start_smart_home_bridge():
    global _server

    if _server is not None:
        return

    _server = ThreadingHTTPServer(
        ("127.0.0.1", 8765),
        BridgeHandler
    )

    Thread(target=_server.serve_forever, daemon=True).start()
    print("RAX Smart Home Bridge running on port 8765")


def queue_device_command(device, action):
    if device not in {"light", "fan", "gate"}:
        return False

    if action not in {"on", "off"}:
        return False

    commands.put({
        "device": device,
        "action": action
    })

    return True
