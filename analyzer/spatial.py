import math
from analyzer.loader import SceneState
from typing import Any, Dict, List

def _bbox_center(actor):
    bmin = actor.mesh.bbox_world_min or actor.mesh.bbox_min
    bmax = actor.mesh.bbox_world_max or actor.mesh.bbox_max
    return [(a + b) / 2 for a, b in zip(bmin, bmax)]

def _dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

def calculate_spatial_summary(scene: SceneState) -> Dict:
    centers = {a.name: _bbox_center(a) for a in scene.actors}
    bounds = {}
    for actor in scene.actors:
        bmin = actor.mesh.bbox_world_min or actor.mesh.bbox_min
        bmax = actor.mesh.bbox_world_max or actor.mesh.bbox_max
        bounds[actor.name] = {
            "center": [round((a + b) / 2, 4) for a, b in zip(bmin, bmax)],
            "size": [round(abs(b - a), 4) for a, b in zip(bmin, bmax)],
        }
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
        "actor_bounds": bounds,
    }


TRANSLATION_LOCK_SCHEMA = "motion_state_translation_locks.v1"


def _number(value: float, digits: int = 5) -> float:
    return round(float(value), digits)


def _summarize(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "mean": None, "max": None}
    return {
        "count": len(values),
        "mean": _number(sum(values) / len(values)),
        "max": _number(max(values)),
    }


def _frame_reports(report: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(report.get("frame_reports"), list):
        return [frame for frame in report["frame_reports"] if isinstance(frame, dict)]
    return [report]


def _bounds(report_frame: dict[str, Any]) -> dict[str, Any]:
    return report_frame.get("spatial", {}).get("actor_bounds", {}) or {}


def _match_actor_name(bounds: dict[str, Any], token: str) -> str | None:
    lowered = token.lower()
    exact = [name for name in bounds if name.lower() == lowered]
    if exact:
        return sorted(exact)[0]
    partial = [name for name in bounds if lowered in name.lower()]
    if partial:
        return sorted(partial, key=lambda name: (len(name), name))[0]
    return None


def _parse_pair_spec(pair_spec: str) -> tuple[str, str]:
    if "=" not in pair_spec:
        raise ValueError(f"Translation lock pair must use control=experiment format: {pair_spec!r}")
    left, right = pair_spec.split("=", 1)
    left = left.strip()
    right = right.strip()
    if not left or not right:
        raise ValueError(f"Translation lock pair must name both actors: {pair_spec!r}")
    return left, right


def _center(bounds: dict[str, Any], name: str) -> list[float] | None:
    value = bounds.get(name, {}).get("center")
    if isinstance(value, list) and len(value) >= 3:
        return [float(value[0]), float(value[1]), float(value[2])]
    return None


def _vector_delta(a: list[float], b: list[float]) -> list[float]:
    return [a[index] - b[index] for index in range(3)]


def _distance(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values))


def evaluate_translation_locks(
    report: dict[str, Any],
    pair_specs: list[str],
    tolerance: float = 0.03,
) -> dict[str, Any]:
    """Verify experiment actors remain pure translations of their control actors."""
    frames = _frame_reports(report)
    pairs = []
    for pair_spec in pair_specs:
        control_token, experiment_token = _parse_pair_spec(pair_spec)
        samples = []
        missing = []
        baseline_translation = None
        drifts = []
        for frame in frames:
            frame_number = frame.get("frame_info", {}).get("current")
            bounds = _bounds(frame)
            control_name = _match_actor_name(bounds, control_token)
            experiment_name = _match_actor_name(bounds, experiment_token)
            if not control_name or not experiment_name:
                missing.append(
                    {
                        "frame": frame_number,
                        "control": control_token if not control_name else control_name,
                        "experiment": experiment_token if not experiment_name else experiment_name,
                    }
                )
                continue
            control_center = _center(bounds, control_name)
            experiment_center = _center(bounds, experiment_name)
            if control_center is None or experiment_center is None:
                missing.append({"frame": frame_number, "control": control_name, "experiment": experiment_name})
                continue
            translation = _vector_delta(experiment_center, control_center)
            if baseline_translation is None:
                baseline_translation = translation
            drift_vector = _vector_delta(translation, baseline_translation)
            drift = _distance(drift_vector)
            drifts.append(drift)
            samples.append(
                {
                    "frame": frame_number,
                    "control": control_name,
                    "experiment": experiment_name,
                    "translation": [_number(value) for value in translation],
                    "drift_m": _number(drift),
                }
            )
        drift_summary = _summarize(drifts)
        pair_verdict = (
            "pass"
            if samples
            and not missing
            and drift_summary["max"] is not None
            and drift_summary["max"] <= tolerance
            else "fail"
        )
        pairs.append(
            {
                "pair": pair_spec,
                "control_token": control_token,
                "experiment_token": experiment_token,
                "baseline_translation": [_number(value) for value in baseline_translation] if baseline_translation else None,
                "tolerance_m": tolerance,
                "drift_m": drift_summary,
                "sample_count": len(samples),
                "missing": missing,
                "samples": samples[:24],
                "verdict": pair_verdict,
            }
        )
    return {
        "schema": TRANSLATION_LOCK_SCHEMA,
        "principle": "experiment_center(frame) must equal control_center(frame) plus one constant translation vector",
        "verdict": "pass" if pairs and all(pair["verdict"] == "pass" for pair in pairs) else "fail",
        "pairs": pairs,
    }
