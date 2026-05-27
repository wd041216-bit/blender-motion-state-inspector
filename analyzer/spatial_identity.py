from __future__ import annotations

import math
from typing import Any


SPATIAL_IDENTITY_GROUP_SCHEMA = "motion_state_spatial_identity_groups.v1"
AXES = ("x", "y", "z")
AXIS_INDEX = {"x": 0, "y": 1, "z": 2}


def _number(value: float, digits: int = 5) -> float:
    return round(float(value), digits)


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


def _parse_group_spec(group_spec: str) -> tuple[list[str], list[str]]:
    if "=" not in group_spec:
        raise ValueError(f"Spatial identity group must use controls=experiments format: {group_spec!r}")
    left, right = group_spec.split("=", 1)
    controls = [item.strip() for item in left.split(",") if item.strip()]
    experiments = [item.strip() for item in right.split(",") if item.strip()]
    if not controls or not experiments or len(controls) != len(experiments):
        raise ValueError(
            "Spatial identity group must name the same number of control and experiment actor tokens: "
            f"{group_spec!r}"
        )
    if len(controls) < 2:
        raise ValueError(f"Spatial identity group needs at least two actors: {group_spec!r}")
    return controls, experiments


def _center(bounds: dict[str, Any], name: str) -> list[float] | None:
    value = bounds.get(name, {}).get("center")
    if isinstance(value, list) and len(value) >= 3:
        return [float(value[0]), float(value[1]), float(value[2])]
    return None


def _vector(left: list[float], right: list[float]) -> list[float]:
    return [float(right[index]) - float(left[index]) for index in range(3)]


def _length(vector: list[float]) -> float:
    return math.sqrt(sum(float(value) * float(value) for value in vector[:3]))


def _normalize(vector: list[float]) -> list[float] | None:
    length = _length(vector)
    if length < 1e-8:
        return None
    return [float(value) / length for value in vector[:3]]


def _angle_degrees(left: list[float], right: list[float]) -> float | None:
    a = _normalize(left)
    b = _normalize(right)
    if a is None or b is None:
        return None
    dot = max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b))))
    return math.degrees(math.acos(dot))


def _summarize(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "mean": None, "max": None}
    return {"count": len(values), "mean": _number(sum(values) / len(values)), "max": _number(max(values))}


def _sign(value: float, epsilon: float) -> int:
    if value > epsilon:
        return 1
    if value < -epsilon:
        return -1
    return 0


def _pairwise_vectors(points: list[list[float]], axes: tuple[str, ...], sign_epsilon: float) -> dict[str, Any]:
    pairs: dict[str, Any] = {}
    for left in range(len(points)):
        for right in range(left + 1, len(points)):
            vector = _vector(points[left], points[right])
            signs = {axis: _sign(vector[AXIS_INDEX[axis]], sign_epsilon) for axis in axes}
            pairs[f"{left}:{right}"] = {
                "vector": [_number(value) for value in vector],
                "axis_signs": signs,
                "distance_m": _number(_length(vector)),
            }
    return pairs


def _changed_pairs(current: dict[str, Any], baseline: dict[str, Any], axes: tuple[str, ...]) -> list[dict[str, Any]]:
    changes = []
    for pair_key, pair in current.items():
        base = baseline.get(pair_key)
        if not base:
            continue
        changed_axes = []
        for axis in axes:
            base_sign = base["axis_signs"].get(axis, 0)
            current_sign = pair["axis_signs"].get(axis, 0)
            if base_sign and current_sign and current_sign != base_sign:
                changed_axes.append({"axis": axis, "baseline": base_sign, "current": current_sign})
        if changed_axes:
            changes.append({"pair": pair_key, "axes": changed_axes})
    return changes


def _mismatched_pairs(control: dict[str, Any], experiment: dict[str, Any], axes: tuple[str, ...]) -> list[dict[str, Any]]:
    mismatches = []
    for pair_key, control_pair in control.items():
        experiment_pair = experiment.get(pair_key)
        if not experiment_pair:
            continue
        axes_mismatch = []
        for axis in axes:
            control_sign = control_pair["axis_signs"].get(axis, 0)
            experiment_sign = experiment_pair["axis_signs"].get(axis, 0)
            if control_sign and experiment_sign and experiment_sign != control_sign:
                axes_mismatch.append({"axis": axis, "control": control_sign, "experiment": experiment_sign})
        if axes_mismatch:
            angle = _angle_degrees(control_pair["vector"], experiment_pair["vector"])
            mismatches.append(
                {
                    "pair": pair_key,
                    "axes": axes_mismatch,
                    "relative_vector_angle_error_degrees": _number(angle) if angle is not None else None,
                }
            )
    return mismatches


def _vector_drift_pairs(control: dict[str, Any], experiment: dict[str, Any], tolerance: float) -> list[dict[str, Any]]:
    drifts = []
    for pair_key, control_pair in control.items():
        experiment_pair = experiment.get(pair_key)
        if not experiment_pair:
            continue
        delta = _vector(control_pair["vector"], experiment_pair["vector"])
        distance = _length(delta)
        if distance > tolerance:
            drifts.append(
                {
                    "pair": pair_key,
                    "control_vector": control_pair["vector"],
                    "experiment_vector": experiment_pair["vector"],
                    "delta": [_number(value) for value in delta],
                    "delta_m": _number(distance),
                }
            )
    return drifts


def evaluate_spatial_identity_groups(
    report: dict[str, Any],
    group_specs: list[str],
    sign_epsilon: float = 0.05,
    vector_tolerance: float = 0.05,
    axes: tuple[str, ...] = AXES,
) -> dict[str, Any]:
    frames = _frame_reports(report)
    groups = []
    for group_spec in group_specs:
        control_tokens, experiment_tokens = _parse_group_spec(group_spec)
        samples = []
        missing = []
        baseline_control = None
        baseline_experiment = None
        control_change_frames: list[int] = []
        experiment_change_frames: list[int] = []
        mismatch_frames: list[int] = []
        vector_drift_frames: list[int] = []
        vector_drift_values: list[float] = []
        max_angle_errors: list[float] = []

        for frame in frames:
            frame_number = frame.get("frame_info", {}).get("current")
            bounds = _bounds(frame)
            control_names = []
            experiment_names = []
            control_centers = []
            experiment_centers = []
            frame_missing = []
            for control_token, experiment_token in zip(control_tokens, experiment_tokens, strict=True):
                control_name = _match_actor_name(bounds, control_token)
                experiment_name = _match_actor_name(bounds, experiment_token)
                if not control_name or not experiment_name:
                    frame_missing.append(
                        {
                            "control": control_token if not control_name else control_name,
                            "experiment": experiment_token if not experiment_name else experiment_name,
                        }
                    )
                    continue
                control_center = _center(bounds, control_name)
                experiment_center = _center(bounds, experiment_name)
                if control_center is None or experiment_center is None:
                    frame_missing.append({"control": control_name, "experiment": experiment_name})
                    continue
                control_names.append(control_name)
                experiment_names.append(experiment_name)
                control_centers.append(control_center)
                experiment_centers.append(experiment_center)
            if frame_missing:
                missing.append({"frame": frame_number, "members": frame_missing})
                continue

            control_pairs = _pairwise_vectors(control_centers, axes, sign_epsilon)
            experiment_pairs = _pairwise_vectors(experiment_centers, axes, sign_epsilon)
            if baseline_control is None:
                baseline_control = control_pairs
            if baseline_experiment is None:
                baseline_experiment = experiment_pairs

            control_changes = _changed_pairs(control_pairs, baseline_control, axes)
            experiment_changes = _changed_pairs(experiment_pairs, baseline_experiment, axes)
            mismatches = _mismatched_pairs(control_pairs, experiment_pairs, axes)
            vector_drifts = _vector_drift_pairs(control_pairs, experiment_pairs, vector_tolerance)
            if control_changes:
                control_change_frames.append(frame_number)
            if experiment_changes:
                experiment_change_frames.append(frame_number)
            if mismatches:
                mismatch_frames.append(frame_number)
                max_angle_errors.append(
                    max(
                        mismatch["relative_vector_angle_error_degrees"] or 0.0
                        for mismatch in mismatches
                    )
                )
            if vector_drifts:
                vector_drift_frames.append(frame_number)
                vector_drift_values.append(max(item["delta_m"] for item in vector_drifts))
            samples.append(
                {
                    "frame": frame_number,
                    "controls": control_names,
                    "experiments": experiment_names,
                    "control_pairwise": control_pairs,
                    "experiment_pairwise": experiment_pairs,
                    "control_order_changes": control_changes,
                    "experiment_order_changes": experiment_changes,
                    "control_experiment_mismatches": mismatches,
                    "pair_vector_drifts": vector_drifts,
                }
            )

        failure_reasons = []
        if mismatch_frames:
            failure_reasons.append("control_experiment_order_mismatch")
        if vector_drift_frames:
            failure_reasons.append("mapped_pair_vector_drift")
        if missing:
            failure_reasons.append("missing_actor_or_center")
        verdict = "pass" if samples and not failure_reasons else "fail"
        groups.append(
            {
                "group": group_spec,
                "control_tokens": control_tokens,
                "experiment_tokens": experiment_tokens,
                "axes": list(axes),
                "sign_epsilon_m": sign_epsilon,
                "vector_tolerance_m": vector_tolerance,
                "sample_count": len(samples),
                "control_identity": {
                    "order_change_count": len(control_change_frames),
                    "order_change_frames": control_change_frames[:24],
                },
                "experiment_identity": {
                    "order_change_count": len(experiment_change_frames),
                    "order_change_frames": experiment_change_frames[:24],
                },
                "control_experiment_mismatch_count": len(mismatch_frames),
                "mismatch_frames": mismatch_frames[:24],
                "pair_vector_delta_m": _summarize(vector_drift_values),
                "vector_drift_frames": vector_drift_frames[:24],
                "max_relative_vector_angle_error_degrees": max(max_angle_errors) if max_angle_errors else 0.0,
                "missing": missing,
                "failure_reasons": failure_reasons,
                "samples": samples[:24],
                "verdict": verdict,
            }
        )
    return {
        "schema": SPATIAL_IDENTITY_GROUP_SCHEMA,
        "principle": (
            "matched multi-actor groups must preserve 3D pairwise spatial identity: "
            "control actors and experiment actors should keep the same relative order along x/y/z axes, "
            "and each group is checked for its own order changes before control-vs-experiment comparison."
        ),
        "verdict": "pass" if groups and all(group["verdict"] == "pass" for group in groups) else "fail",
        "groups": groups,
    }
