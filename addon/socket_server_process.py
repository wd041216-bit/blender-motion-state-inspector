import argparse
import json
import socketserver
import time
import uuid
from pathlib import Path


class InspectHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            data = self.request.recv(65536).decode("utf-8")
            if not data:
                return
            message = json.loads(data)
            command = message.get("cmd")
            if command == "ping":
                response = {"status": "ok", "blender_version": self.server.blender_version}
            elif command == "shutdown":
                self.server.shutdown_requested = True
                response = {"status": "ok"}
            elif command == "inspect":
                response = self._inspect(message)
            else:
                response = {"status": "error", "message": f"Unknown command: {command}"}
        except Exception as exc:
            response = {"status": "error", "message": str(exc)}
        self.request.sendall(json.dumps(response, ensure_ascii=False).encode("utf-8"))

    def _inspect(self, message):
        request_id = uuid.uuid4().hex
        request = {
            "id": request_id,
            "target": message.get("target", "all"),
            "simplified": bool(message.get("simplified", False)),
        }
        request_file = self.server.request_dir / f"request_{request_id}.json"
        response_file = self.server.request_dir / f"response_{request_id}.json"
        tmp_file = request_file.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
        tmp_file.replace(request_file)

        start = time.monotonic()
        while time.monotonic() - start < 30:
            if response_file.exists():
                response = json.loads(response_file.read_text(encoding="utf-8"))
                response_file.unlink(missing_ok=True)
                response.setdefault("elapsed_ms", int((time.monotonic() - start) * 1000))
                return response
            time.sleep(0.05)
        return {"status": "error", "message": "Inspection timed out"}


class InspectTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9658)
    parser.add_argument("--request-dir", required=True)
    parser.add_argument("--blender-version", default="")
    return parser.parse_args()


def main():
    args = parse_args()
    server = InspectTCPServer((args.host, args.port), InspectHandler)
    server.request_dir = Path(args.request_dir)
    server.blender_version = args.blender_version
    server.shutdown_requested = False
    server.timeout = 0.25
    try:
        while not server.shutdown_requested:
            server.handle_request()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
