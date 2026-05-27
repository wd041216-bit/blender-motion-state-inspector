from analyzer.interaction import evaluate_interaction_pairs


def actor(name, x, facing, left_hand, right_hand, left_elbow=80.0, right_elbow=80.0):
    def point(px, py, pz):
        return {"head": [px, py, pz], "tail": [px, py, pz + 0.1]}

    return {
        "name": name,
        "classification": {"class": "character", "is_character": True},
        "facing": {"vector": facing, "confidence": 0.9},
        "body_anchors": {
            "chest": point(x, 0.0, 1.25),
            "neck": point(x, 0.0, 1.45),
            "left_shoulder": point(x, -0.22, 1.38),
            "right_shoulder": point(x, 0.22, 1.38),
            "left_forearm": point(left_hand[0] * 0.5 + x * 0.5, left_hand[1], left_hand[2]),
            "right_forearm": point(right_hand[0] * 0.5 + x * 0.5, right_hand[1], right_hand[2]),
            "left_hand": point(*left_hand),
            "right_hand": point(*right_hand),
        },
        "_test_elbow": {"left": left_elbow, "right": right_elbow},
    }


def report(left, right):
    return {
        "frame_reports": [
            {
                "frame_info": {"current": 1},
                "actors": [left, right],
            }
        ]
    }


def test_interaction_pair_passes_when_each_actor_reaches_partner_torso():
    left = actor("experiment_joe_Belt", 0.0, [1, 0, 0], [0.95, -0.12, 1.3], [0.95, 0.12, 1.3])
    right = actor("experiment_alex_Ch18", 1.0, [-1, 0, 0], [0.05, -0.12, 1.3], [0.05, 0.12, 1.3])

    result = evaluate_interaction_pairs(report(left, right), ["experiment_joe=experiment_alex"], contact_tolerance=0.35)

    assert result["verdict"] == "pass"
    pair = result["pairs"][0]
    assert pair["ok_frame_ratio"] == 1.0
    assert pair["failure_counts"]["left_actor_no_partner_hand_contact"] == 0
    assert pair["failure_counts"]["right_actor_no_partner_hand_contact"] == 0


def test_interaction_pair_fails_when_hands_are_self_biased_and_folded():
    left = actor("experiment_joe_Belt", 0.0, [1, 0, 0], [0.05, -0.1, 1.22], [0.04, 0.1, 1.22])
    right = actor("experiment_alex_Ch18", 1.0, [-1, 0, 0], [0.95, -0.1, 1.22], [0.96, 0.1, 1.22])

    result = evaluate_interaction_pairs(report(left, right), ["experiment_joe=experiment_alex"], contact_tolerance=0.35)

    assert result["verdict"] == "fail"
    pair = result["pairs"][0]
    assert pair["failure_counts"]["folded_or_self_biased_hands"] == 1
    assert pair["failure_counts"]["left_actor_no_partner_hand_contact"] == 1
    assert pair["failure_counts"]["right_actor_no_partner_hand_contact"] == 1


def test_interaction_pair_fails_when_close_hands_do_not_reach_toward_partner():
    left = actor("experiment_joe_Belt", 0.0, [1, 0, 0], [0.0, -0.18, 1.62], [0.0, 0.18, 1.62])
    right = actor("experiment_alex_Ch18", 0.28, [-1, 0, 0], [0.28, -0.18, 1.62], [0.28, 0.18, 1.62])

    result = evaluate_interaction_pairs(report(left, right), ["experiment_joe=experiment_alex"], contact_tolerance=0.42)

    assert result["verdict"] == "fail"
    pair = result["pairs"][0]
    assert pair["failure_counts"]["hands_not_reaching_toward_partner"] == 1
    assert pair["failure_counts"]["left_actor_no_partner_hand_contact"] == 1
    assert pair["failure_counts"]["right_actor_no_partner_hand_contact"] == 1
