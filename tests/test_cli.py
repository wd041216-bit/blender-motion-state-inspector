import pytest
import subprocess
import sys
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
