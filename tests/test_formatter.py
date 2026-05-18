import pytest
import json
from analyzer.formatter import format_markdown, format_json

SAMPLE_REPORT = {
    "summary": "Char 站立，无异常",
    "actors": [{
        "name": "Char",
        "morphology": {"height": 1.75},
        "pose_state": "站立",
        "anomalies": [],
    }],
    "spatial": {"ground_contact": []},
}

def test_format_json():
    out = format_json(SAMPLE_REPORT)
    parsed = json.loads(out)
    assert parsed["actors"][0]["name"] == "Char"

def test_format_markdown():
    out = format_markdown(SAMPLE_REPORT)
    assert "Char" in out
    assert "站立" in out
