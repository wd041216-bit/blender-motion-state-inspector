import json
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path


HOST = "127.0.0.1"
PORT = 9658

_server_process = None
_request_dir = None
_timer_registered = False


def _service_requests():
    global _timer_registered
    if _server_process is None or _request_dir is None:
        _timer_registered = False
        return None

    request_path = Path(_request_dir)
    for item in sorted(request_path.glob("request_*.json")):
        try:
            request = json.loads(item.read_text(encoding="utf-8"))
            response = _handle_inspect_request(request)
            response_file = request_path / f"response_{request.get('id')}.json"
            tmp_file = response_file.with_suffix(".tmp")
            tmp_file.write_text(json.dumps(response, ensure_ascii=False), encoding="utf-8")
            tmp_file.replace(response_file)
            item.unlink(missing_ok=True)
        except Exception as exc:
            error_file = item.with_name(item.name.replace("request_", "response_", 1))
            error_file.write_text(json.dumps({"status": "error", "message": str(exc)}), encoding="utf-8")
            item.unlink(missing_ok=True)

    if _server_process.poll() is None:
        return 0.05

    _timer_registered = False
    return None


def _handle_inspect_request(request):
    try:
        from .collector import collect_scene, write_raw_state

        raw = collect_scene(
            target=request.get("target", "all"),
            simplified=bool(request.get("simplified", False)),
        )
        path = write_raw_state(raw)
        return {"status": "ok", "path": path}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def _register_timer():
    global _timer_registered
    if _timer_registered:
        return
    import bpy

    bpy.app.timers.register(_service_requests, first_interval=0.05, persistent=True)
    _timer_registered = True


def _wait_for_port(host, port, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.1):
                return True
        except OSError:
            time.sleep(0.05)
    return False


def start_server(host=HOST, port=PORT):
    global _server_process, _request_dir
    if _server_process is not None and _server_process.poll() is None:
        return False

    import bpy

    _request_dir = tempfile.mkdtemp(prefix="bmsi_socket_")
    child_script = Path(__file__).with_name("socket_server_process.py")
    blender_version = ".".join(str(value) for value in bpy.app.version)
    _server_process = subprocess.Popen(
        [
            sys.executable,
            str(child_script),
            "--host",
            host,
            "--port",
            str(port),
            "--request-dir",
            _request_dir,
            "--blender-version",
            blender_version,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _register_timer()
    if not _wait_for_port(host, port):
        stop_server()
        return False
    return True


def stop_server():
    global _server_process, _request_dir
    if _server_process is None:
        return False

    try:
        with socket.create_connection((HOST, PORT), timeout=0.5) as sock:
            sock.sendall(json.dumps({"cmd": "shutdown"}).encode("utf-8"))
            sock.recv(4096)
    except OSError:
        pass

    try:
        _server_process.wait(timeout=1.0)
    except subprocess.TimeoutExpired:
        pass
    if _server_process.poll() is None:
        _server_process.terminate()
        try:
            _server_process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            _server_process.kill()
            _server_process.wait(timeout=1.0)

    _server_process = None
    if _request_dir:
        shutil.rmtree(_request_dir, ignore_errors=True)
    _request_dir = None
    return True


def is_running():
    return _server_process is not None and _server_process.poll() is None
