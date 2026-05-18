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
- `simplified` (boolean): if true, skip per-vertex data for performance
- `output_format` (string): `"markdown"`, `"json"`, or `"both"`

**Returns:**
- `report_path` (string): path to the generated report file
- `summary` (string): one-sentence summary of the scene state

## Workflow
1. Ensure Blender is running and the Motion State Inspector addon is enabled.
2. If the server is not running, instruct the user to start it via N-Panel > Motion State > Start Server.
3. Send a TCP command to `127.0.0.1:9658`:
   ```json
   {"cmd": "inspect", "target": "all", "simplified": false}
   ```
4. Receive the response:
   ```json
   {"status": "ok", "path": "/tmp/bmsi_..._raw_state.json", "elapsed_ms": 1200}
   ```
5. Run the analyzer CLI:
   ```bash
   blender-state-inspector /tmp/bmsi_..._raw_state.json --output-md report.md --output-json report.json
   ```
6. Return the report path and summary to the user.

## Prerequisites
- Blender 4.0+ with Motion State Inspector addon installed and enabled
- `blender-state-inspector` CLI installed (`pip install -e .` from project root)
