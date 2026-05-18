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

## Recommended Decision Policy

- Accept: no high-severity anomalies and facing confidence is high.
- Scene retry: camera, floor, actor offset, or prop classification issue.
- Motion retry: event timing, contact, or limb crossover issue.
- Parameter tuning: repeated deformation, wrong skeleton semantics, or facing inference instability.
