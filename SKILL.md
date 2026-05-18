# Motion State Inspector Skill

## Description
Inspect 3D character state from Blender and generate structured LLM-readable reports.

## Triggers
- "inspect blender scene"
- "analyze 3D character"
- "check blender model state"

## Tools

### inspect_blender_scene
Trigger Blender state collection and generate a report.

**Parameters:**
- `target` (string): `"all"` or `"selected"` — which objects to inspect
- `frame` (int | null): frame number to inspect; `null` means current frame
- `frame_start` / `frame_end` / `frame_step` (int | null): optional animation sampling range
- `simplified` (boolean): if true, skip per-vertex data for performance
- `output_format` (string): `"markdown"`, `"json"`, or `"both"`

**Returns:**
- `report_path` (string): path to the generated report file
- `summary` (string): one-sentence summary of the scene state

## Workflow
1. Prefer headless collection for automated pipelines:
   ```bash
   blender --background --python scripts/collect_blender_state.py -- \
     --input scene.blend \
     --output raw_state.json \
     --frame 120
   ```
2. For animation sampling, collect an animation state:
   ```bash
   blender --background --python scripts/collect_blender_state.py -- \
     --input scene.blend \
     --output animation_state.json \
     --frame-start 1 \
     --frame-end 400 \
     --frame-step 20
   ```
3. Run the analyzer CLI:
   ```bash
   blender-state-inspector animation_state.json \
     --output-md report.md \
     --output-json report.json \
     --output-jsonl frame_diagnostics.jsonl
   ```
4. If Blender is already running interactively, the addon socket can also be used.
5. Ensure Blender is running and the Motion State Inspector addon is enabled.
6. If the server is not running, instruct the user to start it via N-Panel > Motion State > Start Server.
7. Send a TCP command to `127.0.0.1:9658`:
   ```json
   {"cmd": "inspect", "target": "all", "simplified": false}
   ```
8. Receive the response:
   ```json
   {"status": "ok", "path": "/tmp/bmsi_..._raw_state.json", "elapsed_ms": 1200}
   ```
9. Run the analyzer CLI:
   ```bash
   blender-state-inspector /tmp/bmsi_..._raw_state.json --output-md report.md --output-json report.json
   ```
10. Return the report path and summary to the user.

## Report Expectations
- Distinguish `character` from `scene_prop`, `static_mesh`, and helper/proxy objects.
- Report normalized morphology, including physical height, vertical extent, width/depth, and unit scale.
- Map common Mixamo bones such as `mixamorig:Hips`, `mixamorig:LeftFoot`, and `mixamorig:RightToeBase`.
- Report facing vectors with source and confidence.
- For animation input, produce frame diagnostics and event diagnostics.

## Prerequisites
- Blender 4.0+ with Motion State Inspector addon installed and enabled
- `blender-state-inspector` CLI installed (`pip install -e .` from project root)
