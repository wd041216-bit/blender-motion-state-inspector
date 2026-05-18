import json
import pytest
from analyzer.loader import load_raw_state, Actor, SceneMeta

SAMPLE_RAW = {
    "meta": {
        "blender_version": "4.2.0",
        "scene_name": "untitled",
        "current_frame": 1,
        "fps": 24,
        "frame_start": 1,
        "frame_end": 250,
        "render_engine": "CYCLES"
    },
    "actors": [
        {
            "name": "Character_A",
            "type": "MESH",
            "visible": True,
            "world_matrix": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],
            "mesh": {
                "vertex_count": 100,
                "face_count": 80,
                "edge_count": 180,
                "bbox_min": [-0.5, -0.2, 0.0],
                "bbox_max": [0.5, 0.2, 1.8],
                "materials": ["Skin"],
                "has_armature_modifier": True,
                "armature_name": "Armature_A",
                "vertex_groups_count": 10
            },
            "armature": {
                "bone_count": 3,
                "bones": [
                    {"name": "root", "parent": None, "head": [0,0,0], "tail": [0,0,0.1], "world_head": [0,0,0], "world_tail": [0,0,0.1], "length": 0.1, "is_deform": True}
                ]
            },
            "pose": {"pose_bones": []}
        }
    ],
    "spatial": {
        "camera": {"name": "Camera", "location": [5,-5,3], "rotation_euler": [1.1,0,0.785], "focal_length": 50},
        "actor_distances": []
    }
}

def test_load_raw_state_from_dict():
    scene = load_raw_state(SAMPLE_RAW)
    assert isinstance(scene.meta, SceneMeta)
    assert scene.meta.blender_version == "4.2.0"
    assert len(scene.actors) == 1
    assert isinstance(scene.actors[0], Actor)
    assert scene.actors[0].name == "Character_A"
    assert scene.actors[0].mesh.bbox_min == [-0.5, -0.2, 0.0]

def test_load_raw_state_from_json(tmp_path):
    path = tmp_path / "raw.json"
    path.write_text(json.dumps(SAMPLE_RAW), encoding="utf-8")
    scene = load_raw_state(str(path))
    assert scene.meta.scene_name == "untitled"

def test_load_legacy_actor_distance_schema():
    raw = json.loads(json.dumps(SAMPLE_RAW))
    raw["spatial"]["actor_distances"] = [{"from": "A", "to": "B", "distance": 1.25}]
    scene = load_raw_state(raw)
    assert scene.spatial.actor_distances[0].from_actor == "A"
    assert scene.spatial.actor_distances[0].to_actor == "B"
