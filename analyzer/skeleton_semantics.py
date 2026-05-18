import re
from typing import Dict, List, Optional

SEMANTIC_PATTERNS = {
    "root": [r"^root$", r"^hips$", r"^pelvis$"],
    "pelvis": [r"^pelvis$", r"^hips$"],
    "spine": [r"^spine$", r"^spine_?\d*$", r"^torso$"],
    "chest": [r"^chest$", r"^upper_?chest$", r"^thorax$"],
    "neck": [r"^neck$", r"^neck_?\d*$"],
    "head": [r"^head$", r"^head_top$", r"^skull$"],
    "left_arm": [r"^arm[_\.]l$", r"^left[_\s]?arm$", r"^upperarm[_\.]l$", r"^upper_arm[_\.]l$"],
    "right_arm": [r"^arm[_\.]r$", r"^right[_\s]?arm$", r"^upperarm[_\.]r$", r"^upper_arm[_\.]r$"],
    "left_forearm": [r"^forearm[_\.]l$", r"^lowerarm[_\.]l$"],
    "right_forearm": [r"^forearm[_\.]r$", r"^lowerarm[_\.]r$"],
    "left_hand": [r"^hand[_\.]l$", r"^left[_\s]?hand$", r"^wrist[_\.]l$"],
    "right_hand": [r"^hand[_\.]r$", r"^right[_\s]?hand$", r"^wrist[_\.]r$"],
    "left_thigh": [r"^thigh[_\.]l$", r"^upperleg[_\.]l$", r"^left[_\s]?leg$", r"^leg[_\.]l$"],
    "right_thigh": [r"^thigh[_\.]r$", r"^upperleg[_\.]r$", r"^right[_\s]?leg$", r"^leg[_\.]r$"],
    "left_shin": [r"^shin[_\.]l$", r"^calf[_\.]l$", r"^lowerleg[_\.]l$"],
    "right_shin": [r"^shin[_\.]r$", r"^calf[_\.]r$", r"^lowerleg[_\.]r$"],
    "left_foot": [r"^foot[_\.]l$", r"^left[_\s]?foot$"],
    "right_foot": [r"^foot[_\.]r$", r"^right[_\s]?foot$"],
    "left_toe": [r"^toe[_\.]l$", r"^toes[_\.]l$"],
    "right_toe": [r"^toe[_\.]r$", r"^toes[_\.]r$"],
}

def _match_bone(bone_name: str, patterns: List[str]) -> bool:
    lowered = bone_name.lower()
    for pat in patterns:
        if re.search(pat, lowered):
            return True
    return False

def map_skeleton_semantics(bone_names: List[str]) -> Dict[str, Optional[str]]:
    mapping: Dict[str, Optional[str]] = {key: None for key in SEMANTIC_PATTERNS}
    for bname in bone_names:
        for sem_key, patterns in SEMANTIC_PATTERNS.items():
            if mapping[sem_key] is None and _match_bone(bname, patterns):
                mapping[sem_key] = bname
                break
    return mapping
