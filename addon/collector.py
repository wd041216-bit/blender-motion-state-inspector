import json
import tempfile
from pathlib import Path
import bpy
from addon.utils import ensure_object_mode, get_evaluated_mesh


def collect_scene(target="all", simplified=False):
    ensure_object_mode()
    scene = bpy.context.scene
    actors = []
    for obj in scene.objects:
        if obj.type != "MESH":
            continue
        if target == "selected" and not obj.select_get():
            continue
        mesh_data = _collect_mesh(obj, simplified)
        arm_data = _collect_armature(obj)
        pose_data = _collect_pose(obj)
        actors.append({
            "name": obj.name,
            "type": obj.type,
            "visible": obj.visible_get(),
            "world_matrix": [list(row) for row in obj.matrix_world],
            "mesh": mesh_data,
            "armature": arm_data,
            "pose": pose_data,
        })
    spatial = _collect_spatial(scene)
    raw = {
        "meta": {
            "blender_version": ".".join(str(x) for x in bpy.app.version),
            "scene_name": scene.name,
            "current_frame": scene.frame_current,
            "fps": scene.render.fps,
            "frame_start": scene.frame_start,
            "frame_end": scene.frame_end,
            "render_engine": scene.render.engine,
        },
        "actors": actors,
        "spatial": spatial,
    }
    return raw


def _collect_mesh(obj, simplified):
    mesh = obj.data
    has_arm = any(m.type == "ARMATURE" for m in obj.modifiers)
    arm_name = None
    for m in obj.modifiers:
        if m.type == "ARMATURE" and m.object:
            arm_name = m.object.name
            break
    result = {
        "vertex_count": len(mesh.vertices),
        "face_count": len(mesh.polygons),
        "edge_count": len(mesh.edges),
        "bbox_min": list(obj.bound_box[0]),
        "bbox_max": list(obj.bound_box[6]),
        "materials": [mat.name for mat in mesh.materials if mat],
        "has_armature_modifier": has_arm,
        "armature_name": arm_name,
        "vertex_groups_count": len(obj.vertex_groups),
    }
    if not simplified:
        eval_mesh = get_evaluated_mesh(obj)
        verts = [list(v.co) for v in eval_mesh.vertices]
        result["vertices"] = verts
        obj.to_mesh_clear()
    return result


def _collect_armature(obj):
    arm_obj = None
    for m in obj.modifiers:
        if m.type == "ARMATURE" and m.object:
            arm_obj = m.object
            break
    if not arm_obj or arm_obj.type != "ARMATURE":
        return {"bone_count": 0, "bones": []}
    arm = arm_obj.data
    bones = []
    for bone in arm.bones:
        pose_bone = arm_obj.pose.bones.get(bone.name)
        pb_data = {}
        if pose_bone:
            pb_data = {
                "location": list(pose_bone.location),
                "rotation_quaternion": list(pose_bone.rotation_quaternion),
                "scale": list(pose_bone.scale),
                "world_matrix": [list(row) for row in pose_bone.matrix],
            }
        bones.append({
            "name": bone.name,
            "parent": bone.parent.name if bone.parent else None,
            "head": list(bone.head_local),
            "tail": list(bone.tail_local),
            "world_head": list(pose_bone.head) if pose_bone else list(bone.head_local),
            "world_tail": list(pose_bone.tail) if pose_bone else list(bone.tail_local),
            "local_rotation_euler": list(bone.matrix_local.to_euler()),
            "world_rotation_quaternion": list(pose_bone.rotation_quaternion) if pose_bone else [1, 0, 0, 0],
            "length": bone.length,
            "is_deform": bone.use_deform,
            "constraints": [c.name for c in (pose_bone.constraints if pose_bone else [])],
            "pose": pb_data,
        })
    return {"bone_count": len(bones), "bones": bones}


def _collect_pose(obj):
    arm_obj = None
    for m in obj.modifiers:
        if m.type == "ARMATURE" and m.object:
            arm_obj = m.object
            break
    if not arm_obj:
        return {"pose_bones": []}
    pose_bones = []
    for pb in arm_obj.pose.bones:
        pose_bones.append({
            "name": pb.name,
            "location": list(pb.location),
            "rotation_quaternion": list(pb.rotation_quaternion),
            "scale": list(pb.scale),
            "world_matrix": [list(row) for row in pb.matrix],
        })
    return {"pose_bones": pose_bones}


def _collect_spatial(scene):
    cam = scene.camera
    cam_data = None
    if cam:
        cam_data = {
            "name": cam.name,
            "location": list(cam.location),
            "rotation_euler": list(cam.rotation_euler),
            "focal_length": cam.data.lens if cam.data else 50,
        }
    distances = []
    meshes = [o for o in scene.objects if o.type == "MESH"]
    for i in range(len(meshes)):
        for j in range(i + 1, len(meshes)):
            d = (meshes[i].location - meshes[j].location).length
            distances.append({
                "from": meshes[i].name,
                "to": meshes[j].name,
                "distance": round(d, 4),
            })
    return {
        "camera": cam_data or {"name": "", "location": [0, 0, 0], "rotation_euler": [0, 0, 0], "focal_length": 50},
        "actor_distances": distances,
    }


def write_raw_state(raw, path=None):
    if path is None:
        fd, path = tempfile.mkstemp(suffix="_raw_state.json", prefix="bmsi_")
        with open(fd, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=2)
    else:
        Path(path).write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
