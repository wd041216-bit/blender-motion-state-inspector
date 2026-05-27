import json
import subprocess
import sys

from analyzer.spatial_packet import build_spatial_packet, build_timeline_spatial_packet


def actor_report(name, klass, center, size, pose="static", facing=None):
    return {
        "name": name,
        "classification": {"class": klass, "is_character": klass == "character"},
        "pose_state": pose,
        "facing": facing or {"vector": [0.0, 1.0, 0.0], "confidence": 0.8},
        "contacts": [],
        "ground_clearance_m": 0.0,
        "morphology": {"height": size[2], "unit_scale": 1.0},
        "skeleton_semantics": {},
    }


def report(frame=1):
    return {
        "frame_info": {"current": frame, "fps": 24},
        "ground": {"z": 0.0, "explicit": True},
        "actors": [
            actor_report("Chad Body", "character", [0.0, 0.0, 1.0], [0.8, 0.4, 1.8], pose="airborne"),
            actor_report("Chair 01", "prop", [1.0, 2.0, 0.5], [0.6, 0.6, 1.0], pose="static"),
            actor_report("Far Lamp", "prop", [8.0, 0.0, 1.0], [0.3, 0.3, 2.0], pose="static"),
        ],
        "spatial": {
            "camera": {"name": "Cam", "location": [0, -4, 2], "rotation_euler": [1, 0, 0], "focal_length": 50},
            "actor_bounds": {
                "Chad Body": {"center": [0.0, 0.0, 1.0], "size": [0.8, 0.4, 1.8]},
                "Chair 01": {"center": [1.0, 2.0, 0.5], "size": [0.6, 0.6, 1.0]},
                "Far Lamp": {"center": [8.0, 0.0, 1.0], "size": [0.3, 0.3, 2.0]},
            },
        },
    }


def test_spatial_packet_uses_stable_ids_and_actor_centric_relations():
    packet = build_spatial_packet(report(), ego_actor="Chad", top_k=4)

    assert packet["schema"] == "motion_state_spatial_packet.v1"
    assert packet["actors"][0]["id"] == "character:chad_body"
    assert packet["actors"][0]["priority"] == 1.0
    assert packet["relations"][0]["a"] == "character:chad_body"
    assert packet["relations"][0]["b"] == "prop:chair_01"
    assert packet["relations"][0]["relation"] == "front_right_mid"
    assert packet["relations"][0]["distance_m"] == 2.291


def test_spatial_packet_limits_relations_by_top_k_and_ego_actor():
    packet = build_spatial_packet(report(), ego_actor="Chad", top_k=1)

    assert len(packet["relations"]) == 1
    assert packet["relations"][0]["b"] == "prop:chair_01"


def test_timeline_spatial_packet_merges_pose_event_ranges():
    timeline = {
        "frame_reports": [
            report(frame=1),
            report(frame=5),
            {
                **report(frame=9),
                "actors": [
                    actor_report("Chad Body", "character", [0.0, 0.0, 1.0], [0.8, 0.4, 1.8], pose="standing"),
                    actor_report("Chair 01", "prop", [1.0, 2.0, 0.5], [0.6, 0.6, 1.0]),
                ],
                "spatial": {
                    **report(frame=9)["spatial"],
                    "actor_bounds": {
                        "Chad Body": {"center": [0.0, 0.0, 1.0], "size": [0.8, 0.4, 1.8]},
                        "Chair 01": {"center": [1.0, 2.0, 0.5], "size": [0.6, 0.6, 1.0]},
                    },
                },
            },
        ]
    }

    packet = build_timeline_spatial_packet(timeline, ego_actor="Chad", top_k=2)

    assert packet["schema"] == "motion_state_spatial_packet.v1"
    assert len(packet["frames"]) == 3
    assert packet["temporal_events"][0] == {
        "range": [1, 5],
        "actor": "character:chad_body",
        "event": "pose:airborne",
    }


def test_cli_writes_spatial_packet_for_single_frame(tmp_path):
    raw = tmp_path / "raw.json"
    raw.write_text(json.dumps({
        "meta": {"blender_version": "4.2.0", "scene_name": "t", "current_frame": 1, "fps": 24, "frame_start": 1, "frame_end": 1, "render_engine": "CYCLES"},
        "actors": [],
        "spatial": {"camera": {"name": "Cam", "location": [0, 0, 0], "rotation_euler": [0, 0, 0], "focal_length": 50}, "actor_distances": []},
    }))
    packet = tmp_path / "spatial_packet.json"

    result = subprocess.run([
        sys.executable,
        "-m",
        "analyzer.cli",
        str(raw),
        "--output-md",
        str(tmp_path / "report.md"),
        "--output-json",
        str(tmp_path / "report.json"),
        "--output-spatial-packet",
        str(packet),
    ], capture_output=True, text=True)

    assert result.returncode == 0
    assert json.loads(packet.read_text())["schema"] == "motion_state_spatial_packet.v1"
