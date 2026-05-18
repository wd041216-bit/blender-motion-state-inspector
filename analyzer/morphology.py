from analyzer.loader import Actor
from analyzer.skeleton_semantics import map_skeleton_semantics
from typing import Dict

def estimate_unit_scale(raw_height: float) -> float:
    if raw_height > 20.0:
        return 0.01
    if raw_height > 4.0:
        return 0.1
    return 1.0

def _bbox(actor: Actor):
    bmin = actor.mesh.bbox_world_min or actor.mesh.bbox_min
    bmax = actor.mesh.bbox_world_max or actor.mesh.bbox_max
    return bmin, bmax

def calculate_morphology(actor: Actor) -> Dict[str, float]:
    bmin, bmax = _bbox(actor)
    raw_dx = bmax[0] - bmin[0]
    raw_dy = bmax[1] - bmin[1]
    raw_dz = bmax[2] - bmin[2]
    unit_scale = estimate_unit_scale(max(raw_dx, raw_dy, raw_dz))
    dx = abs(raw_dx * unit_scale)
    dy = abs(raw_dy * unit_scale)
    dz = abs(raw_dz * unit_scale)
    dims = sorted([dx, dy, dz], reverse=True)
    height = dims[0]
    shoulder_width = dims[1] if len(dims) > 1 else 0.0
    depth = dims[2] if len(dims) > 2 else 0.0
    volume = dx * dy * dz

    arm_length = 0.0
    leg_length = 0.0
    head_torso_ratio = 0.0
    pelvis_height = 0.0

    bones_by_name = {b.name: b for b in actor.armature.bones}
    semantics = map_skeleton_semantics(list(bones_by_name))

    def _dist(a, b):
        return (sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5) * unit_scale

    def _bone(key):
        name = semantics.get(key)
        return bones_by_name.get(name) if name else None

    head_bone = _bone("head")
    pelvis_bone = _bone("pelvis") or _bone("root")
    l_hand = _bone("left_hand")
    l_foot = _bone("left_foot")

    if head_bone and pelvis_bone:
        torso_len = _dist(pelvis_bone.world_head, head_bone.world_head)
        if height > 0:
            head_torso_ratio = torso_len / height
        pelvis_height = pelvis_bone.world_head[2] * unit_scale

    if l_hand and pelvis_bone:
        arm_length = _dist(pelvis_bone.world_head, l_hand.world_head)
    if l_foot and pelvis_bone:
        leg_length = _dist(pelvis_bone.world_head, l_foot.world_head)

    return {
        "height": round(height, 4),
        "vertical_extent": round(dz, 4),
        "shoulder_width": round(shoulder_width, 4),
        "depth": round(depth, 4),
        "arm_length": round(arm_length, 4),
        "leg_length": round(leg_length, 4),
        "head_torso_ratio": round(head_torso_ratio, 4),
        "bbox_volume": round(volume, 6),
        "pelvis_height": round(pelvis_height, 4),
        "raw_bbox_size": [round(raw_dx, 4), round(raw_dy, 4), round(raw_dz, 4)],
        "unit_scale": unit_scale,
    }
