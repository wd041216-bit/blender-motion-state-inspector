import json
import socketserver
import threading
import bpy
from addon.collector import collect_scene, write_raw_state

HOST = "127.0.0.1"
PORT = 9658

_server_instance = None
_server_thread = None


class InspectHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            data = self.request.recv(65536).decode("utf-8")
            if not data:
                return
            msg = json.loads(data)
            cmd = msg.get("cmd")
            if cmd == "ping":
                response = {"status": "ok", "blender_version": ".".join(str(x) for x in bpy.app.version)}
            elif cmd == "inspect":
                target = msg.get("target", "all")
                simplified = msg.get("simplified", False)
                raw = {"status": "pending"}
                def _collect():
                    nonlocal raw
                    raw = collect_scene(target=target, simplified=simplified)
                    return None
                bpy.app.timers.register(_collect, first_interval=0.01)
                import time
                time.sleep(0.5)
                path = write_raw_state(raw)
                response = {"status": "ok", "path": path, "elapsed_ms": 500}
            else:
                response = {"status": "error", "message": f"Unknown command: {cmd}"}
        except Exception as e:
            response = {"status": "error", "message": str(e)}
        self.request.sendall(json.dumps(response, ensure_ascii=False).encode("utf-8"))


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_server(host=HOST, port=PORT):
    global _server_instance, _server_thread
    if _server_instance is not None:
        return False
    _server_instance = ThreadedTCPServer((host, port), InspectHandler)
    _server_thread = threading.Thread(target=_server_instance.serve_forever, daemon=True)
    _server_thread.start()
    return True


def stop_server():
    global _server_instance, _server_thread
    if _server_instance is not None:
        _server_instance.shutdown()
        _server_instance.server_close()
        _server_instance = None
        _server_thread = None
        return True
    return False


def is_running():
    return _server_instance is not None
