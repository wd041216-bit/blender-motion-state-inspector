from analyzer.actor_classifier import classify_actor
from analyzer.loader import load_raw_state


def test_classify_character_from_rigged_skinned_mesh():
    scene = load_raw_state({
        "meta": {"blender_version": "4.2.0", "scene_name": "t", "current_frame": 1, "fps": 24, "frame_start": 1, "frame_end": 1, "render_engine": "CYCLES"},
        "actors": [{
            "name": "mixamo_Alex",
            "type": "MESH",
            "visible": True,
            "world_matrix": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],
            "mesh": {"vertex_count": 100, "face_count": 80, "edge_count": 180, "bbox_min": [0,0,0], "bbox_max": [1,1,2], "materials": [], "has_armature_modifier": True, "armature_name": "Arm", "vertex_groups_count": 20},
            "armature": {"bone_count": 65, "bones": []},
            "pose": {"pose_bones": []},
        }],
        "spatial": {"camera": {"name": "Cam", "location": [0,0,0], "rotation_euler": [0,0,0], "focal_length": 50}, "actor_distances": []},
    })
    assert classify_actor(scene.actors[0])["class"] == "character"


def test_classify_named_floor_as_scene_prop():
    scene = load_raw_state({
        "meta": {"blender_version": "4.2.0", "scene_name": "t", "current_frame": 1, "fps": 24, "frame_start": 1, "frame_end": 1, "render_engine": "CYCLES"},
        "actors": [{
            "name": "fast_ha_vln_floor",
            "type": "MESH",
            "visible": True,
            "world_matrix": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],
            "mesh": {"vertex_count": 8, "face_count": 6, "edge_count": 12, "bbox_min": [0,0,0], "bbox_max": [1,1,0.1], "materials": [], "has_armature_modifier": False, "armature_name": None, "vertex_groups_count": 0},
            "armature": {"bone_count": 0, "bones": []},
            "pose": {"pose_bones": []},
        }],
        "spatial": {"camera": {"name": "Cam", "location": [0,0,0], "rotation_euler": [0,0,0], "focal_length": 50}, "actor_distances": []},
    })
    assert classify_actor(scene.actors[0])["class"] == "scene_prop"
