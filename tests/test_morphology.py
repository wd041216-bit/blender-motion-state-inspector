import pytest
from analyzer.loader import load_raw_state
from analyzer.morphology import calculate_morphology

SAMPLE = {
    "meta": {"blender_version": "4.2.0", "scene_name": "test", "current_frame": 1, "fps": 24, "frame_start": 1, "frame_end": 250, "render_engine": "CYCLES"},
    "actors": [{
        "name": "Char", "type": "MESH", "visible": True,
        "world_matrix": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],
        "mesh": {"vertex_count": 100, "face_count": 80, "edge_count": 180, "bbox_min": [-0.5, -0.2, 0.0], "bbox_max": [0.5, 0.2, 1.8], "materials": [], "has_armature_modifier": True, "armature_name": "Arm", "vertex_groups_count": 10},
        "armature": {"bone_count": 0, "bones": []},
        "pose": {"pose_bones": []}
    }],
    "spatial": {"camera": {"name": "Cam", "location": [0,0,0], "rotation_euler": [0,0,0], "focal_length": 50}, "actor_distances": []}
}

def test_morphology_from_bbox():
    scene = load_raw_state(SAMPLE)
    morph = calculate_morphology(scene.actors[0])
    assert morph["height"] == pytest.approx(1.8, abs=0.01)
    assert morph["shoulder_width"] == pytest.approx(1.0, abs=0.01)
    # dx=1.0, dy=0.4, dz=1.8 => volume = 0.72
    assert morph["bbox_volume"] == pytest.approx(0.72, abs=0.01)
