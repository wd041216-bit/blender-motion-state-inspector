from typing import Dict, List

def detect_anomalies(
    joint_angles: Dict[str, float],
    bbox_aspect_yx: float,
    bbox_aspect_yz: float,
    foot_ground_clearance: float,
    is_jumping: bool,
) -> List[Dict]:
    anomalies = []
    for joint_name, angle in joint_angles.items():
        if angle < -10 or angle > 185:
            joint_type = "elbow" if "elbow" in joint_name.lower() else "knee" if "knee" in joint_name.lower() else "joint"
            anomalies.append({
                "type": f"{joint_type}_inversion",
                "joint": joint_name,
                "angle": angle,
                "message": f"{joint_name} 角度异常: {angle}°",
            })
    if bbox_aspect_yx < 0.3 or bbox_aspect_yz < 0.3:
        anomalies.append({
            "type": "squashed",
            "message": "模型 bbox 高度方向异常压缩",
        })
    if not is_jumping and foot_ground_clearance > 0.15:
        anomalies.append({
            "type": "floating",
            "clearance": foot_ground_clearance,
            "message": f"脚部离地 {foot_ground_clearance:.3f}m (非跳跃状态)",
        })
    if not is_jumping and foot_ground_clearance < -0.03:
        anomalies.append({
            "type": "ground_penetration",
            "clearance": foot_ground_clearance,
            "message": f"脚部穿入地面 {abs(foot_ground_clearance):.3f}m",
        })
    return anomalies
