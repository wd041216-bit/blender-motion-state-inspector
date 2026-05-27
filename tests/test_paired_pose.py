from analyzer.paired_pose import evaluate_paired_pose_groups


def paired_report(control_frames, experiment_frames):
    def bounds(center, size):
        return {"center": center, "size": size}

    def frame(number, control0, control1, experiment0, experiment1):
        return {
            "frame_info": {"current": number, "fps": 24},
            "spatial": {
                "actor_bounds": {
                    "control_mesh_person0": bounds(*control0),
                    "control_mesh_person1": bounds(*control1),
                    "experiment_joe_Belt": bounds(*experiment0),
                    "experiment_alex_Ch18": bounds(*experiment1),
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


def test_paired_pose_passes_when_experiment_pair_replicates_control_envelope_and_overlap():
    controls = [
        (
            ([0.0, 0.0, 0.9], [0.62, 0.42, 1.8]),
            ([0.48, 0.0, 0.9], [0.62, 0.42, 1.8]),
        ),
        (
            ([0.1, 0.0, 0.9], [0.62, 0.42, 1.8]),
            ([0.58, 0.0, 0.9], [0.62, 0.42, 1.8]),
        ),
    ]
    experiments = [
        (
            ([4.0, 0.0, 0.9], [0.66, 0.46, 1.82]),
            ([4.48, 0.0, 0.9], [0.66, 0.46, 1.82]),
        ),
        (
            ([4.1, 0.0, 0.9], [0.66, 0.46, 1.82]),
            ([4.58, 0.0, 0.9], [0.66, 0.46, 1.82]),
        ),
    ]

    result = evaluate_paired_pose_groups(
        paired_report(controls, experiments),
        ["control_mesh_person0,control_mesh_person1=experiment_joe,experiment_alex"],
    )

    assert result["verdict"] == "pass"
    group = result["groups"][0]
    assert group["failure_reasons"] == []
    assert group["pair_envelope_delta_m"]["max"] < 0.08
    assert group["overlap_delta"]["max"] < 0.1


def test_paired_pose_fails_when_experiment_pair_shape_and_overlap_diverge_from_control():
    controls = [
        (
            ([0.0, 0.0, 0.9], [0.62, 0.42, 1.8]),
            ([0.48, 0.0, 0.9], [0.62, 0.42, 1.8]),
        ),
        (
            ([0.1, 0.0, 0.9], [0.62, 0.42, 1.8]),
            ([0.58, 0.0, 0.9], [0.62, 0.42, 1.8]),
        ),
    ]
    experiments = [
        (
            ([4.0, 0.0, 0.9], [0.82, 0.38, 1.88]),
            ([4.86, -0.18, 0.9], [0.82, 0.38, 1.88]),
        ),
        (
            ([4.1, 0.0, 0.9], [0.82, 0.38, 1.88]),
            ([4.96, -0.18, 0.9], [0.82, 0.38, 1.88]),
        ),
    ]

    result = evaluate_paired_pose_groups(
        paired_report(controls, experiments),
        ["control_mesh_person0,control_mesh_person1=experiment_joe,experiment_alex"],
        envelope_tolerance=0.12,
        overlap_tolerance=0.18,
    )

    assert result["verdict"] == "fail"
    group = result["groups"][0]
    assert "pair_envelope_drift" in group["failure_reasons"]
    assert "pair_overlap_drift" in group["failure_reasons"]
    assert group["pair_envelope_delta_m"]["max"] > 0.3
    assert group["overlap_delta"]["max"] > 0.4
