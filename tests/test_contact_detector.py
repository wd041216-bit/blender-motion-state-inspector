import pytest
from analyzer.contact_detector import detect_contacts

def test_ground_contact():
    bones = [{"name": "foot.L", "world_head": [0,0,0.01], "world_tail": [0,0,0]}]
    result = detect_contacts(bones, ground_y=0.0, threshold=0.05)
    assert any(c["type"] == "ground" for c in result)

def test_no_contact():
    bones = [{"name": "foot.L", "world_head": [0,0,0.1], "world_tail": [0,0,0.08]}]
    result = detect_contacts(bones, ground_y=0.0, threshold=0.05)
    assert not any(c["type"] == "ground" for c in result)
