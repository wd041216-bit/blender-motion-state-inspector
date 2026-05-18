# Examples

## Single Frame

```bash
blender --background --python scripts/collect_blender_state.py -- \
  --input path/to/avatar.glb \
  --output /tmp/avatar_raw_state.json \
  --frame 1

python -m analyzer.cli /tmp/avatar_raw_state.json \
  --output-md /tmp/avatar_report.md \
  --output-json /tmp/avatar_report.json
```

## Animation Sampling

```bash
blender --background --python scripts/collect_blender_state.py -- \
  --input path/to/scene.blend \
  --output /tmp/animation_state.json \
  --frame-start 1 \
  --frame-end 400 \
  --frame-step 20

python -m analyzer.cli /tmp/animation_state.json \
  --output-md /tmp/animation_report.md \
  --output-json /tmp/animation_report.json \
  --output-jsonl /tmp/frame_diagnostics.jsonl
```

## Minimal Report Shape

```json
{
  "summary": "Avatar character 伸展，无异常",
  "actors": [
    {
      "name": "Avatar",
      "classification": {
        "class": "character",
        "confidence": 0.95
      },
      "morphology": {
        "height": 1.8563,
        "vertical_extent": 1.8563,
        "shoulder_width": 0.7006,
        "unit_scale": 1.0
      },
      "facing": {
        "vector": [-0.054062, -0.99799, 0.033076],
        "source": "torso_cross_validated_by_toes",
        "confidence": 0.9
      },
      "ground_clearance_m": 0.0965,
      "anomalies": []
    }
  ]
}
```
