import bpy
import json
import sys
import os

addon_path = os.path.join(os.path.dirname(__file__), "..", "addon")
sys.path.insert(0, addon_path)

from addon.collector import collect_scene

def test_collect_empty_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    raw = collect_scene(target="all", simplified=True)
    assert "meta" in raw
    assert "actors" in raw
    assert len(raw["actors"]) == 0
    print("PASS: test_collect_empty_scene")

def test_collect_cube():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    bpy.ops.mesh.primitive_cube_add()
    raw = collect_scene(target="all", simplified=True)
    assert len(raw["actors"]) == 1
    actor = raw["actors"][0]
    assert actor["name"] == "Cube"
    assert actor["type"] == "MESH"
    assert actor["mesh"]["vertex_count"] == 8
    print("PASS: test_collect_cube")

def test_socket_server_ping():
    from addon.socket_server import start_server, stop_server
    ok = start_server()
    assert ok
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 9658))
    sock.sendall(json.dumps({"cmd": "ping"}).encode())
    data = sock.recv(4096).decode()
    response = json.loads(data)
    assert response["status"] == "ok"
    sock.close()
    stop_server()
    print("PASS: test_socket_server_ping")

if __name__ == "__main__":
    test_collect_empty_scene()
    test_collect_cube()
    test_socket_server_ping()
    print("\nAll Blender addon tests passed!")
