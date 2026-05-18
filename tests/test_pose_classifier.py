import pytest
from analyzer.pose_classifier import classify_pose

def test_standing():
    # limb_extension=0.6 avoids "伸展" threshold (>0.8)
    assert classify_pose(pelvis_pitch=0, spine_bend=5, limb_extension=0.6) == "站立"

def test_inverted():
    assert classify_pose(pelvis_pitch=85, spine_bend=5, limb_extension=0.5) == "倒立"

def test_bent():
    assert classify_pose(pelvis_pitch=10, spine_bend=50, limb_extension=0.7) == "弯腰"

def test_curled():
    assert classify_pose(pelvis_pitch=0, spine_bend=10, limb_extension=0.2) == "蜷缩"

def test_extended():
    assert classify_pose(pelvis_pitch=0, spine_bend=5, limb_extension=0.9) == "伸展"
