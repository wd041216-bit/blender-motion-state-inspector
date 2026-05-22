import pytest
from analyzer.spatial import calculate_spatial_summary, evaluate_translation_locks
from analyzer.loader import SceneState, SceneMeta, Actor, MeshData, ArmatureData, PoseData, SpatialData, CameraData

ACTOR_A = Actor(name="A", type="MESH", visible=True, world_matrix=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],
    mesh=MeshData(vertex_count=0, face_count=0, edge_count=0, bbox_min=[0,0,0], bbox_max=[1,1,1], materials=[], has_armature_modifier=False, armature_name=None, vertex_groups_count=0),
    armature=ArmatureData(bone_count=0, bones=[]), pose=PoseData(pose_bones=[]))

ACTOR_B = Actor(name="B", type="MESH", visible=True, world_matrix=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[2,0,0,1]],
    mesh=MeshData(vertex_count=0, face_count=0, edge_count=0, bbox_min=[2,0,0], bbox_max=[3,1,1], materials=[], has_armature_modifier=False, armature_name=None, vertex_groups_count=0),
    armature=ArmatureData(bone_count=0, bones=[]), pose=PoseData(pose_bones=[]))

SCENE = SceneState(
    meta=SceneMeta(blender_version="4.2.0", scene_name="test", current_frame=1, fps=24, frame_start=1, frame_end=250, render_engine="CYCLES"),
    actors=[ACTOR_A, ACTOR_B],
    spatial=SpatialData(camera=CameraData(name="Cam", location=[5,-5,3], rotation_euler=[1.1,0,0.785], focal_length=50), actor_distances=[])
)

def test_distance_between_actors():
    summary = calculate_spatial_summary(SCENE)
    assert summary["actor_distances"][0]["distance"] == pytest.approx(2.0, abs=0.01)

def test_camera_info():
    summary = calculate_spatial_summary(SCENE)
    assert summary["camera"]["name"] == "Cam"


def timeline_report(drift=0.0):
    def frame(number, control_center, experiment_center):
        return {
            "frame_info": {"current": number, "fps": 24},
            "spatial": {
                "actor_bounds": {
                    "control_mesh_person0": {"center": control_center, "size": [0.6, 0.4, 1.8]},
                    "experiment_joe_Belt": {"center": experiment_center, "size": [0.8, 0.5, 1.8]},
                }
            },
            "actors": [],
        }

    return {
        "frame_reports": [
            frame(1, [0.0, 0.0, 0.9], [4.7, 0.0, 0.9]),
            frame(5, [0.2, 0.1, 0.9], [4.9 + drift, 0.1, 0.9]),
            frame(9, [0.4, 0.2, 0.9], [5.1 + drift, 0.2, 0.9]),
        ]
    }


def test_translation_locks_pass_when_experiment_is_constant_control_translation():
    report = evaluate_translation_locks(
        timeline_report(),
        pair_specs=["control_mesh_person0=experiment_joe"],
        tolerance=0.03,
    )

    assert report["schema"] == "motion_state_translation_locks.v1"
    assert report["verdict"] == "pass"
    assert report["pairs"][0]["baseline_translation"] == [4.7, 0.0, 0.0]
    assert report["pairs"][0]["drift_m"]["max"] == pytest.approx(0.0)


def test_translation_locks_fail_when_experiment_stops_being_a_translation_clone():
    report = evaluate_translation_locks(
        timeline_report(drift=0.12),
        pair_specs=["control_mesh_person0=experiment_joe"],
        tolerance=0.03,
    )

    assert report["verdict"] == "fail"
    assert report["pairs"][0]["verdict"] == "fail"
    assert report["pairs"][0]["drift_m"]["max"] == pytest.approx(0.12)


def test_cli_embeds_translation_locks_for_timeline_reports(tmp_path):
    import json
    import subprocess
    import sys

    raw = tmp_path / "raw.json"
    raw.write_text(
        json.dumps(
            {
                "frames": [
                    {
                        "meta": {
                            "blender_version": "4.2.0",
                            "scene_name": "t",
                            "current_frame": 1,
                            "fps": 24,
                            "frame_start": 1,
                            "frame_end": 2,
                            "render_engine": "CYCLES",
                        },
                        "actors": [
                            {
                                "name": "control_mesh_person0",
                                "type": "MESH",
                                "visible": True,
                                "world_matrix": [],
                                "mesh": {"bbox_min": [0, 0, 0], "bbox_max": [1, 1, 1]},
                                "armature": {"bone_count": 0, "bones": []},
                                "pose": {"pose_bones": []},
                            },
                            {
                                "name": "experiment_joe_Belt",
                                "type": "MESH",
                                "visible": True,
                                "world_matrix": [],
                                "mesh": {"bbox_min": [4, 0, 0], "bbox_max": [5, 1, 1]},
                                "armature": {"bone_count": 0, "bones": []},
                                "pose": {"pose_bones": []},
                            },
                        ],
                        "spatial": {
                            "camera": {
                                "name": "Cam",
                                "location": [0, 0, 0],
                                "rotation_euler": [0, 0, 0],
                                "focal_length": 50,
                            }
                        },
                    },
                    {
                        "meta": {
                            "blender_version": "4.2.0",
                            "scene_name": "t",
                            "current_frame": 2,
                            "fps": 24,
                            "frame_start": 1,
                            "frame_end": 2,
                            "render_engine": "CYCLES",
                        },
                        "actors": [
                            {
                                "name": "control_mesh_person0",
                                "type": "MESH",
                                "visible": True,
                                "world_matrix": [],
                                "mesh": {"bbox_min": [1, 0, 0], "bbox_max": [2, 1, 1]},
                                "armature": {"bone_count": 0, "bones": []},
                                "pose": {"pose_bones": []},
                            },
                            {
                                "name": "experiment_joe_Belt",
                                "type": "MESH",
                                "visible": True,
                                "world_matrix": [],
                                "mesh": {"bbox_min": [5, 0, 0], "bbox_max": [6, 1, 1]},
                                "armature": {"bone_count": 0, "bones": []},
                                "pose": {"pose_bones": []},
                            },
                        ],
                        "spatial": {
                            "camera": {
                                "name": "Cam",
                                "location": [0, 0, 0],
                                "rotation_euler": [0, 0, 0],
                                "focal_length": 50,
                            }
                        },
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "analyzer.cli",
            str(raw),
            "--output-md",
            str(tmp_path / "report.md"),
            "--output-json",
            str(tmp_path / "report.json"),
            "--translation-lock-pair",
            "control_mesh_person0=experiment_joe",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["translation_locks"]["verdict"] == "pass"
