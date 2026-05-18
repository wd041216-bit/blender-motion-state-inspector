from __future__ import annotations

import math
from typing import Optional

from analyzer.loader import Actor, BoneData
from analyzer.morphology import estimate_unit_scale
from analyzer.skeleton_semantics import map_skeleton_semantics


def _sub(a, b):
    return [x - y for x, y in zip(a, b)]


def _add(a, b):
    return [x + y for x, y in zip(a, b)]


def _mul(a, s):
    return [x * s for x in a]


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def _norm(a):
    return math.sqrt(_dot(a, a))


def _normalize(a):
    n = _norm(a)
    if n < 1e-8:
        return None
    return [x / n for x in a]


def _angle_deg(a, b) -> Optional[float]:
    na = _normalize(a)
    nb = _normalize(b)
    if not na or not nb:
        return None
    value = max(-1.0, min(1.0, _dot(na, nb)))
    return math.degrees(math.acos(value))


def _bone_map(actor: Actor) -> dict[str, BoneData]:
    return {bone.name: bone for bone in actor.armature.bones}


def _bone(actor: Actor, semantics: dict, key: str) -> Optional[BoneData]:
    name = semantics.get(key)
    return _bone_map(actor).get(name) if name else None


def _midpoint(a, b):
    return _mul(_add(a, b), 0.5)


def infer_facing(actor: Actor) -> dict:
    bones = _bone_map(actor)
    semantics = map_skeleton_semantics(list(bones))
    bmin = actor.mesh.bbox_world_min or actor.mesh.bbox_min
    bmax = actor.mesh.bbox_world_max or actor.mesh.bbox_max
    unit_scale = estimate_unit_scale(max(bmax[i] - bmin[i] for i in range(3)))

    pelvis = _bone(actor, semantics, "pelvis") or _bone(actor, semantics, "root")
    head = _bone(actor, semantics, "head")
    left_shoulder = _bone(actor, semantics, "left_shoulder") or _bone(actor, semantics, "left_arm")
    right_shoulder = _bone(actor, semantics, "right_shoulder") or _bone(actor, semantics, "right_arm")
    left_foot = _bone(actor, semantics, "left_foot")
    right_foot = _bone(actor, semantics, "right_foot")
    left_toe = _bone(actor, semantics, "left_toe")
    right_toe = _bone(actor, semantics, "right_toe")

    up = _normalize(_sub(head.world_head, pelvis.world_head)) if head and pelvis else None
    side = _normalize(_sub(left_shoulder.world_head, right_shoulder.world_head)) if left_shoulder and right_shoulder else None
    torso_forward_candidates = []
    if up and side:
        fwd = _normalize(_cross(side, up))
        if fwd:
            torso_forward_candidates = [fwd, _mul(fwd, -1.0)]

    foot_vectors = []
    if left_foot and left_toe:
        foot_vectors.append(_sub(left_toe.world_head, left_foot.world_head))
    if right_foot and right_toe:
        foot_vectors.append(_sub(right_toe.world_head, right_foot.world_head))
    foot_forward = None
    if foot_vectors:
        total = [0.0, 0.0, 0.0]
        for vec in foot_vectors:
            total = _add(total, vec)
        foot_forward = _normalize(total)

    source = "unknown"
    confidence = 0.0
    facing = foot_forward
    if foot_forward:
        source = "toe_average"
        confidence = 0.75
    if torso_forward_candidates:
        if foot_forward:
            facing = max(torso_forward_candidates, key=lambda candidate: _dot(candidate, foot_forward))
            source = "torso_cross_validated_by_toes"
            confidence = 0.9
        elif not facing:
            facing = torso_forward_candidates[0]
            source = "torso_cross_unoriented"
            confidence = 0.45

    torso_to_foot_angle = None
    if torso_forward_candidates and foot_forward:
        torso_to_foot_angle = min(
            _angle_deg(candidate, foot_forward) or 180.0
            for candidate in torso_forward_candidates
        )

    vertical = [0.0, 0.0, 1.0]
    torso_vertical_angle = _angle_deg(up, vertical) if up else None

    return {
        "vector": [round(v, 6) for v in facing] if facing else None,
        "source": source,
        "confidence": confidence,
        "up_vector": [round(v, 6) for v in up] if up else None,
        "side_vector": [round(v, 6) for v in side] if side else None,
        "foot_forward_vector": [round(v, 6) for v in foot_forward] if foot_forward else None,
        "torso_to_foot_angle_deg": round(torso_to_foot_angle, 3) if torso_to_foot_angle is not None else None,
        "torso_vertical_angle_deg": round(torso_vertical_angle, 3) if torso_vertical_angle is not None else None,
        "unit_scale": unit_scale,
    }
