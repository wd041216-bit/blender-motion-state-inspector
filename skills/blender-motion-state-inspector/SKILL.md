---
name: blender-motion-state-inspector
description: Use this skill when the user asks to inspect Blender, GLB, GLTF, or FBX character scenes, debug retargeted animation, compare avatar pose state, identify model facing/ground/contact/clipping issues, or create LLM-readable 3D motion reports.
version: 0.1.1
license: MIT
---

# Blender Motion State Inspector

Use this skill to turn a 3D scene or animation into structured facts that an
LLM can read without guessing from screenshots.

## When To Use

Use this skill for:

- Blender scene inspection and QA.
- Avatar, armature, skeleton, or motion-retargeting debugging.
- Facing, posture, morphology, floor contact, clipping, and actor spacing checks.
- Generating Markdown, JSON, or JSONL reports from `.blend`, `.glb`, `.gltf`, or `.fbx` files.

## Workflow

1. Install the project if the CLI is not already available:

   ```bash
   python -m pip install -e .
   ```

2. Collect state from a scene with Blender:

   ```bash
   blender --background --python scripts/collect_blender_state.py -- \
     --input scene.blend \
     --output raw_state.json \
     --frame 120
   ```

3. For motion sampling, collect a frame range:

   ```bash
   blender --background --python scripts/collect_blender_state.py -- \
     --input scene.blend \
     --output animation_state.json \
     --frame-start 1 \
     --frame-end 400 \
     --frame-step 20
   ```

4. Analyze the raw state:

   ```bash
   blender-state-inspector animation_state.json \
     --output-md report.md \
     --output-json report.json \
     --output-jsonl frame_diagnostics.jsonl
   ```

5. For temporal clipping or ground-penetration QA, add a clip check:

   ```bash
   blender-state-inspector animation_state.json \
     --clip-check \
     --clip-tolerance 0.01 \
     --clip-frame-start 40 \
     --clip-frame-end 96 \
     --output-md report.md \
     --output-json report.json
   ```

## Report Expectations

Prefer evidence from the generated report over visual guesses. Inspect:

- actor classification: character, static mesh, scene prop, helper, floor
- normalized morphology: height, width, depth, vertical extent, unit scale
- skeleton semantics and Mixamo/Mecanim-compatible bone names
- facing vectors, source, confidence, and foot/head cross-checks
- pose state and anomaly flags
- ground clearance and contact facts
- actor-to-actor distances and bbox overlap
- temporal clipping verdict and failing-frame diagnostics

## Interactive Blender Mode

If Blender is already open and the addon is enabled:

1. Open the N-panel.
2. Go to the `Motion State` tab.
3. Start the local socket server.
4. Send an inspect command to `127.0.0.1:9658`.

Example socket payload:

```json
{"cmd": "inspect", "target": "all", "simplified": false}
```

Then run the analyzer on the returned raw-state path.

## Important Notes

- The inspector reports facts; it does not generate or fix animations.
- For ambiguous animation QA, combine the report with one-frame-at-a-time visual review.
- Use full vertex collection when precise clipping/contact evidence matters.
- Use simplified collection only for fast scene triage.
