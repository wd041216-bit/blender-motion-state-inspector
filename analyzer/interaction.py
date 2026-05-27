from __future__ import annotations

import math
from typing import Any


INTERACTION_PAIR_SCHEMA = "motion_state_interaction_pairs.v1"


def _number(value: float, digits: int = 5) -> float:
    return round(float(value), digits)


def _distance(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((float(a) - float(b)) ** 2 for a, b in zip(left[:3], right[:3])))


def _vector(left: list[float], right: list[float]) -> list[float]:
    return [float(right[index]) - float(left[index]) for index in range(3)]


def _norm(values: list[float]) -> float:
    return math.sqrt(sum(float(value) * float(value) for value in values[:3]))


def _normalize(values: list[float]) -> list[float] | None:
    length = _norm(values)
    if length < 1e-8:
        return None
    return [float(value) / length for value in values[:3]]


def _dot(left: list[float], right: list[float]) -> float:
    return sum(float(a) * float(b) for a, b in zip(left[:3], right[:3]))


def _angle_degrees(a: list[float], b: list[float]) -> float | None:
    left = _normalize(a)
    right = _normalize(b)
    if left is None or right is None:
        return None
    return math.degrees(math.acos(max(-1.0, min(1.0, _dot(left, right)))))


def _summarize(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "mean": None, "max": None, "min": None}
    return {
        "count": len(values),
        "mean": _number(sum(values) / len(values)),
        "max": _number(max(values)),
        "min": _number(min(values)),
    }


def _frame_reports(report: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(report.get("frame_reports"), list):
        return [frame for frame in report["frame_reports"] if isinstance(frame, dict)]
    return [report]


def _match_actor(frame: dict[str, Any], token: str) -> dict[str, Any] | None:
    actors = [actor for actor in frame.get("actors", []) if isinstance(actor, dict)]
    lowered = token.lower()
    exact = [actor for actor in actors if str(actor.get("name", "")).lower() == lowered]
    if exact:
        return sorted(exact, key=lambda actor: str(actor.get("name", "")))[0]
    partial = [actor for actor in actors if lowered in str(actor.get("name", "")).lower()]
    if partial:
        return sorted(partial, key=lambda actor: (len(str(actor.get("name", ""))), str(actor.get("name", ""))))[0]
    return None


def _parse_pair(pair_spec: str) -> tuple[str, str]:
    if "=" not in pair_spec:
        raise ValueError(f"Interaction pair must use actor_a=actor_b format: {pair_spec!r}")
    left, right = pair_spec.split("=", 1)
    left = left.strip()
    right = right.strip()
    if not left or not right:
        raise ValueError(f"Interaction pair must name both actors: {pair_spec!r}")
    return left, right


def _anchor(actor: dict[str, Any], key: str) -> list[float] | None:
    anchors = actor.get("body_anchors")
    if not isinstance(anchors, dict):
        return None
    value = anchors.get(key)
    if not isinstance(value, dict):
        return None
    point = value.get("head") or value.get("point")
    if isinstance(point, list) and len(point) >= 3:
        return [float(point[0]), float(point[1]), float(point[2])]
    return None


def _midpoint(points: list[list[float] | None]) -> list[float] | None:
    valid = [point for point in points if point is not None]
    if not valid:
        return None
    return [sum(point[index] for point in valid) / len(valid) for index in range(3)]


def _upper_torso(actor: dict[str, Any]) -> list[float] | None:
    return _midpoint(
        [
            _anchor(actor, "chest"),
            _anchor(actor, "neck"),
            _anchor(actor, "left_shoulder"),
            _anchor(actor, "right_shoulder"),
        ]
    )


def _facing_vector(actor: dict[str, Any]) -> list[float] | None:
    facing = actor.get("facing")
    if not isinstance(facing, dict):
        return None
    value = facing.get("vector")
    if isinstance(value, list) and len(value) >= 3:
        return _normalize([float(value[0]), float(value[1]), float(value[2])])
    return None


def _elbow_angle(actor: dict[str, Any], side: str) -> float | None:
    shoulder = _anchor(actor, f"{side}_shoulder")
    elbow = _anchor(actor, f"{side}_forearm")
    hand = _anchor(actor, f"{side}_hand")
    if shoulder is None or elbow is None or hand is None:
        return None
    return _angle_degrees(_vector(elbow, shoulder), _vector(elbow, hand))


def _shoulder_wrist_ratio(actor: dict[str, Any], side: str) -> float | None:
    shoulder = _anchor(actor, f"{side}_shoulder")
    elbow = _anchor(actor, f"{side}_forearm")
    hand = _anchor(actor, f"{side}_hand")
    if shoulder is None or elbow is None or hand is None:
        return None
    arm_length = _distance(shoulder, elbow) + _distance(elbow, hand)
    if arm_length < 1e-8:
        return None
    return _distance(shoulder, hand) / arm_length


def _hand_contact_sample(
    source: dict[str, Any],
    target: dict[str, Any],
    side: str,
    contact_tolerance: float,
    folded_elbow_min_degrees: float,
    folded_ratio_min: float,
    reach_dot_min: float,
) -> dict[str, Any] | None:
    hand = _anchor(source, f"{side}_hand")
    own_torso = _upper_torso(source)
    target_torso = _upper_torso(target)
    target_left = _anchor(target, "left_shoulder")
    target_right = _anchor(target, "right_shoulder")
    if hand is None or own_torso is None or target_torso is None:
        return None
    target_points = [point for point in (target_torso, target_left, target_right) if point is not None]
    target_distance = min(_distance(hand, point) for point in target_points)
    self_distance = _distance(hand, own_torso)
    elbow_angle = _elbow_angle(source, side)
    shoulder_wrist_ratio = _shoulder_wrist_ratio(source, side)
    partner_direction = _normalize(_vector(own_torso, target_torso))
    hand_direction = _normalize(_vector(own_torso, hand))
    reach_dot = _dot(hand_direction, partner_direction) if hand_direction is not None and partner_direction is not None else None
    reaches_partner = target_distance <= contact_tolerance and reach_dot is not None and reach_dot >= reach_dot_min
    self_biased = self_distance + 0.08 < target_distance
    folded = (
        (elbow_angle is not None and elbow_angle < folded_elbow_min_degrees)
        or (shoulder_wrist_ratio is not None and shoulder_wrist_ratio < folded_ratio_min)
    )
    return {
        "side": side,
        "target_distance_m": _number(target_distance),
        "self_distance_m": _number(self_distance),
        "elbow_angle_degrees": _number(elbow_angle) if elbow_angle is not None else None,
        "shoulder_wrist_ratio": _number(shoulder_wrist_ratio) if shoulder_wrist_ratio is not None else None,
        "reach_dot": _number(reach_dot) if reach_dot is not None else None,
        "reaches_partner": reaches_partner,
        "reaches_toward_partner": reach_dot is not None and reach_dot >= reach_dot_min,
        "self_biased": self_biased,
        "folded": folded,
    }


def _actor_contact_state(
    source: dict[str, Any],
    target: dict[str, Any],
    contact_tolerance: float,
    folded_elbow_min_degrees: float,
    folded_ratio_min: float,
    reach_dot_min: float,
) -> dict[str, Any]:
    hands = [
        sample
        for side in ("left", "right")
        if (
            sample := _hand_contact_sample(
                source,
                target,
                side,
                contact_tolerance,
                folded_elbow_min_degrees,
                folded_ratio_min,
                reach_dot_min,
            )
        )
        is not None
    ]
    best_target_distance = min((sample["target_distance_m"] for sample in hands), default=None)
    reaching_hands = [sample["side"] for sample in hands if sample["reaches_partner"]]
    folded_hands = [sample["side"] for sample in hands if sample["folded"]]
    self_biased_hands = [sample["side"] for sample in hands if sample["self_biased"]]
    not_toward_partner_hands = [sample["side"] for sample in hands if not sample["reaches_toward_partner"]]
    return {
        "actor": source.get("name"),
        "target": target.get("name"),
        "hands": hands,
        "best_target_distance_m": best_target_distance,
        "reaching_hands": reaching_hands,
        "folded_hands": folded_hands,
        "self_biased_hands": self_biased_hands,
        "not_toward_partner_hands": not_toward_partner_hands,
        "contact_ok": bool(reaching_hands) and not self_biased_hands and not folded_hands,
    }


def evaluate_interaction_pairs(
    report: dict[str, Any],
    pair_specs: list[str],
    contact_tolerance: float = 0.45,
    folded_elbow_min_degrees: float = 35.0,
    folded_ratio_min: float = 0.37,
    facing_dot_max: float = -0.25,
    reach_dot_min: float = 0.15,
) -> dict[str, Any]:
    frames = _frame_reports(report)
    pairs = []
    for pair_spec in pair_specs:
        left_token, right_token = _parse_pair(pair_spec)
        samples = []
        missing = []
        best_distances: list[float] = []
        facing_dots: list[float] = []
        failure_counts = {
            "missing_actor_or_anchors": 0,
            "not_facing_partner": 0,
            "left_actor_no_partner_hand_contact": 0,
            "right_actor_no_partner_hand_contact": 0,
            "folded_or_self_biased_hands": 0,
            "hands_not_reaching_toward_partner": 0,
        }
        for frame in frames:
            frame_number = frame.get("frame_info", {}).get("current")
            left = _match_actor(frame, left_token)
            right = _match_actor(frame, right_token)
            if left is None or right is None:
                failure_counts["missing_actor_or_anchors"] += 1
                missing.append({"frame": frame_number, "left": left_token, "right": right_token})
                continue
            left_facing = _facing_vector(left)
            right_facing = _facing_vector(right)
            facing_dot = _dot(left_facing, right_facing) if left_facing is not None and right_facing is not None else None
            left_contact = _actor_contact_state(
                left,
                right,
                contact_tolerance,
                folded_elbow_min_degrees,
                folded_ratio_min,
                reach_dot_min,
            )
            right_contact = _actor_contact_state(
                right,
                left,
                contact_tolerance,
                folded_elbow_min_degrees,
                folded_ratio_min,
                reach_dot_min,
            )
            if facing_dot is not None:
                facing_dots.append(facing_dot)
            for state in (left_contact, right_contact):
                if state["best_target_distance_m"] is not None:
                    best_distances.append(float(state["best_target_distance_m"]))
            if facing_dot is None or facing_dot > facing_dot_max:
                failure_counts["not_facing_partner"] += 1
            if not left_contact["contact_ok"]:
                failure_counts["left_actor_no_partner_hand_contact"] += 1
            if not right_contact["contact_ok"]:
                failure_counts["right_actor_no_partner_hand_contact"] += 1
            if left_contact["folded_hands"] or right_contact["folded_hands"] or left_contact["self_biased_hands"] or right_contact["self_biased_hands"]:
                failure_counts["folded_or_self_biased_hands"] += 1
            if left_contact["not_toward_partner_hands"] or right_contact["not_toward_partner_hands"]:
                failure_counts["hands_not_reaching_toward_partner"] += 1
            samples.append(
                {
                    "frame": frame_number,
                    "left_actor": left.get("name"),
                    "right_actor": right.get("name"),
                    "facing_dot": _number(facing_dot) if facing_dot is not None else None,
                    "left_contact": left_contact,
                    "right_contact": right_contact,
                    "frame_ok": (
                        facing_dot is not None
                        and facing_dot <= facing_dot_max
                        and left_contact["contact_ok"]
                        and right_contact["contact_ok"]
                    ),
                }
            )
        sampled_count = len(samples)
        ok_count = sum(1 for sample in samples if sample["frame_ok"])
        ok_ratio = ok_count / sampled_count if sampled_count else 0.0
        if sampled_count and ok_ratio >= 0.8 and not missing:
            verdict = "pass"
        elif sampled_count and ok_ratio >= 0.35:
            verdict = "review"
        else:
            verdict = "fail"
        pairs.append(
            {
                "pair": pair_spec,
                "left_token": left_token,
                "right_token": right_token,
                "contact_tolerance_m": contact_tolerance,
                "folded_elbow_min_degrees": folded_elbow_min_degrees,
                "folded_shoulder_wrist_ratio_min": folded_ratio_min,
                "facing_dot_max": facing_dot_max,
                "reach_dot_min": reach_dot_min,
                "sample_count": sampled_count,
                "ok_frame_count": ok_count,
                "ok_frame_ratio": _number(ok_ratio),
                "best_target_distance_m": _summarize(best_distances),
                "facing_dot": _summarize(facing_dots),
                "failure_counts": failure_counts,
                "missing": missing,
                "samples": samples[:24],
                "verdict": verdict,
            }
        )
    return {
        "schema": INTERACTION_PAIR_SCHEMA,
        "principle": (
            "multi-actor contact is judged from per-character body anchors: actors should face each other, "
            "at least one hand per actor should reach the partner upper torso/shoulder zone, and hands should "
            "not be folded back toward the source actor."
        ),
        "verdict": "pass" if pairs and all(pair["verdict"] == "pass" for pair in pairs) else "fail",
        "pairs": pairs,
    }
