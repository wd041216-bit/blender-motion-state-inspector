import pytest
from analyzer.spatial import calculate_spatial_summary
from analyzer.loader import SceneState, SceneMeta, Actor, MeshData, ArmatureData, PoseData, SpatialData, CameraData

ACTOR_A = Actor(name="A", type="MESH", visible=True, world_matrix=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],
    mesh=MeshData(vertex_count=0, face_count=0, edge_count=0, bbox_min=[0,0,0], bbox_max=[1,1,1], materials=[], has_armature_modifier=False, armature_name=None, vertex_groups_count=0),
    armature=ArmatureData(bone_count=0, bones=[]), pose=PoseData(pose_bones=[]))

ACTOR_B = Actor(name="B", type="MESH", visible=True, world_matrix=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[2,0,0,1]],
    mesh=MeshData(vertex_count=0, face_count=0, edge_count=0, bbox_min=[2,0,0], bbox_max=[3,1,1], materials=[], has_armature_modifier=False, armature_name=None, vertex_groups_count=0),
    armature=ArmatureData(bone_count=0, bones=[]), pose=PoseData(pose_bones=[]))

SCENE = SceneState(
    meta=SceneMeta(blender_version="4.2.0", scene_name="test", current_frame=1, fps=24, frame_start=1, frame_end=250, render_engine="CYCLES"),
    actors=[ACTOR_A, ACTOR_B],
    spatial=SpatialData(camera=CameraData(name="Cam", location=[5,-5,3], rotation_euler=[1.1,0,0.785], focal_length=50), actor_distances=[])
)

def test_distance_between_actors():
    summary = calculate_spatial_summary(SCENE)
    assert summary["actor_distances"][0]["distance"] == pytest.approx(2.0, abs=0.01)

def test_camera_info():
    summary = calculate_spatial_summary(SCENE)
    assert summary["camera"]["name"] == "Cam"
