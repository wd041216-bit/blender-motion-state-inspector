# Blender Motion State Inspector

[![Tests](https://github.com/wd041216-bit/blender-motion-state-inspector/actions/workflows/tests.yml/badge.svg)](https://github.com/wd041216-bit/blender-motion-state-inspector/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![Blender 4.2+](https://img.shields.io/badge/Blender-4.2%2B-orange.svg)](https://www.blender.org/)

A tool that converts 3D character models, armatures, actions, materials, and scene relationships into LLM-readable structured state reports.

It answers: What is the current form and posture of this 3D character? How is it moving? Are there any anomalies (inverted joints, floating, squashing)? What is the spatial relationship with the scene, props, and other actors?

**It does NOT generate animations or fix models.** It reports facts. QA, retarget, animation alignment, and story acceptance are downstream applications.

---

## Why This Exists

LLM agents are increasingly asked to inspect avatars, retargeted motion, game scenes, robotics simulations, and digital-human assets. Screenshots are useful, but they are ambiguous: a model can be facing backward, slightly floating, folded at the waist, or misclassified as a prop, and a text-only agent has to guess.

Blender Motion State Inspector turns a `.blend`, `.glb`, `.gltf`, or `.fbx` scene into structured facts:

- character vs prop/helper/floor classification
- normalized morphology: height, vertical extent, width, depth, unit scale
- Mixamo-friendly skeleton semantics
- facing/up/side/foot-forward vectors with confidence
- ground clearance and contact facts
- single-frame reports and multi-frame JSONL diagnostics
- temporal clipping checks with pass/fail verdicts and failing-frame spatial details

The goal is simple: make 3D state readable by agents without requiring them to stare at pixels.

---

## Quick Demo

Collect a single frame:

```bash
blender --background --python scripts/collect_blender_state.py -- \
  --input scene.blend \
  --output raw_state.json \
  --frame 120

python -m analyzer.cli raw_state.json \
  --output-md report.md \
  --output-json report.json
```

Sample a motion:

```bash
blender --background --python scripts/collect_blender_state.py -- \
  --input scene.blend \
  --output animation_state.json \
  --frame-start 1 \
  --frame-end 400 \
  --frame-step 20

python -m analyzer.cli animation_state.json \
  --output-md report.md \
  --output-json report.json \
  --output-jsonl frame_diagnostics.jsonl
```

Run a temporal clipping check over the sampled frame range:

```bash
python -m analyzer.cli animation_state.json \
  --clip-check \
  --clip-tolerance 0.01 \
  --clip-frame-start 40 \
  --clip-frame-end 96 \
  --output-md report.md \
  --output-json report.json
```

The `clip_check` section reports `verdict: pass` when no clipping is found in
the requested time window. If clipping is detected, it reports the failing
frames with spatial diagnostics such as object names, overlap center,
axis overlap depth, actor bounding boxes, and ground penetration depth.

Example frame diagnostic:

```json
{
  "frame": 161,
  "actor": "Avatar",
  "pose_state": "伸展",
  "facing": {
    "vector": [-0.10087, -0.994312, 0.034185],
    "source": "torso_cross_validated_by_toes",
    "confidence": 0.9
  },
  "ground_clearance_m": 0.0968,
  "anomalies": []
}
```

---

## Architecture

```
Blender (3D Viewport)
  ├─ N-Panel UI: "Motion State" tab
  ├─ Collector: bpy scene traversal ──┐
  └─ Socket Server: TCP 127.0.0.1     │
                                      ▼
Unity (Editor / Play Mode)      raw_state.json
  └─ C# Exporter: UnityPlugin ────────┘
                                      │
                                      ▼
CLI Analyzer (pip installable) <──────┘
  ├─ Loader: raw_state.json → Python dataclasses
  ├─ Actor Classifier: character vs prop/helper/floor filtering
  ├─ Morphology: body proportions from bbox + bones
  ├─ Skeleton Semantics: bone name pattern matching (Blender & Unity Mecanim support)
  ├─ Facing: torso/head/foot forward vectors and confidence
  ├─ Pose Classifier: rule-based posture detection
  ├─ Anomaly Detector: joint inversion, floating, squashing
  ├─ Spatial: distance, orientation, camera calc
  ├─ Contact Detector: ground contact / collision
  ├─ Clip Detector: temporal bbox/ground penetration pass-fail diagnostics
  └─ Formatter: Markdown + JSON report output
```

---

## Installation

```bash
git clone https://github.com/wd041216-bit/blender-motion-state-inspector.git
cd blender-motion-state-inspector
python -m pip install -e .
```

Verify:

```bash
blender-state-inspector --help
python -m pytest tests/test_loader.py tests/test_morphology.py tests/test_skeleton_semantics.py tests/test_spatial.py tests/test_contact_detector.py tests/test_clip_detector.py tests/test_anomaly_detector.py tests/test_pose_classifier.py tests/test_formatter.py tests/test_cli.py tests/test_actor_classifier.py -q
```

---

## Quick Start

### Prerequisites
- Blender 4.2+
- Python 3.11+
- Docker (optional, for headless testing)

### 1. Install the CLI

```bash
git clone https://github.com/wd041216-bit/blender-motion-state-inspector.git
cd blender-motion-state-inspector
pip install -e .
```

Verify:
```bash
blender-state-inspector --help
```

### 2. Install the Blender Addon

1. Build the extension package:
   ```bash
   mkdir -p dist
   blender --command extension build --source-dir addon --output-dir dist --valid-tags=""
   ```
2. In Blender: Edit → Preferences → Add-ons → Install...
3. Select `dist/motion_state_inspector-0.1.1.zip`
4. Enable "3D View: Motion State Inspector"
5. Open the N-Panel (press N) → "Motion State" tab

### 2b. Build as a Blender Extension

The `addon/` directory includes a `blender_manifest.toml` for Blender's extension tooling:

```bash
blender --command extension validate addon --valid-tags=""
blender --command extension build --source-dir addon --output-dir dist --valid-tags=""
blender --command extension validate dist/motion_state_inspector-0.1.1.zip --valid-tags=""
```

This produces a local extension package that can be reviewed before submission to the Blender Extensions platform.

### 3. Use from Blender (Manual)

1. Open a scene with a rigged character
2. N-Panel → Motion State → "Inspect Scene"
3. Find the generated `raw_state.json` path in the status bar
4. Run analyzer:
   ```bash
   blender-state-inspector /tmp/bmsi_xxx_raw_state.json --output-md report.md --output-json report.json
   ```

### 4. Use from Agent (Remote Trigger)

1. In Blender N-Panel → click "Start Server" (port 9658)
2. From your LLM agent:
   ```json
   {"cmd": "inspect", "target": "all", "simplified": false}
   ```
3. Receive response:
   ```json
   {"status": "ok", "path": "/tmp/bmsi_xxx_raw_state.json", "elapsed_ms": 500}
   ```
4. Run CLI analyzer on the returned path

The socket listener runs in a separate Python subprocess. Blender scene
collection still runs on Blender's main thread via `bpy.app.timers`, avoiding
in-process Python threading inside Blender.

### 5. Use Headless From Blender

For automated pipelines, collect state without opening the addon UI:

```bash
blender --background --python scripts/collect_blender_state.py -- \
  --input scene.blend \
  --output raw_state.json \
  --frame 120
```

Sample an animation range:

```bash
blender --background --python scripts/collect_blender_state.py -- \
  --input scene.blend \
  --output animation_state.json \
  --frame-start 1 \
  --frame-end 400 \
  --frame-step 20

python -m analyzer.cli animation_state.json \
  --output-md report.md \
  --output-json report.json \
  --output-jsonl frame_diagnostics.jsonl
```

Temporal clipping check:

```bash
python -m analyzer.cli animation_state.json \
  --clip-check \
  --clip-tolerance 0.01 \
  --clip-frame-start 40 \
  --clip-frame-end 96 \
  --output-md report.md \
  --output-json report.json
```

When no clipping is found in the selected time window, `clip_check.verdict`
is `pass`. If clipping is found, the report lists the failing frames with
object names, overlap center, axis overlap depth, actor bounding boxes, and
ground penetration depth.

### 6. Use From Unity (C# Exporter Plugin)

You can automatically capture and inspect the active scene state directly from the Unity Editor, without using Blender.

#### Add the Exporter to Unity
Copy the C# exporter script [addon/unity/UnityMotionStateExporter.cs](addon/unity/UnityMotionStateExporter.cs) into your Unity project's `Assets` folder (preferably under an `Editor` folder, e.g. `Assets/Editor/UnityMotionStateExporter.cs`).

#### Export Current Frame
1. Open your scene in Unity.
2. In the top menu bar, click **Tools** > **Motion State Inspector** > **Export Current Frame**.
3. Choose a folder and save the file (e.g., `raw_state.json`).

The exporter automatically:
- Traverses all active GameObjects containing `Animator` or `Renderer` components.
- Extracts armature structure, joint positions, bounding boxes, vertex counts, materials, and active camera state.
- Maps Unity's Left-Handed, Y-Up coordinate system `(X, Y, Z)` to Blender's Right-Handed, Z-Up coordinate system `(X, -Z, Y)` during export so that the generated file is fully compatible with the Python analyzer out of the box.
- Serializes decimals using `CultureInfo.InvariantCulture` to prevent syntax errors in systems configured with European/non-US locales.

#### Run Python Analyzer
Analyze the exported file with the Python CLI:
```bash
blender-state-inspector raw_state.json --output-md report.md --output-json report.json
```

---

## Project Structure

```
blender-motion-state-inspector/
├── addon/                          # Addons for Blender and Unity
│   ├── unity/                      # Unity C# Exporter plugin
│   │   └── UnityMotionStateExporter.cs
│   ├── __init__.py                 # Blender Addon registration
│   ├── collector.py                # bpy scene traversal → raw_state.json
│   ├── panel.py                    # N-Panel UI
│   ├── socket_server.py            # Blender-side subprocess/timer bridge
│   ├── socket_server_process.py    # Pure Python local TCP subprocess
│   └── utils.py                    # Blender helpers
├── analyzer/                       # CLI analyzer (pip installable)
│   ├── __init__.py
│   ├── cli.py                      # Entry point: blender-state-inspector
│   ├── loader.py                   # raw_state.json → dataclasses
│   ├── morphology.py               # Body proportion calculations
│   ├── skeleton_semantics.py       # Bone naming pattern matching
│   ├── pose_classifier.py          # Posture detection rules
│   ├── anomaly_detector.py         # Issue detection thresholds
│   ├── spatial.py                  # Distance/orientation/camera
│   ├── contact_detector.py         # Ground contact / collision
│   ├── clip_detector.py            # Temporal clipping pass/fail diagnostics
│   └── formatter.py                # JSON + Markdown output
├── tests/                          # Test suite
│   ├── test_loader.py
│   ├── test_morphology.py
│   ├── test_skeleton_semantics.py
│   ├── test_pose_classifier.py
│   ├── test_anomaly_detector.py
│   ├── test_spatial.py
│   ├── test_contact_detector.py
│   ├── test_clip_detector.py
│   ├── test_formatter.py
│   ├── test_cli.py
│   ├── test_blender_addon.py       # Headless Blender integration test
│   └── assets/
│       └── sample_raw.json         # Test fixture
├── Dockerfile                      # Ubuntu 24.04 + Blender headless
├── SKILL.md                        # Claude Code / Codex skill definition
├── pyproject.toml
├── setup.py
└── README.md
```

---

## Key Interfaces

### Collector Output (raw_state.json)

The collector exports a single JSON file with this schema:

```json
{
  "meta": {
    "blender_version": "4.2.0",
    "scene_name": "untitled",
    "current_frame": 1,
    "fps": 24
  },
  "actors": [
    {
      "name": "Character_A",
      "type": "MESH",
      "world_matrix": [...],
      "mesh": {
        "vertex_count": 8234,
        "bbox_min": [-0.45, -0.12, 0.0],
        "bbox_max": [0.45, 0.15, 1.78],
        "materials": ["Skin"],
        "has_armature_modifier": true
      },
      "armature": {
        "bones": [
          {
            "name": "root",
            "parent": null,
            "head": [0,0,0],
            "tail": [0,0,0.05],
            "world_head": [0,0,0],
            "world_tail": [0,0,0.05],
            "length": 0.05,
            "is_deform": true
          }
        ]
      },
      "pose": {
        "pose_bones": [
          {
            "name": "root",
            "location": [0,0,0],
            "rotation_quaternion": [1,0,0,0],
            "world_matrix": [...]
          }
        ]
      }
    }
  ],
  "spatial": {
    "camera": {"name": "Camera", "location": [5,-5,3], ...},
    "actor_distances": [...]
  }
}
```

### Socket Protocol

| Request | Response |
|---------|----------|
| `{"cmd": "ping"}` | `{"status": "ok", "blender_version": "4.2.0"}` |
| `{"cmd": "inspect", "target": "all", "simplified": false}` | `{"status": "ok", "path": "...", "elapsed_ms": 500}` |

### Analyzer CLI

```bash
blender-state-inspector <raw_state.json> --output-md report.md --output-json report.json
```

For animation-state input, add a temporal clipping gate:

```bash
blender-state-inspector animation_state.json \
  --clip-check \
  --clip-tolerance 0.01 \
  --clip-frame-start 40 \
  --clip-frame-end 96 \
  --output-md report.md \
  --output-json report.json
```

`clip_check.verdict` is `pass` when the requested time window has no detected
clipping. When it is `fail`, the JSON contains the failing frames and spatial
details:

```json
{
  "clip_check": {
    "verdict": "fail",
    "events": [
      {
        "type": "bbox_overlap",
        "frame": 72,
        "actors": ["Character_A", "Prop_B"],
        "overlap": {
          "penetration_depth": 0.034,
          "center": [0.12, -0.03, 0.84],
          "axes": {"x": 0.034, "y": 0.12, "z": 0.31}
        }
      }
    ]
  }
}
```

### Analyzer Output (report.json)

```json
{
  "summary": "Character_A 站立，双脚着地，双臂自然下垂，无异常",
  "actors": [
    {
      "name": "Character_A",
      "morphology": {
        "height": 1.75,
        "shoulder_width": 0.42,
        "arm_length": 0.68,
        "leg_length": 0.85
      },
      "pose_state": "站立",
      "anomalies": [],
      "skeleton_semantics": {
        "root": "root",
        "spine": "spine",
        "head": "head"
      }
    }
  ],
  "spatial": {
    "ground_contact": ["Character_A.left_foot", "Character_A.right_foot"],
    "actor_distances": []
  }
}
```

---

## Development

### Run Tests

```bash
# Unit tests (no Blender needed)
python -m pytest tests/test_*.py --ignore=tests/test_blender_addon.py -v

# Blender headless integration test
python -m pytest tests/test_blender_addon.py -v

# Or run directly in Blender
blender -b -P tests/test_blender_addon.py

# Docker headless test
docker build -t blender-motion-state-inspector .
docker run --rm -v "$(pwd):/workspace" -e PYTHONPATH=/workspace blender-motion-state-inspector:latest blender -b -P tests/test_blender_addon.py
```

### Build Addon Zip

```bash
mkdir -p dist
blender --command extension validate addon --valid-tags=""
blender --command extension build --source-dir addon --output-dir dist --valid-tags=""
blender --command extension validate dist/motion_state_inspector-0.1.1.zip --valid-tags=""
```

### Install for Development

```bash
pip install -e ".[dev]"
```

---

## Agent Skill Integration

This project includes `SKILL.md` for Claude Code / Codex agents.

**Trigger phrases:**
- "inspect blender scene"
- "analyze 3D character"
- "check blender model state"

**Prerequisites for agents:**
1. Blender running with addon enabled
2. Socket server started (N-Panel → Start Server)
3. `blender-state-inspector` CLI installed

**Typical agent workflow:**
1. Agent sends TCP command to `127.0.0.1:9658`
2. Blender collects scene → writes `raw_state.json`
3. Agent runs CLI → generates `report.md` + `report.json`
4. Agent returns summary + full report to user

---

## Current Capabilities

| Feature | Status |
|---------|--------|
| Mesh bbox, vertex count, materials | ✅ |
| Armature bones, hierarchy, world coords | ✅ |
| Pose bones, rotation, location | ✅ |
| Headless `.blend/.glb/.gltf/.fbx` state collection | ✅ |
| Animation range sampling + JSONL diagnostics | ✅ |
| Temporal clipping pass/fail check | ✅ |
| Character vs scene prop classification | ✅ |
| Mixamo namespace/CamelCase skeleton mapping | ✅ |
| Unity Mecanim Humanoid bone name mapping | ✅ |
| Unity scene & camera state C# exporter | ✅ |
| Facing vector inference from torso + toes | ✅ |
| Body proportions (height, arm/leg length) | ✅ |
| Skeleton semantic mapping | ✅ |
| Pose classification (standing/inverted/bent/etc) | ✅ |
| Anomaly detection (inversion, floating, squashing) | ✅ |
| Ground contact detection | ✅ |
| Actor-to-actor distance | ✅ |
| Camera info | ✅ |
| Remote socket trigger | ✅ |
| Markdown + JSON report | ✅ |
| Docker headless test | ✅ |

## Integrating With Agentic 3D Workflows

Use this as the inspection layer between generation and acceptance:

```text
Blender / GLB / FBX / animation source
        ↓
collect_blender_state.py
        ↓
raw_state.json or animation_state.json
        ↓
analyzer CLI
        ↓
LLM-readable facts
        ↓
accept / retry / retarget / camera fix / floor fix / parameter tuning
```

It is useful for:

- avatar retargeting QA
- motion generation acceptance gates
- game character checks
- digital human pipelines
- Blender add-on automation
- multi-actor scene debugging

## Known Limitations / V1 Exclusions

- Animation sampling is frame-step based; no dense curve analysis yet
- Temporal clipping detection currently uses world-space AABB overlap and ground penetration checks; it is not triangle-level mesh intersection yet
- No physics state capture (cloth, soft body)
- No automatic keyframe selection
- No multi-viewpoint screenshots
- No skeleton/bbox/trajectory overlay rendering
- Pose classification uses simplified heuristic

## Roadmap

- [ ] Automatic keyframe selection + screenshots
- [ ] Skeleton/bbox/trajectory overlay rendering
- [ ] Dense animation curve analysis
- [ ] Triangle-level mesh intersection for temporal clipping
- [ ] Shape key values and material diagnostics
- [ ] MCP server protocol support
- [ ] Real-time frame-change listeners
- [ ] Token-based socket authentication
- [ ] Non-Blender DCC support

## License

MIT

## Contributing

Pull requests are welcome. The highest-impact areas are:

- new skeleton naming conventions
- better facing inference
- more robust contact detection
- animation event clustering
- screenshots and overlays

See [CONTRIBUTING.md](CONTRIBUTING.md).
