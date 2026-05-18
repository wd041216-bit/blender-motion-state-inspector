from __future__ import annotations

from analyzer.loader import Actor


PROP_NAME_HINTS = (
    "floor",
    "ground",
    "wall",
    "waypoint",
    "marker",
    "path",
    "navigation",
    "camera",
    "light",
    "helper",
    "proxy",
    "plane",
)


def classify_actor(actor: Actor) -> dict:
    name = actor.name.lower()
    has_rig = actor.mesh.has_armature_modifier and actor.armature.bone_count >= 12
    has_skinning = actor.mesh.vertex_groups_count >= 8
    is_named_prop = any(hint in name for hint in PROP_NAME_HINTS)

    if has_rig and has_skinning:
        cls = "character"
        confidence = 0.95
        reason = "mesh has an armature modifier, many bones, and skinning vertex groups"
    elif is_named_prop:
        cls = "scene_prop"
        confidence = 0.85
        reason = "name matches common scene helper/prop hints"
    elif actor.armature.bone_count > 0:
        cls = "rigged_object"
        confidence = 0.65
        reason = "object has armature data but weak character skinning evidence"
    else:
        cls = "static_mesh"
        confidence = 0.65
        reason = "mesh has no character armature"

    return {
        "class": cls,
        "confidence": confidence,
        "reason": reason,
        "is_character": cls == "character",
    }
