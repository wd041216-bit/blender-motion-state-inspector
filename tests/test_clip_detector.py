from analyzer.clip_detector import build_temporal_clip_check


def _actor(name, bbox_min, bbox_max, visible=True):
    return {
        "name": name,
        "type": "MESH",
        "visible": visible,
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


def _frame(frame, actors):
    return {
        "meta": {
            "blender_version": "4.2.0",
            "scene_name": "clip-test",
            "current_frame": frame,
            "fps": 24,
            "frame_start": 1,
            "frame_end": 10,
            "render_engine": "CYCLES",
        },
        "actors": actors,
        "spatial": {
            "camera": {"name": "Cam", "location": [0, 0, 0], "rotation_euler": [0, 0, 0], "focal_length": 50},
            "actor_distances": [],
        },
    }


def test_temporal_clip_check_passes_without_overlap():
    raw = {
        "meta": {"kind": "animation_state", "frame_start": 1, "frame_end": 2, "frame_step": 1, "fps": 24, "frame_count": 2},
        "frames": [
            _frame(1, [_actor("Hero", [0, 0, 0], [1, 1, 2]), _actor("Prop", [2, 0, 0], [3, 1, 1])]),
            _frame(2, [_actor("Hero", [0, 0, 0], [1, 1, 2]), _actor("Prop", [2, 0, 0], [3, 1, 1])]),
        ],
    }
    result = build_temporal_clip_check(raw)
    assert result["verdict"] == "pass"
    assert result["events"] == []


def test_temporal_clip_check_reports_overlap_frame_and_spatial_info():
    raw = {
        "meta": {"kind": "animation_state", "frame_start": 1, "frame_end": 2, "frame_step": 1, "fps": 24, "frame_count": 2},
        "frames": [
            _frame(1, [_actor("Hero", [0, 0, 0], [1, 1, 2]), _actor("Prop", [2, 0, 0], [3, 1, 1])]),
            _frame(2, [_actor("Hero", [0, 0, 0], [1, 1, 2]), _actor("Prop", [0.75, 0.25, 0.2], [1.5, 1.25, 1.2])]),
        ],
    }
    result = build_temporal_clip_check(raw)
    assert result["verdict"] == "fail"
    assert result["events"][0]["frame"] == 2
    assert result["events"][0]["type"] == "bbox_overlap"
    assert result["events"][0]["overlap"]["penetration_depth"] > 0
    assert result["events"][0]["overlap"]["center"]


def test_temporal_clip_check_reports_ground_penetration():
    raw = _frame(4, [_actor("Floor", [-5, -5, -0.02], [5, 5, 0.0]), _actor("Hero", [0, 0, -0.15], [1, 1, 2])])
    result = build_temporal_clip_check(raw, tolerance=0.01)
    assert result["verdict"] == "fail"
    assert result["events"][0]["type"] == "ground_penetration"
    assert result["events"][0]["frame"] == 4
    assert result["events"][0]["penetration_depth"] == 0.15
