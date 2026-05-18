from typing import Dict, List

def detect_contacts(bones: List[Dict], ground_y: float = 0.0, threshold: float = 0.05) -> List[Dict]:
    contacts = []
    for bone in bones:
        name = bone["name"].lower()
        if "foot" in name or "toe" in name or "hand" in name:
            endpoints = [bone.get("world_head", [0,0,0]), bone.get("world_tail", [0,0,0])]
            for pt in endpoints:
                if abs(pt[2] - ground_y) <= threshold:
                    contacts.append({
                        "type": "ground",
                        "bone": bone["name"],
                        "point": pt,
                    })
                    break
    return contacts
