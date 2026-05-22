import argparse
import json
import sys
from pathlib import Path

from analyzer.loader import load_raw_state
from analyzer.actor_classifier import classify_actor
from analyzer.morphology import calculate_morphology
from analyzer.skeleton_semantics import map_skeleton_semantics
from analyzer.pose_classifier import classify_pose
from analyzer.anomaly_detector import detect_anomalies
from analyzer.spatial import calculate_spatial_summary
from analyzer.spatial_packet import build_spatial_packet, build_timeline_spatial_packet
from analyzer.contact_detector import detect_contacts
from analyzer.formatter import format_json, format_markdown
from analyzer.facing import infer_facing
from analyzer.clip_detector import build_temporal_clip_check


def _bone_lookup(actor):
    return {b.name: b for b in actor.armature.bones}


def _semantic_bone(actor, semantics, key):
    name = semantics.get(key)
    return _bone_lookup(actor).get(name) if name else None


def _ground_reference(scene):
    candidates = []
    for actor in scene.actors:
        name = actor.name.lower()
        if any(token in name for token in ("floor", "ground", "plane")):
            bmax = actor.mesh.bbox_world_max or actor.mesh.bbox_max
            candidates.append(bmax[2])
    return (max(candidates), True) if candidates else (0.0, False)


def _character_pose(actor, semantics, facing):
    pelvis = _semantic_bone(actor, semantics, "pelvis") or _semantic_bone(actor, semantics, "root")
    head = _semantic_bone(actor, semantics, "head")
    pelvis_pitch = 0.0
    if pelvis and head and head.world_head[2] < pelvis.world_head[2]:
        pelvis_pitch = 100.0
    spine_bend = facing.get("torso_vertical_angle_deg") or 0.0
    return classify_pose(pelvis_pitch=pelvis_pitch, spine_bend=spine_bend, limb_extension=0.9)


def _foot_clearance(actor, semantics, ground_z, unit_scale):
    foot_keys = ("left_foot", "right_foot", "left_toe", "right_toe")
    z_values = []
    for key in foot_keys:
        bone = _semantic_bone(actor, semantics, key)
        if bone:
            z_values.append(bone.world_head[2])
    if not z_values:
        return None
    return (min(z_values) - ground_z) * unit_scale


def build_report(scene):
    actors_report = []
    ground_z, has_ground = _ground_reference(scene)
    for actor in scene.actors:
        classification = classify_actor(actor)
        morph = calculate_morphology(actor)
        sem = map_skeleton_semantics([b.name for b in actor.armature.bones])
        facing = infer_facing(actor) if classification["is_character"] else {
            "vector": None,
            "source": "not_character",
            "confidence": 0.0,
        }
        pose = _character_pose(actor, sem, facing) if classification["is_character"] else "静态物体"
        joint_angles = {}
        for pb in actor.pose.pose_bones:
            q = pb.rotation_quaternion
            joint_angles[pb.name] = q[0] * 180
        contact_bones = []
        for key in ("left_foot", "right_foot", "left_toe", "right_toe", "left_hand", "right_hand"):
            bone = _semantic_bone(actor, sem, key)
            if bone:
                contact_bones.append({"name": bone.name, "world_head": bone.world_head, "world_tail": bone.world_head})
        clearance = _foot_clearance(actor, sem, ground_z, morph.get("unit_scale", 1.0))
        if classification["is_character"]:
            anoms = detect_anomalies(
                joint_angles=joint_angles,
                bbox_aspect_yx=morph["height"] / morph["shoulder_width"] if morph["shoulder_width"] else 1.0,
                bbox_aspect_yz=morph["height"] / morph["depth"] if morph.get("depth") else 1.0,
                foot_ground_clearance=clearance or 0.0,
                is_jumping=not has_ground,
            )
            contacts = detect_contacts(contact_bones, ground_y=ground_z, threshold=0.08 / morph.get("unit_scale", 1.0))
        else:
            anoms = []
            contacts = []
        actors_report.append({
            "name": actor.name,
            "classification": classification,
            "morphology": morph,
            "pose_state": pose,
            "facing": facing,
            "anomalies": anoms,
            "contacts": contacts,
            "skeleton_semantics": sem,
            "ground_clearance_m": round(clearance, 4) if clearance is not None else None,
        })
    spatial = calculate_spatial_summary(scene)
    summary_parts = []
    for ar in actors_report:
        status = f"{ar['name']} {ar['classification']['class']} {ar['pose_state']}"
        if ar["anomalies"]:
            status += "，检测到异常"
        else:
            status += "，无异常"
        summary_parts.append(status)
    return {
        "summary": "；".join(summary_parts),
        "actors": actors_report,
        "spatial": spatial,
        "frame_info": {"current": scene.meta.current_frame, "fps": scene.meta.fps},
        "ground": {"z": ground_z, "explicit": has_ground},
    }


def build_timeline_report(
    raw: dict,
    clip_check: bool = False,
    clip_tolerance: float = 0.0,
    clip_frame_start: int | None = None,
    clip_frame_end: int | None = None,
):
    frame_reports = []
    jsonl_rows = []
    for frame_raw in raw.get("frames", []):
        report = build_report(load_raw_state(frame_raw))
        frame_reports.append(report)
        for actor in report.get("actors", []):
            if actor["classification"]["is_character"]:
                jsonl_rows.append({
                    "frame": report["frame_info"]["current"],
                    "actor": actor["name"],
                    "pose_state": actor["pose_state"],
                    "facing": actor["facing"],
                    "ground_clearance_m": actor["ground_clearance_m"],
                    "anomalies": actor["anomalies"],
                })

    anomaly_events = []
    active = {}
    for row in jsonl_rows:
        frame = row["frame"]
        for anomaly in row.get("anomalies", []):
            key = (row["actor"], anomaly.get("type", "unknown"))
            if key not in active:
                active[key] = {"actor": row["actor"], "type": key[1], "start": frame, "end": frame, "count": 1}
            else:
                active[key]["end"] = frame
                active[key]["count"] += 1
    anomaly_events = list(active.values())

    report = {
        "summary": f"Analyzed {len(frame_reports)} sampled frames",
        "meta": raw.get("meta", {}),
        "frame_reports": frame_reports,
        "frame_diagnostics": jsonl_rows,
        "event_diagnostics": anomaly_events,
    }
    if clip_check:
        report["clip_check"] = build_temporal_clip_check(
            raw,
            tolerance=clip_tolerance,
            frame_start=clip_frame_start,
            frame_end=clip_frame_end,
        )
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(prog="blender-state-inspector")
    parser.add_argument("input", help="Path to raw_state.json")
    parser.add_argument("--output-md", default="report.md", help="Markdown output path")
    parser.add_argument("--output-json", default="report.json", help="JSON output path")
    parser.add_argument("--output-jsonl", default=None, help="Optional per-frame diagnostics JSONL path for animation_state input")
    parser.add_argument("--output-spatial-packet", default=None, help="Optional compact spatial packet JSON for agent context")
    parser.add_argument("--spatial-top-k", type=int, default=24, help="Maximum compact spatial relations to emit")
    parser.add_argument("--spatial-ego-actor", default=None, help="Prioritize relations touching an actor name token")
    parser.add_argument("--clip-check", action="store_true", help="Run temporal clipping/interpenetration pass-fail diagnostics")
    parser.add_argument("--clip-tolerance", type=float, default=0.0, help="Allowed overlap/penetration tolerance in scene units")
    parser.add_argument("--clip-frame-start", type=int, default=None, help="Optional first frame for temporal clip check")
    parser.add_argument("--clip-frame-end", type=int, default=None, help="Optional last frame for temporal clip check")
    args = parser.parse_args(argv)

    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if "frames" in raw:
        report = build_timeline_report(
            raw,
            clip_check=args.clip_check,
            clip_tolerance=args.clip_tolerance,
            clip_frame_start=args.clip_frame_start,
            clip_frame_end=args.clip_frame_end,
        )
    else:
        scene = load_raw_state(raw)
        report = build_report(scene)
        if args.clip_check:
            report["clip_check"] = build_temporal_clip_check(
                raw,
                tolerance=args.clip_tolerance,
                frame_start=args.clip_frame_start,
                frame_end=args.clip_frame_end,
            )

    Path(args.output_md).write_text(format_markdown(report), encoding="utf-8")
    Path(args.output_json).write_text(format_json(report), encoding="utf-8")
    if args.output_spatial_packet:
        if "frame_reports" in report:
            packet = build_timeline_spatial_packet(
                report,
                ego_actor=args.spatial_ego_actor,
                top_k=args.spatial_top_k,
            )
        else:
            packet = build_spatial_packet(
                report,
                ego_actor=args.spatial_ego_actor,
                top_k=args.spatial_top_k,
            )
        Path(args.output_spatial_packet).write_text(json.dumps(packet, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.output_jsonl and "frame_diagnostics" in report:
        Path(args.output_jsonl).write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in report["frame_diagnostics"]),
            encoding="utf-8",
        )
    print(f"Report written to {args.output_md} and {args.output_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
