import pytest
from analyzer.anomaly_detector import detect_anomalies

def test_no_anomalies():
    result = detect_anomalies(
        joint_angles={"left_elbow": 15, "right_knee": 170},
        bbox_aspect_yx=1.8,
        bbox_aspect_yz=1.8,
        foot_ground_clearance=0.0,
        is_jumping=False,
    )
    assert result == []

def test_knee_inversion():
    result = detect_anomalies(
        joint_angles={"right_knee": 190},
        bbox_aspect_yx=1.8,
        bbox_aspect_yz=1.8,
        foot_ground_clearance=0.0,
        is_jumping=False,
    )
    assert any(a["type"] == "knee_inversion" for a in result)

def test_floating():
    result = detect_anomalies(
        joint_angles={},
        bbox_aspect_yx=1.8,
        bbox_aspect_yz=1.8,
        foot_ground_clearance=0.2,
        is_jumping=False,
    )
    assert any(a["type"] == "floating" for a in result)
