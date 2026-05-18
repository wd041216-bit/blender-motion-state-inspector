from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class SceneMeta:
    blender_version: str
    scene_name: str
    current_frame: int
    fps: int
    frame_start: int
    frame_end: int
    render_engine: str

@dataclass
class MeshData:
    vertex_count: int
    face_count: int
    edge_count: int
    bbox_min: List[float]
    bbox_max: List[float]
    materials: List[str]
    has_armature_modifier: bool
    armature_name: Optional[str]
    vertex_groups_count: int
    bbox_world_min: Optional[List[float]] = None
    bbox_world_max: Optional[List[float]] = None
    dimensions: Optional[List[float]] = None

@dataclass
class BoneData:
    name: str
    parent: Optional[str]
    head: List[float]
    tail: List[float]
    world_head: List[float]
    world_tail: List[float]
    local_rotation_euler: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    world_rotation_quaternion: List[float] = field(default_factory=lambda: [1.0, 0.0, 0.0, 0.0])
    length: float = 0.0
    is_deform: bool = True
    constraints: List[dict] = field(default_factory=list)

@dataclass
class ArmatureData:
    bone_count: int
    bones: List[BoneData]

@dataclass
class PoseBoneData:
    name: str
    location: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    rotation_quaternion: List[float] = field(default_factory=lambda: [1.0, 0.0, 0.0, 0.0])
    scale: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    world_matrix: Optional[List[List[float]]] = None

@dataclass
class PoseData:
    pose_bones: List[PoseBoneData]

@dataclass
class Actor:
    name: str
    type: str
    visible: bool
    world_matrix: List[List[float]]
    mesh: MeshData
    armature: ArmatureData
    pose: PoseData

@dataclass
class CameraData:
    name: str
    location: List[float]
    rotation_euler: List[float]
    focal_length: float

@dataclass
class ActorDistance:
    from_actor: str
    to_actor: str
    distance: float

@dataclass
class SpatialData:
    camera: CameraData
    actor_distances: List[ActorDistance]

@dataclass
class SceneState:
    meta: SceneMeta
    actors: List[Actor]
    spatial: SpatialData

def _load_mesh(data: dict) -> MeshData:
    return MeshData(
        vertex_count=data.get("vertex_count", 0),
        face_count=data.get("face_count", 0),
        edge_count=data.get("edge_count", 0),
        bbox_min=data.get("bbox_min", [0.0, 0.0, 0.0]),
        bbox_max=data.get("bbox_max", [0.0, 0.0, 0.0]),
        bbox_world_min=data.get("bbox_world_min"),
        bbox_world_max=data.get("bbox_world_max"),
        dimensions=data.get("dimensions"),
        materials=data.get("materials", []),
        has_armature_modifier=data.get("has_armature_modifier", False),
        armature_name=data.get("armature_name"),
        vertex_groups_count=data.get("vertex_groups_count", 0),
    )

def _load_bone(data: dict) -> BoneData:
    return BoneData(
        name=data["name"],
        parent=data.get("parent"),
        head=data["head"],
        tail=data["tail"],
        world_head=data.get("world_head", data["head"]),
        world_tail=data.get("world_tail", data["tail"]),
        local_rotation_euler=data.get("local_rotation_euler", [0.0, 0.0, 0.0]),
        world_rotation_quaternion=data.get("world_rotation_quaternion", [1.0, 0.0, 0.0, 0.0]),
        length=data.get("length", 0.0),
        is_deform=data.get("is_deform", True),
        constraints=data.get("constraints", []),
    )

def _load_actor(data: dict) -> Actor:
    mesh_data = _load_mesh(data["mesh"])
    arm_data = ArmatureData(
        bone_count=data["armature"]["bone_count"],
        bones=[_load_bone(b) for b in data["armature"]["bones"]],
    )
    pose_bones = [PoseBoneData(**pb) for pb in data["pose"].get("pose_bones", [])]
    pose_data = PoseData(pose_bones=pose_bones)
    return Actor(
        name=data["name"],
        type=data["type"],
        visible=data["visible"],
        world_matrix=data["world_matrix"],
        mesh=mesh_data,
        armature=arm_data,
        pose=pose_data,
    )

def load_raw_state(source: str | dict) -> SceneState:
    if isinstance(source, str):
        with open(source, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = source
    meta = SceneMeta(**data["meta"])
    actors = [_load_actor(a) for a in data["actors"]]
    actor_distances = []
    for ad in data["spatial"].get("actor_distances", []):
        actor_distances.append(ActorDistance(
            from_actor=ad.get("from_actor", ad.get("from", "")),
            to_actor=ad.get("to_actor", ad.get("to", "")),
            distance=ad.get("distance", 0.0),
        ))
    spatial = SpatialData(
        camera=CameraData(**data["spatial"]["camera"]),
        actor_distances=actor_distances,
    )
    return SceneState(meta=meta, actors=actors, spatial=spatial)
