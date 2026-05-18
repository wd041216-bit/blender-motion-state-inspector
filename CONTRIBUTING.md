# Contributing

Thanks for helping improve Blender Motion State Inspector.

The project is intentionally small: Blender collects raw state, the analyzer turns that state into LLM-readable facts, and downstream tools decide what to do with those facts.

## Good First Contributions

- Add skeleton naming patterns for a rig family.
- Improve actor classification for props, floors, helpers, and characters.
- Add a regression fixture for a known `.glb` or `.blend` shape.
- Improve facing inference for a tricky avatar orientation.
- Add animation event clustering rules.

## Development Setup

```bash
python -m pip install -e .
python -m pytest tests/test_loader.py tests/test_morphology.py tests/test_skeleton_semantics.py tests/test_spatial.py tests/test_contact_detector.py tests/test_anomaly_detector.py tests/test_pose_classifier.py tests/test_formatter.py tests/test_cli.py tests/test_actor_classifier.py -q
```

Blender headless integration:

```bash
blender --background --python tests/test_blender_addon.py
```

## Design Rules

- Prefer structured facts over screenshots.
- Keep Blender collection and Python analysis loosely coupled.
- Preserve source scene assets; never mutate the input file while inspecting.
- Treat character/prop classification as probabilistic and report confidence.
- For LLM-facing fields, include evidence and units.

## Pull Request Checklist

- Tests pass locally.
- New analyzer behavior includes at least one unit test.
- New Blender collector behavior is backward compatible with old raw JSON where practical.
- README or examples are updated when CLI behavior changes.
