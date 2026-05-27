import re
from typing import Dict, List, Optional

SEMANTIC_PATTERNS = {
    "root": [r"^root$", r"^hips$", r"^pelvis$", r"^下半身$"],
    "pelvis": [r"^pelvis$", r"^hips$", r"^下半身$"],
    "spine": [r"^spine$", r"^spine_?\d*$", r"^torso$", r"^上半身$", r"^上半身1$", r"^上半身2$"],
    "chest": [r"^chest$", r"^upper_?chest$", r"^thorax$", r"^spine2$", r"^spine_?2$", r"^m上半身$", r"^m-上半身$"],
    "neck": [r"^neck$", r"^neck_?\d*$", r"^首$"],
    "head": [r"^head$", r"^head_top$", r"^headtop_end$", r"^skull$", r"^頭$"],
    "left_shoulder": [r"^shoulder\.l$", r"^leftshoulder$", r"^left_shoulder$", r"^左肩$"],
    "right_shoulder": [r"^shoulder\.r$", r"^rightshoulder$", r"^right_shoulder$", r"^右肩$"],
    "left_arm": [r"^arm\.l$", r"^leftarm$", r"^left_arm$", r"^upperarm\.l$", r"^upper_arm\.l$", r"^leftupperarm$", r"^左腕$"],
    "right_arm": [r"^arm\.r$", r"^rightarm$", r"^right_arm$", r"^upperarm\.r$", r"^upper_arm\.r$", r"^rightupperarm$", r"^右腕$"],
    "left_forearm": [r"^forearm\.l$", r"^leftforearm$", r"^left_forearm$", r"^lowerarm\.l$", r"^leftlowerarm$", r"^左ひじ$"],
    "right_forearm": [r"^forearm\.r$", r"^rightforearm$", r"^right_forearm$", r"^lowerarm\.r$", r"^rightlowerarm$", r"^右ひじ$"],
    "left_hand": [r"^hand\.l$", r"^lefthand$", r"^left_hand$", r"^wrist\.l$", r"^左手首$"],
    "right_hand": [r"^hand\.r$", r"^righthand$", r"^right_hand$", r"^wrist\.r$", r"^右手首$"],
    "left_thigh": [r"^thigh\.l$", r"^leftupleg$", r"^upperleg\.l$", r"^left_upperleg$", r"^leftupperleg$", r"^左足$", r"^足\.l$"],
    "right_thigh": [r"^thigh\.r$", r"^rightupleg$", r"^upperleg\.r$", r"^right_upperleg$", r"^rightupperleg$", r"^右足$", r"^足\.r$"],
    "left_shin": [r"^shin\.l$", r"^leftleg$", r"^calf\.l$", r"^lowerleg\.l$", r"^leftlowerleg$", r"^左ひざ$", r"^ひざ\.l$"],
    "right_shin": [r"^shin\.r$", r"^rightleg$", r"^calf\.r$", r"^lowerleg\.r$", r"^rightlowerleg$", r"^右ひざ$", r"^ひざ\.r$"],
    "left_foot": [r"^foot\.l$", r"^leftfoot$", r"^left_foot$", r"^左足首$", r"^足首\.l$"],
    "right_foot": [r"^foot\.r$", r"^rightfoot$", r"^right_foot$", r"^右足首$", r"^足首\.r$"],
    "left_toe": [r"^toe\.l$", r"^toes\.l$", r"^lefttoebase$", r"^lefttoe_end$", r"^lefttoes$"],
    "right_toe": [r"^toe\.r$", r"^toes\.r$", r"^righttoebase$", r"^righttoe_end$", r"^righttoes$"],
}

def normalize_bone_name(bone_name: str) -> str:
    name = bone_name.split(":")[-1].strip()
    name = re.sub(r"^\d+[_\-. ]+", "", name)
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
