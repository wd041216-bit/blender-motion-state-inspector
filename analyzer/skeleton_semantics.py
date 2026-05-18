import re
from typing import Dict, List, Optional

SEMANTIC_PATTERNS = {
    "root": [r"^root$", r"^hips$", r"^pelvis$"],
    "pelvis": [r"^pelvis$", r"^hips$"],
    "spine": [r"^spine$", r"^spine_?\d*$", r"^torso$"],
    "chest": [r"^chest$", r"^upper_?chest$", r"^thorax$", r"^spine2$", r"^spine_?2$"],
    "neck": [r"^neck$", r"^neck_?\d*$"],
    "head": [r"^head$", r"^head_top$", r"^headtop_end$", r"^skull$"],
    "left_shoulder": [r"^shoulder\.l$", r"^leftshoulder$", r"^left_shoulder$"],
    "right_shoulder": [r"^shoulder\.r$", r"^rightshoulder$", r"^right_shoulder$"],
    "left_arm": [r"^arm\.l$", r"^leftarm$", r"^left_arm$", r"^upperarm\.l$", r"^upper_arm\.l$"],
    "right_arm": [r"^arm\.r$", r"^rightarm$", r"^right_arm$", r"^upperarm\.r$", r"^upper_arm\.r$"],
    "left_forearm": [r"^forearm\.l$", r"^leftforearm$", r"^left_forearm$", r"^lowerarm\.l$"],
    "right_forearm": [r"^forearm\.r$", r"^rightforearm$", r"^right_forearm$", r"^lowerarm\.r$"],
    "left_hand": [r"^hand\.l$", r"^lefthand$", r"^left_hand$", r"^wrist\.l$"],
    "right_hand": [r"^hand\.r$", r"^righthand$", r"^right_hand$", r"^wrist\.r$"],
    "left_thigh": [r"^thigh\.l$", r"^leftupleg$", r"^upperleg\.l$", r"^left_upperleg$"],
    "right_thigh": [r"^thigh\.r$", r"^rightupleg$", r"^upperleg\.r$", r"^right_upperleg$"],
    "left_shin": [r"^shin\.l$", r"^leftleg$", r"^calf\.l$", r"^lowerleg\.l$"],
    "right_shin": [r"^shin\.r$", r"^rightleg$", r"^calf\.r$", r"^lowerleg\.r$"],
    "left_foot": [r"^foot\.l$", r"^leftfoot$", r"^left_foot$"],
    "right_foot": [r"^foot\.r$", r"^rightfoot$", r"^right_foot$"],
    "left_toe": [r"^toe\.l$", r"^toes\.l$", r"^lefttoebase$", r"^lefttoe_end$"],
    "right_toe": [r"^toe\.r$", r"^toes\.r$", r"^righttoebase$", r"^righttoe_end$"],
}

def normalize_bone_name(bone_name: str) -> str:
    name = bone_name.split(":")[-1].strip()
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    name = name.replace("-", "_").replace(" ", "_")
    name = re.sub(r"_+", "_", name).strip("_").lower()
    name = re.sub(r"_l$", ".l", name)
    name = re.sub(r"_r$", ".r", name)
    # Keep Mixamo's LeftFoot/RightFoot style easy to match as well.
    return name.replace("_", "")

def _match_bone(bone_name: str, patterns: List[str]) -> bool:
    lowered = normalize_bone_name(bone_name)
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
    return mapping
