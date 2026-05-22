# Agent Workflow

Blender Motion State Inspector is designed to sit between a 3D generation step and an automated decision step.

```text
asset or scene
  -> collect raw Blender state
  -> analyze structured facts
  -> agent decides accept / retry / escalate
```

## Single Frame Gate

Use when a generated model or pose needs a quick sanity check.

```bash
blender --background --python scripts/collect_blender_state.py -- \
  --input scene.blend \
  --output raw_state.json \
  --frame 120

python -m analyzer.cli raw_state.json \
  --output-md report.md \
  --output-json report.json
```

The agent reads:

- actor classification
- morphology
- skeleton semantics
- facing
- contacts
- anomalies

## Blender Extension Packaging

The interactive add-on can be validated and packaged with Blender's extension CLI:

```bash
blender --command extension validate addon --valid-tags=""
blender --command extension build --source-dir addon --output-dir dist --valid-tags=""
```

The package is intended for review through the Blender Extensions platform rather than as a Blender core patch.

## Motion Gate

Use when an action needs to be checked across a frame range.

```bash
blender --background --python scripts/collect_blender_state.py -- \
  --input scene.blend \
  --output animation_state.json \
  --frame-start 1 \
  --frame-end 400 \
  --frame-step 10

python -m analyzer.cli animation_state.json \
  --output-md report.md \
  --output-json report.json \
  --output-jsonl frame_diagnostics.jsonl
```

The agent reads:

- frame diagnostics
- event diagnostics
- ground clearance over time
- facing changes
- anomaly ranges

## Compact Spatial Packet

Use when a text-only agent needs spatial context without reading the full raw
state or every frame report.

```bash
python -m analyzer.cli animation_state.json \
  --output-md report.md \
  --output-json report.json \
  --output-jsonl frame_diagnostics.jsonl \
  --output-spatial-packet spatial_packet.json \
  --spatial-ego-actor "Chad" \
  --spatial-top-k 24
```

The packet writes stable actor IDs, compact bboxes, actor-centric relation
labels, nearest relation rows, and merged temporal pose ranges. Agents should
read `spatial_packet.json` first for scene navigation, then fall back to
`report.json` or `frame_diagnostics.jsonl` only when they need full evidence.

Important fields:

- `actors`: stable IDs, classes, pose, bbox, facing basis, contacts.
- `relations`: top-K pairwise spatial relations such as `front_right_mid`.
- `temporal_events`: merged pose ranges for timeline reports.

## Recommended Decision Policy

- Accept: no high-severity anomalies and facing confidence is high.
- Scene retry: camera, floor, actor offset, or prop classification issue.
- Motion retry: event timing, contact, or limb crossover issue.
- Parameter tuning: repeated deformation, wrong skeleton semantics, or facing inference instability.
