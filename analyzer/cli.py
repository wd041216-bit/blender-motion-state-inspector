import argparse
import json
import sys
from pathlib import Path

from analyzer.loader import load_raw_state
from analyzer.morphology import calculate_morphology
from analyzer.skeleton_semantics import map_skeleton_semantics
from analyzer.pose_classifier import classify_pose
from analyzer.anomaly_detector import detect_anomalies
from analyzer.spatial import calculate_spatial_summary
from analyzer.contact_detector import detect_contacts
from analyzer.formatter import format_json, format_markdown


def build_report(scene):
    actors_report = []
    for actor in scene.actors:
        morph = calculate_morphology(actor)
        sem = map_skeleton_semantics([b.name for b in actor.armature.bones])
        pose = classify_pose(pelvis_pitch=0, spine_bend=0, limb_extension=0.9)
        joint_angles = {}
        for pb in actor.pose.pose_bones:
            q = pb.rotation_quaternion
            joint_angles[pb.name] = q[0] * 180
        foot_bones = [b for b in actor.armature.bones if "foot" in b.name.lower()]
        clearance = 0.0
        if foot_bones:
            clearance = max(b.world_head[2] for b in foot_bones)
        anoms = detect_anomalies(
            joint_angles=joint_angles,
            bbox_aspect_yx=morph["height"] / morph["shoulder_width"] if morph["shoulder_width"] else 1.0,
            bbox_aspect_yz=morph["height"] / (morph["bbox_volume"] / morph["shoulder_width"] / morph["height"]) if morph["bbox_volume"] else 1.0,
            foot_ground_clearance=clearance,
            is_jumping=False,
        )
        contacts = detect_contacts(
            [{"name": b.name, "world_head": b.world_head, "world_tail": b.world_tail} for b in foot_bones],
        )
        actors_report.append({
            "name": actor.name,
            "morphology": morph,
            "pose_state": pose,
            "anomalies": anoms,
            "contacts": contacts,
            "skeleton_semantics": sem,
        })
    spatial = calculate_spatial_summary(scene)
    summary_parts = []
    for ar in actors_report:
        status = f"{ar['name']} {ar['pose_state']}"
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
    }


def main(argv=None):
    parser = argparse.ArgumentParser(prog="blender-state-inspector")
    parser.add_argument("input", help="Path to raw_state.json")
    parser.add_argument("--output-md", default="report.md", help="Markdown output path")
    parser.add_argument("--output-json", default="report.json", help="JSON output path")
    args = parser.parse_args(argv)

    scene = load_raw_state(args.input)
    report = build_report(scene)

    Path(args.output_md).write_text(format_markdown(report), encoding="utf-8")
    Path(args.output_json).write_text(format_json(report), encoding="utf-8")
    print(f"Report written to {args.output_md} and {args.output_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
