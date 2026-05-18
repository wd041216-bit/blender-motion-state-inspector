from __future__ import annotations

from itertools import combinations
from typing import Iterable

from analyzer.actor_classifier import classify_actor
from analyzer.loader import Actor, SceneState, load_raw_state


GROUND_NAME_HINTS = ("floor", "ground", "plane")


def actor_bbox(actor: Actor) -> dict:
    min_v = actor.mesh.bbox_world_min or actor.mesh.bbox_min
    max_v = actor.mesh.bbox_world_max or actor.mesh.bbox_max
    return {
        "min": [float(value) for value in min_v],
        "max": [float(value) for value in max_v],
    }


def bbox_center(bbox: dict) -> list[float]:
    return [round((bbox["min"][axis] + bbox["max"][axis]) * 0.5, 5) for axis in range(3)]


def bbox_overlap(a: dict, b: dict, tolerance: float = 0.0) -> dict | None:
    overlap = [
        min(a["max"][axis], b["max"][axis]) - max(a["min"][axis], b["min"][axis])
        for axis in range(3)
    ]
    if any(value <= tolerance for value in overlap):
        return None
    overlap_min = [max(a["min"][axis], b["min"][axis]) for axis in range(3)]
    overlap_max = [min(a["max"][axis], b["max"][axis]) for axis in range(3)]
    return {
        "axes": {axis: round(overlap[index], 5) for index, axis in enumerate(("x", "y", "z"))},
        "penetration_depth": round(min(overlap), 5),
        "center": bbox_center({"min": overlap_min, "max": overlap_max}),
        "bbox": {
            "min": [round(value, 5) for value in overlap_min],
            "max": [round(value, 5) for value in overlap_max],
        },
    }


def is_ground_like(actor: Actor) -> bool:
    name = actor.name.lower()
    return any(hint in name for hint in GROUND_NAME_HINTS)


def ground_reference(scene: SceneState) -> tuple[float, bool]:
    candidates = []
    for actor in scene.actors:
        if is_ground_like(actor):
            bbox = actor_bbox(actor)
            candidates.append(bbox["max"][2])
    return (max(candidates), True) if candidates else (0.0, False)


def detect_frame_clipping(scene: SceneState, tolerance: float = 0.0) -> list[dict]:
    frame = scene.meta.current_frame
    ground_z, explicit_ground = ground_reference(scene)
    visible_actors = [actor for actor in scene.actors if actor.visible]
    bboxes = {actor.name: actor_bbox(actor) for actor in visible_actors}
    events = []

    for actor in visible_actors:
        if is_ground_like(actor):
            continue
        bbox = bboxes[actor.name]
        penetration = ground_z - bbox["min"][2]
        if penetration > tolerance:
            events.append(
                {
                    "type": "ground_penetration",
                    "frame": frame,
                    "actor": actor.name,
                    "classification": classify_actor(actor)["class"],
                    "ground_z": round(ground_z, 5),
                    "explicit_ground": explicit_ground,
                    "penetration_depth": round(penetration, 5),
                    "actor_bottom_center": [
                        round((bbox["min"][0] + bbox["max"][0]) * 0.5, 5),
                        round((bbox["min"][1] + bbox["max"][1]) * 0.5, 5),
                        round(bbox["min"][2], 5),
                    ],
                    "actor_bbox": bbox,
                }
            )

    non_ground = [actor for actor in visible_actors if not is_ground_like(actor)]
    for actor_a, actor_b in combinations(non_ground, 2):
        overlap = bbox_overlap(bboxes[actor_a.name], bboxes[actor_b.name], tolerance=tolerance)
        if not overlap:
            continue
        events.append(
            {
                "type": "bbox_overlap",
                "frame": frame,
                "actors": [actor_a.name, actor_b.name],
                "classifications": [classify_actor(actor_a)["class"], classify_actor(actor_b)["class"]],
                "overlap": overlap,
                "actor_bboxes": {
                    actor_a.name: bboxes[actor_a.name],
                    actor_b.name: bboxes[actor_b.name],
                },
            }
        )

    return events


def build_temporal_clip_check(
    raw: dict,
    tolerance: float = 0.0,
    frame_start: int | None = None,
    frame_end: int | None = None,
) -> dict:
    frame_events = []
    frames: Iterable[dict]
    if "frames" in raw:
        frames = raw.get("frames", [])
        meta = raw.get("meta", {})
    else:
        frames = [raw]
        meta = raw.get("meta", {})

    sampled_frames = 0
    checked_frames = 0
    for frame_raw in frames:
        sampled_frames += 1
        frame_number = int(frame_raw.get("meta", {}).get("current_frame", 0))
        if frame_start is not None and frame_number < frame_start:
            continue
        if frame_end is not None and frame_number > frame_end:
            continue
        checked_frames += 1
        scene = load_raw_state(frame_raw)
        frame_events.extend(detect_frame_clipping(scene, tolerance=tolerance))

    return {
        "schema": "temporal_clip_check.v1",
        "verdict": "pass" if not frame_events else "fail",
        "summary": (
            f"PASS: no clipping detected across {checked_frames} checked frames"
            if not frame_events
            else f"FAIL: {len(frame_events)} clipping events across {checked_frames} checked frames"
        ),
        "meta": meta,
        "frame_range": {"start": frame_start, "end": frame_end},
        "sampled_frames": sampled_frames,
        "checked_frames": checked_frames,
        "tolerance": tolerance,
        "events": frame_events,
    }
