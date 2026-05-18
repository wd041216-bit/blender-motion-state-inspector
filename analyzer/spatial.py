import math
from analyzer.loader import SceneState
from typing import Dict, List

def _bbox_center(actor):
    bmin = actor.mesh.bbox_world_min or actor.mesh.bbox_min
    bmax = actor.mesh.bbox_world_max or actor.mesh.bbox_max
    return [(a + b) / 2 for a, b in zip(bmin, bmax)]

def _dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

def calculate_spatial_summary(scene: SceneState) -> Dict:
    centers = {a.name: _bbox_center(a) for a in scene.actors}
    distances = []
    names = list(centers.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            d = _dist(centers[names[i]], centers[names[j]])
            distances.append({
                "from_actor": names[i],
                "to_actor": names[j],
                "distance": round(d, 4),
            })
    cam = scene.spatial.camera
    return {
        "camera": {
            "name": cam.name,
            "location": cam.location,
            "rotation_euler": cam.rotation_euler,
            "focal_length": cam.focal_length,
        },
        "actor_distances": distances,
    }
