from typing import Literal

PoseState = Literal["站立", "倒立", "弯腰", "蜷缩", "伸展"]

def classify_pose(pelvis_pitch: float, spine_bend: float, limb_extension: float) -> PoseState:
    if pelvis_pitch > 80:
        return "倒立"
    if spine_bend > 45:
        return "弯腰"
    if limb_extension < 0.3:
        return "蜷缩"
    if limb_extension > 0.8 and spine_bend < 10:
        return "伸展"
    return "站立"
