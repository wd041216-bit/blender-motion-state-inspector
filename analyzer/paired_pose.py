from __future__ import annotations

import math
from typing import Any


PAIRED_POSE_GROUP_SCHEMA = "motion_state_paired_pose_groups.v1"


def _number(value: float, digits: int = 5) -> float:
    return round(float(value), digits)


def _summarize(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "mean": None, "max": None}
    return {"count": len(values), "mean": _number(sum(values) / len(values)), "max": _number(max(values))}


def _distance(values: list[float]) -> float:
    return math.sqrt(sum(float(value) * float(value) for value in values[:3]))


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
        raise ValueError(f"Paired pose group must use controls=experiments format: {group_spec!r}")
    left, right = group_spec.split("=", 1)
    controls = [item.strip() for item in left.split(",") if item.strip()]
    experiments = [item.strip() for item in right.split(",") if item.strip()]
    if not controls or not experiments or len(controls) != len(experiments):
        raise ValueError(
            "Paired pose group must name the same number of control and experiment actor tokens: "
            f"{group_spec!r}"
        )
    if len(controls) < 2:
        raise ValueError(f"Paired pose group needs at least two actors: {group_spec!r}")
    return controls, experiments


def _center_size(bounds: dict[str, Any], name: str) -> tuple[list[float], list[float]] | None:
    item = bounds.get(name, {})
    center = item.get("center")
    size = item.get("size")
    if isinstance(center, list) and isinstance(size, list) and len(center) >= 3 and len(size) >= 3:
        return [float(v) for v in center[:3]], [abs(float(v)) for v in size[:3]]
    return None


def _minmax(center: list[float], size: list[float]) -> tuple[list[float], list[float]]:
    half = [value / 2.0 for value in size]
    return [center[i] - half[i] for i in range(3)], [center[i] + half[i] for i in range(3)]


def _union_size(items: list[tuple[list[float], list[float]]]) -> list[float]:
    mins = []
    maxs = []
    for center, size in items:
        bmin, bmax = _minmax(center, size)
        mins.append(bmin)
        maxs.append(bmax)
    return [max(item[i] for item in maxs) - min(item[i] for item in mins) for i in range(3)]


def _overlap_ratios(items: list[tuple[list[float], list[float]]]) -> dict[str, float]:
    if len(items) != 2:
        return {"x": 0.0, "y": 0.0, "z": 0.0}
    (a_center, a_size), (b_center, b_size) = items
    ratios = {}
    for axis, index in (("x", 0), ("y", 1), ("z", 2)):
        a_min, a_max = a_center[index] - a_size[index] / 2.0, a_center[index] + a_size[index] / 2.0
        b_min, b_max = b_center[index] - b_size[index] / 2.0, b_center[index] + b_size[index] / 2.0
        overlap = max(0.0, min(a_max, b_max) - max(a_min, b_min))
        denom = max(min(a_size[index], b_size[index]), 1e-8)
        ratios[axis] = overlap / denom
    return ratios


def evaluate_paired_pose_groups(
    report: dict[str, Any],
    group_specs: list[str],
    envelope_tolerance: float = 0.18,
    overlap_tolerance: float = 0.22,
) -> dict[str, Any]:
    frames = _frame_reports(report)
    groups = []
    for group_spec in group_specs:
        control_tokens, experiment_tokens = _parse_group_spec(group_spec)
        samples = []
        missing = []
        envelope_deltas: list[float] = []
        overlap_deltas: list[float] = []
        envelope_drift_frames: list[int] = []
        overlap_drift_frames: list[int] = []

        for frame in frames:
            frame_number = frame.get("frame_info", {}).get("current")
            bounds = _bounds(frame)
            control_items = []
            experiment_items = []
            control_names = []
            experiment_names = []
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
                control_item = _center_size(bounds, control_name)
                experiment_item = _center_size(bounds, experiment_name)
                if control_item is None or experiment_item is None:
                    frame_missing.append({"control": control_name, "experiment": experiment_name})
                    continue
                control_names.append(control_name)
                experiment_names.append(experiment_name)
                control_items.append(control_item)
                experiment_items.append(experiment_item)
            if frame_missing:
                missing.append({"frame": frame_number, "members": frame_missing})
                continue

            control_envelope = _union_size(control_items)
            experiment_envelope = _union_size(experiment_items)
            envelope_delta_vector = [experiment_envelope[index] - control_envelope[index] for index in range(3)]
            envelope_delta = _distance(envelope_delta_vector)
            control_overlap = _overlap_ratios(control_items)
            experiment_overlap = _overlap_ratios(experiment_items)
            overlap_axis_delta = {
                axis: abs(experiment_overlap[axis] - control_overlap[axis])
                for axis in ("x", "y", "z")
            }
            overlap_delta = max(overlap_axis_delta.values(), default=0.0)
            envelope_deltas.append(envelope_delta)
            overlap_deltas.append(overlap_delta)
            if envelope_delta > envelope_tolerance:
                envelope_drift_frames.append(frame_number)
            if overlap_delta > overlap_tolerance:
                overlap_drift_frames.append(frame_number)

            samples.append(
                {
                    "frame": frame_number,
                    "controls": control_names,
                    "experiments": experiment_names,
                    "control_pair_envelope_size": [_number(value) for value in control_envelope],
                    "experiment_pair_envelope_size": [_number(value) for value in experiment_envelope],
                    "pair_envelope_delta_vector": [_number(value) for value in envelope_delta_vector],
                    "pair_envelope_delta_m": _number(envelope_delta),
                    "control_overlap": {axis: _number(value) for axis, value in control_overlap.items()},
                    "experiment_overlap": {axis: _number(value) for axis, value in experiment_overlap.items()},
                    "overlap_axis_delta": {axis: _number(value) for axis, value in overlap_axis_delta.items()},
                    "overlap_delta": _number(overlap_delta),
                }
            )

        failure_reasons = []
        if envelope_drift_frames:
            failure_reasons.append("pair_envelope_drift")
        if overlap_drift_frames:
            failure_reasons.append("pair_overlap_drift")
        if missing:
            failure_reasons.append("missing_actor_or_bounds")
        verdict = "pass" if samples and not failure_reasons else "fail"
        groups.append(
            {
                "group": group_spec,
                "control_tokens": control_tokens,
                "experiment_tokens": experiment_tokens,
                "envelope_tolerance_m": envelope_tolerance,
                "overlap_tolerance": overlap_tolerance,
                "sample_count": len(samples),
                "pair_envelope_delta_m": _summarize(envelope_deltas),
                "overlap_delta": _summarize(overlap_deltas),
                "envelope_drift_frames": envelope_drift_frames[:24],
                "overlap_drift_frames": overlap_drift_frames[:24],
                "missing": missing,
                "failure_reasons": failure_reasons,
                "samples": samples[:24],
                "verdict": verdict,
            }
        )
    return {
        "schema": PAIRED_POSE_GROUP_SCHEMA,
        "principle": (
            "InterMask experiment pairs should replicate the mapped control pair pose envelope and body overlap. "
            "The control pair is treated as truth, including unusual contact or crossing."
        ),
        "verdict": "pass" if groups and all(group["verdict"] == "pass" for group in groups) else "fail",
        "groups": groups,
    }
