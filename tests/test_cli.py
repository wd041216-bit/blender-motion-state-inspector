import pytest
import subprocess
import sys
import json
from pathlib import Path

def test_cli_help():
    result = subprocess.run([sys.executable, "-m", "analyzer.cli", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "blender-state-inspector" in result.stdout or "usage" in result.stdout.lower()

def test_cli_main(tmp_path):
    raw = tmp_path / "raw.json"
    raw.write_text('{"meta":{"blender_version":"4.2.0","scene_name":"t","current_frame":1,"fps":24,"frame_start":1,"frame_end":250,"render_engine":"CYCLES"},"actors":[],"spatial":{"camera":{"name":"Cam","location":[0,0,0],"rotation_euler":[0,0,0],"focal_length":50},"actor_distances":[]}}')
    out_md = tmp_path / "report.md"
    out_json = tmp_path / "report.json"
    result = subprocess.run([sys.executable, "-m", "analyzer.cli", str(raw), "--output-md", str(out_md), "--output-json", str(out_json)], capture_output=True, text=True)
    assert result.returncode == 0
    assert out_md.exists()
    assert out_json.exists()

def test_cli_timeline_jsonl(tmp_path):
    frame = {"meta":{"blender_version":"4.2.0","scene_name":"t","current_frame":1,"fps":24,"frame_start":1,"frame_end":2,"render_engine":"CYCLES"},"actors":[],"spatial":{"camera":{"name":"Cam","location":[0,0,0],"rotation_euler":[0,0,0],"focal_length":50},"actor_distances":[]}}
    raw = tmp_path / "timeline.json"
    raw.write_text('{"meta":{"kind":"animation_state","frame_start":1,"frame_end":2,"frame_step":1,"fps":24,"frame_count":2},"frames":[' + __import__("json").dumps(frame) + ',' + __import__("json").dumps({**frame, "meta": {**frame["meta"], "current_frame": 2}}) + ']}')
    out_md = tmp_path / "timeline.md"
    out_json = tmp_path / "timeline_report.json"
    out_jsonl = tmp_path / "timeline.jsonl"
    result = subprocess.run([sys.executable, "-m", "analyzer.cli", str(raw), "--output-md", str(out_md), "--output-json", str(out_json), "--output-jsonl", str(out_jsonl)], capture_output=True, text=True)
    assert result.returncode == 0
    assert out_json.exists()
    assert out_jsonl.exists()

def test_cli_timeline_clip_check(tmp_path):
    def actor(name, bbox_min, bbox_max):
        return {
            "name": name,
            "type": "MESH",
            "visible": True,
            "world_matrix": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            "mesh": {
                "vertex_count": 8,
                "face_count": 6,
                "edge_count": 12,
                "bbox_min": bbox_min,
                "bbox_max": bbox_max,
                "bbox_world_min": bbox_min,
                "bbox_world_max": bbox_max,
                "dimensions": [bbox_max[i] - bbox_min[i] for i in range(3)],
                "materials": [],
                "has_armature_modifier": False,
                "armature_name": None,
                "vertex_groups_count": 0,
            },
            "armature": {"bone_count": 0, "bones": []},
            "pose": {"pose_bones": []},
        }

    def frame(number, actors):
        return {
            "meta": {"blender_version":"4.2.0","scene_name":"t","current_frame":number,"fps":24,"frame_start":1,"frame_end":2,"render_engine":"CYCLES"},
            "actors": actors,
            "spatial": {"camera":{"name":"Cam","location":[0,0,0],"rotation_euler":[0,0,0],"focal_length":50},"actor_distances":[]},
        }

    raw = tmp_path / "timeline.json"
    raw.write_text(json.dumps({
        "meta": {"kind": "animation_state", "frame_start": 1, "frame_end": 2, "frame_step": 1, "fps": 24, "frame_count": 2},
        "frames": [
            frame(1, [actor("Hero", [0, 0, 0], [1, 1, 2]), actor("Prop", [3, 0, 0], [4, 1, 1])]),
            frame(2, [actor("Hero", [0, 0, 0], [1, 1, 2]), actor("Prop", [0.5, 0.2, 0.2], [1.5, 1.2, 1.2])]),
        ],
    }))
    out_md = tmp_path / "timeline.md"
    out_json = tmp_path / "timeline_report.json"
    result = subprocess.run([
        sys.executable,
        "-m",
        "analyzer.cli",
        str(raw),
        "--clip-check",
        "--output-md",
        str(out_md),
        "--output-json",
        str(out_json),
    ], capture_output=True, text=True)
    assert result.returncode == 0
    report = json.loads(out_json.read_text())
    assert report["clip_check"]["verdict"] == "fail"
    assert report["clip_check"]["events"][0]["frame"] == 2
    assert "时间段穿模检查" in out_md.read_text()
