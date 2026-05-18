from analyzer.loader import Actor
from typing import Dict

def calculate_morphology(actor: Actor) -> Dict[str, float]:
    bbox = actor.mesh
    dx = bbox.bbox_max[0] - bbox.bbox_min[0]
    dy = bbox.bbox_max[1] - bbox.bbox_min[1]
    dz = bbox.bbox_max[2] - bbox.bbox_min[2]
    height = dz
    shoulder_width = dx
    depth = dy
    volume = dx * dy * dz

    arm_length = 0.0
    leg_length = 0.0
    head_torso_ratio = 0.0
    pelvis_height = 0.0

    bones_by_name = {b.name.lower(): b for b in actor.armature.bones}

    def _dist(a, b):
        return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5

    head_bone = bones_by_name.get("head") or bones_by_name.get("head_top")
    pelvis_bone = bones_by_name.get("pelvis") or bones_by_name.get("hips") or bones_by_name.get("root")
    l_hand = bones_by_name.get("hand.l") or bones_by_name.get("left_hand") or bones_by_name.get("hand_l")
    r_hand = bones_by_name.get("hand.r") or bones_by_name.get("right_hand") or bones_by_name.get("hand_r")
    l_foot = bones_by_name.get("foot.l") or bones_by_name.get("left_foot") or bones_by_name.get("foot_l")
    r_foot = bones_by_name.get("foot.r") or bones_by_name.get("right_foot") or bones_by_name.get("foot_r")

    if head_bone and pelvis_bone:
        torso_len = _dist(pelvis_bone.world_head, head_bone.world_head)
        if height > 0:
            head_torso_ratio = torso_len / height
        pelvis_height = pelvis_bone.world_head[2]

    if l_hand and pelvis_bone:
        arm_length = _dist(pelvis_bone.world_head, l_hand.world_head)
    if l_foot and pelvis_bone:
        leg_length = _dist(pelvis_bone.world_head, l_foot.world_head)

    return {
        "height": round(height, 4),
        "shoulder_width": round(shoulder_width, 4),
        "arm_length": round(arm_length, 4),
        "leg_length": round(leg_length, 4),
        "head_torso_ratio": round(head_torso_ratio, 4),
        "bbox_volume": round(volume, 6),
        "pelvis_height": round(pelvis_height, 4),
    }
