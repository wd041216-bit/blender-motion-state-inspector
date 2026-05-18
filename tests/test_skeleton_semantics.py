import pytest
from analyzer.skeleton_semantics import map_skeleton_semantics

BONES = [
    {"name": "root", "parent": None},
    {"name": "spine", "parent": "root"},
    {"name": "chest", "parent": "spine"},
    {"name": "neck", "parent": "chest"},
    {"name": "head", "parent": "neck"},
    {"name": "arm.L", "parent": "chest"},
    {"name": "forearm.L", "parent": "arm.L"},
    {"name": "hand.L", "parent": "forearm.L"},
    {"name": "thigh.L", "parent": "root"},
    {"name": "shin.L", "parent": "thigh.L"},
    {"name": "foot.L", "parent": "shin.L"},
]

def test_map_skeleton():
    mapping = map_skeleton_semantics([b["name"] for b in BONES])
    assert mapping["root"] == "root"
    assert mapping["spine"] == "spine"
    assert mapping["head"] == "head"
    assert mapping["left_arm"] == "arm.L"
    assert mapping["left_forearm"] == "forearm.L"
    assert mapping["left_hand"] == "hand.L"
    assert mapping["left_thigh"] == "thigh.L"
    assert mapping["left_shin"] == "shin.L"
    assert mapping["left_foot"] == "foot.L"
    assert mapping.get("right_arm") is None
