from analyzer.spatial_identity import evaluate_spatial_identity_groups


def paired_report(control_frames, experiment_frames):
    def frame(number, control0, control1, experiment0, experiment1):
        return {
            "frame_info": {"current": number, "fps": 24},
            "spatial": {
                "actor_bounds": {
                    "control_mesh_person0": {"center": control0, "size": [0.6, 0.4, 1.8]},
                    "control_mesh_person1": {"center": control1, "size": [0.6, 0.4, 1.8]},
                    "experiment_joe_Belt": {"center": experiment0, "size": [0.8, 0.5, 1.8]},
                    "experiment_alex_Ch18": {"center": experiment1, "size": [0.8, 0.5, 1.8]},
                }
            },
            "actors": [],
        }

    return {
        "frame_reports": [
            frame(index * 4 + 1, *control_pair, *experiment_pair)
            for index, (control_pair, experiment_pair) in enumerate(zip(control_frames, experiment_frames, strict=True))
        ]
    }


def test_spatial_identity_passes_when_experiment_preserves_control_relative_order():
    controls = [
        ([0.0, 0.0, 0.9], [1.0, 0.2, 0.9]),
        ([0.1, 0.0, 0.9], [1.1, 0.2, 0.9]),
    ]
    experiments = [
        ([4.0, 0.0, 0.9], [5.0, 0.2, 0.9]),
        ([4.1, 0.0, 0.9], [5.1, 0.2, 0.9]),
    ]

    result = evaluate_spatial_identity_groups(
        paired_report(controls, experiments),
        ["control_mesh_person0,control_mesh_person1=experiment_joe,experiment_alex"],
        sign_epsilon=0.05,
    )

    assert result["verdict"] == "pass"
    group = result["groups"][0]
    assert group["control_identity"]["order_change_count"] == 0
    assert group["experiment_identity"]["order_change_count"] == 0
    assert group["control_experiment_mismatch_count"] == 0


def test_spatial_identity_fails_when_experiment_swaps_but_control_does_not():
    controls = [
        ([0.0, 0.0, 0.9], [1.0, 0.0, 0.9]),
        ([0.1, 0.0, 0.9], [1.1, 0.0, 0.9]),
        ([0.2, 0.0, 0.9], [1.2, 0.0, 0.9]),
    ]
    experiments = [
        ([4.0, 0.0, 0.9], [5.0, 0.0, 0.9]),
        ([4.7, 0.0, 0.9], [4.3, 0.0, 0.9]),
        ([5.2, 0.0, 0.9], [4.2, 0.0, 0.9]),
    ]

    result = evaluate_spatial_identity_groups(
        paired_report(controls, experiments),
        ["control_mesh_person0,control_mesh_person1=experiment_joe,experiment_alex"],
        sign_epsilon=0.05,
    )

    assert result["verdict"] == "fail"
    group = result["groups"][0]
    assert group["control_identity"]["order_change_count"] == 0
    assert group["experiment_identity"]["order_change_count"] == 2
    assert group["control_experiment_mismatch_count"] == 2
    assert group["mismatch_frames"] == [5, 9]


def test_spatial_identity_fails_when_pair_vector_has_3d_offset_without_order_swap():
    controls = [
        ([0.0, 0.0, 0.9], [1.0, 0.0, 0.9]),
        ([0.1, 0.0, 0.9], [1.1, 0.0, 0.9]),
    ]
    experiments = [
        ([4.0, 0.0, 0.9], [5.16, -0.12, 0.88]),
        ([4.1, 0.0, 0.9], [5.26, -0.12, 0.88]),
    ]

    result = evaluate_spatial_identity_groups(
        paired_report(controls, experiments),
        ["control_mesh_person0,control_mesh_person1=experiment_joe,experiment_alex"],
        vector_tolerance=0.05,
    )

    assert result["verdict"] == "fail"
    group = result["groups"][0]
    assert group["failure_reasons"] == ["mapped_pair_vector_drift"]
    assert group["pair_vector_delta_m"]["max"] > 0.2
    assert group["vector_drift_frames"] == [1, 5]


def test_spatial_identity_reports_control_group_swaps_too():
    controls = [
        ([0.0, 0.0, 0.9], [1.0, 0.0, 0.9]),
        ([1.2, 0.0, 0.9], [0.2, 0.0, 0.9]),
    ]
    experiments = [
        ([4.0, 0.0, 0.9], [5.0, 0.0, 0.9]),
        ([5.2, 0.0, 0.9], [4.2, 0.0, 0.9]),
    ]

    result = evaluate_spatial_identity_groups(
        paired_report(controls, experiments),
        ["control_mesh_person0,control_mesh_person1=experiment_joe,experiment_alex"],
        sign_epsilon=0.05,
    )

    assert result["verdict"] == "pass"
    group = result["groups"][0]
    assert group["control_identity"]["order_change_count"] == 1
    assert group["experiment_identity"]["order_change_count"] == 1
    assert group["control_experiment_mismatch_count"] == 0
    assert group["pair_vector_delta_m"]["max"] in (None, 0.0)
    assert group["failure_reasons"] == []


def test_spatial_identity_fails_when_control_swaps_and_experiment_does_not_follow():
    controls = [
        ([0.0, 0.0, 0.9], [1.0, 0.0, 0.9]),
        ([1.2, 0.0, 0.9], [0.2, 0.0, 0.9]),
    ]
    experiments = [
        ([4.0, 0.0, 0.9], [5.0, 0.0, 0.9]),
        ([4.2, 0.0, 0.9], [5.2, 0.0, 0.9]),
    ]

    result = evaluate_spatial_identity_groups(
        paired_report(controls, experiments),
        ["control_mesh_person0,control_mesh_person1=experiment_joe,experiment_alex"],
        sign_epsilon=0.05,
    )

    assert result["verdict"] == "fail"
    group = result["groups"][0]
    assert group["control_identity"]["order_change_count"] == 1
    assert group["experiment_identity"]["order_change_count"] == 0
    assert group["failure_reasons"] == ["control_experiment_order_mismatch", "mapped_pair_vector_drift"]
