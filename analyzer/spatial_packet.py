from __future__ import annotations

import math
import re
from typing import Any


SCHEMA = "motion_state_spatial_packet.v1"


def _slug(value: str) -> str:
    rendered = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return rendered or "unnamed"


def _actor_class(actor: dict[str, Any]) -> str:
    classification = actor.get("classification", {})
    klass = str(classification.get("class") or "actor").lower()
    if classification.get("is_character"):
        return "character"
    if any(token in actor.get("name", "").lower() for token in ("floor", "ground", "plane")):
        return "floor"
    if any(token in actor.get("name", "").lower() for token in ("camera", "cam")):
        return "camera"
    if any(token in actor.get("name", "").lower() for token in ("control", "teacher", "kimodo", "smplx")):
        return "control"
    return klass


def _actor_id(actor: dict[str, Any]) -> str:
    return f"{_actor_class(actor)}:{_slug(str(actor.get('name', 'actor')))}"


def _number(value: float | int | None, digits: int = 3) -> float:
    return round(float(value or 0.0), digits)


def _bounds_for(report: dict[str, Any], actor: dict[str, Any]) -> dict[str, list[float]]:
    name = str(actor.get("name", ""))
    bounds = report.get("spatial", {}).get("actor_bounds", {}).get(name, {})
    center = bounds.get("center")
    size = bounds.get("size")
    if center and size:
        return {"center": [_number(v) for v in center], "size": [_number(v) for v in size]}
    morph = actor.get("morphology", {})
    height = float(morph.get("height") or morph.get("vertical_extent") or 0.0)
    width = float(morph.get("shoulder_width") or 0.0)
    depth = float(morph.get("depth") or 0.0)
    return {"center": [0.0, 0.0, _number(height / 2.0)], "size": [_number(width), _number(depth), _number(height)]}


def _distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _relation_label(delta: list[float], distance: float) -> str:
    horizontal = []
    if delta[1] > 0.25:
        horizontal.append("front")
    elif delta[1] < -0.25:
        horizontal.append("behind")
    if delta[0] > 0.25:
        horizontal.append("right")
    elif delta[0] < -0.25:
        horizontal.append("left")
    if not horizontal:
        horizontal.append("same_xy")
    if distance < 1.0:
        band = "near"
    elif distance < 3.0:
        band = "mid"
    else:
        band = "far"
    return "_".join(horizontal + [band])


def _overlap_1d(a_center: float, a_size: float, b_center: float, b_size: float) -> float:
    a0 = a_center - a_size / 2.0
    a1 = a_center + a_size / 2.0
    b0 = b_center - b_size / 2.0
    b1 = b_center + b_size / 2.0
    return max(0.0, min(a1, b1) - max(a0, b0))


def _actor_packet(report: dict[str, Any], actor: dict[str, Any], ego_token: str | None) -> dict[str, Any]:
    bounds = _bounds_for(report, actor)
    facing = actor.get("facing", {}) or {}
    vector = facing.get("vector") if isinstance(facing.get("vector"), list) else None
    is_ego = bool(ego_token and ego_token.lower() in str(actor.get("name", "")).lower())
    priority = 1.0 if actor.get("classification", {}).get("is_character") or is_ego else 0.5
    return {
        "id": _actor_id(actor),
        "name": actor.get("name", ""),
        "class": _actor_class(actor),
        "priority": priority,
        "pose": actor.get("pose_state", "unknown"),
        "bbox": bounds,
        "basis": {
            "facing": vector,
            "up": [0.0, 0.0, 1.0],
            "confidence": _number(facing.get("confidence"), 3),
        },
        "contacts": actor.get("contacts", []),
        "ground_clearance_m": actor.get("ground_clearance_m"),
    }


def _relations(actors: list[dict[str, Any]], ego_actor: str | None, top_k: int) -> list[dict[str, Any]]:
    rows = []
    ego_token = ego_actor.lower() if ego_actor else None
    for i, a in enumerate(actors):
        for b in actors[i + 1 :]:
            if ego_token and ego_token not in a["name"].lower() and ego_token not in b["name"].lower():
                continue
            ac = a["bbox"]["center"]
            bc = b["bbox"]["center"]
            asize = a["bbox"]["size"]
            bsize = b["bbox"]["size"]
            delta = [bc[idx] - ac[idx] for idx in range(3)]
            distance = _distance(ac, bc)
            rows.append({
                "a": a["id"],
                "b": b["id"],
                "relation": _relation_label(delta, distance),
                "distance_m": _number(distance, 3),
                "vertical_delta_m": _number(delta[2], 3),
                "overlap": {
                    "x": _number(_overlap_1d(ac[0], asize[0], bc[0], bsize[0]), 3),
                    "y": _number(_overlap_1d(ac[1], asize[1], bc[1], bsize[1]), 3),
                    "z": _number(_overlap_1d(ac[2], asize[2], bc[2], bsize[2]), 3),
                },
            })
    return sorted(rows, key=lambda row: row["distance_m"])[: max(0, top_k)]


def build_spatial_packet(report: dict[str, Any], ego_actor: str | None = None, top_k: int = 24) -> dict[str, Any]:
    actors = [_actor_packet(report, actor, ego_actor) for actor in report.get("actors", [])]
    frame = report.get("frame_info", {})
    bounds = [actor["bbox"] for actor in actors]
    if bounds:
        mins = [
            min(item["center"][axis] - item["size"][axis] / 2.0 for item in bounds)
            for axis in range(3)
        ]
        maxs = [
            max(item["center"][axis] + item["size"][axis] / 2.0 for item in bounds)
            for axis in range(3)
        ]
    else:
        mins = [0.0, 0.0, 0.0]
        maxs = [0.0, 0.0, 0.0]
    return {
        "schema": SCHEMA,
        "scene": {
            "frame": frame.get("current"),
            "fps": frame.get("fps"),
            "world_bounds": {"min": [_number(v) for v in mins], "max": [_number(v) for v in maxs]},
            "ground": report.get("ground", {}),
            "camera": report.get("spatial", {}).get("camera", {}),
        },
        "actors": actors,
        "relations": _relations(actors, ego_actor, top_k),
    }


def _merge_pose_ranges(frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    active: dict[tuple[str, str], dict[str, Any]] = {}
    for packet in frames:
        frame = packet.get("scene", {}).get("frame")
        seen = set()
        for actor in packet.get("actors", []):
            event = f"pose:{actor.get('pose', 'unknown')}"
            key = (actor["id"], event)
            seen.add(key)
            if key not in active:
                active[key] = {"range": [frame, frame], "actor": actor["id"], "event": event}
            else:
                active[key]["range"][1] = frame
        for key in list(active):
            if key not in seen:
                events.append(active.pop(key))
    events.extend(active.values())
    return events


def build_timeline_spatial_packet(report: dict[str, Any], ego_actor: str | None = None, top_k: int = 24) -> dict[str, Any]:
    frames = [
        build_spatial_packet(frame_report, ego_actor=ego_actor, top_k=top_k)
        for frame_report in report.get("frame_reports", [])
    ]
    return {
        "schema": SCHEMA,
        "kind": "timeline",
        "meta": report.get("meta", {}),
        "frames": frames,
        "temporal_events": _merge_pose_ranges(frames),
    }
