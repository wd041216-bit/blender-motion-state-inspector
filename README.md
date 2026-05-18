# 3D Motion State Inspector

A tool that converts 3D character models, armatures, actions, materials, and scene relationships into LLM-readable structured state reports.

It answers: What is the current form and posture of this 3D character? How is it moving? Are there any anomalies (inverted joints, floating, squashing)? What is the spatial relationship with the scene, props, and other actors?

**It does NOT generate animations or fix models.** It reports facts. QA, retarget, animation alignment, and story acceptance are downstream applications.

---

## Architecture

```
Blender (3D Viewport)
  ├─ N-Panel UI: "Motion State" tab
  ├─ Collector: bpy scene traversal → raw_state.json
  └─ Socket Server: TCP 127.0.0.1:9658 (remote agent triggering)

CLI Analyzer (pip installable)
  ├─ Loader: raw_state.json → Python dataclasses
  ├─ Morphology: body proportions from bbox + bones
  ├─ Skeleton Semantics: bone name pattern matching
  ├─ Pose Classifier: rule-based posture detection
  ├─ Anomaly Detector: joint inversion, floating, squashing
  ├─ Spatial: distance, orientation, camera calc
  ├─ Contact Detector: ground contact / collision
  └─ Formatter: Markdown + JSON report output
```

---

## Quick Start

### Prerequisites
- Blender 4.0+
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

1. Zip the `addon/` folder: `zip -r addon.zip addon/`
2. In Blender: Edit → Preferences → Add-ons → Install...
3. Select `addon.zip`
4. Enable "3D View: Motion State Inspector"
5. Open the N-Panel (press N) → "Motion State" tab

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

---

## Project Structure

```
blender-motion-state-inspector/
├── addon/                          # Blender addon (runs inside Blender)
│   ├── __init__.py                 # Addon registration
│   ├── collector.py                # bpy scene traversal → raw_state.json
│   ├── panel.py                    # N-Panel UI
│   ├── socket_server.py            # Background TCP server
│   └── utils.py                    # Blender helpers
├── analyzer/                       # CLI analyzer (pip installable)
│   ├── __init__.py
│   ├── cli.py                      # Entry point: blender-state-inspector
│   ├── loader.py                   # raw_state.json → dataclasses
│   ├── morphology.py               # Body proportion calculations
│   ├── skeleton_semantics.py     # Bone naming pattern matching
│   ├── pose_classifier.py          # Posture detection rules
│   ├── anomaly_detector.py         # Issue detection thresholds
│   ├── spatial.py                  # Distance/orientation/camera
│   ├── contact_detector.py         # Ground contact / collision
│   └── formatter.py                # JSON + Markdown output
├── tests/                          # Test suite
│   ├── test_loader.py
│   ├── test_morphology.py
│   ├── test_skeleton_semantics.py
│   ├── test_pose_classifier.py
│   ├── test_anomaly_detector.py
│   ├── test_spatial.py
│   ├── test_contact_detector.py
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
cd addon
zip -r ../motion_state_inspector.zip .
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

## Known Limitations / V1 Exclusions

- No animation curve sampling (current frame only)
- No physics state capture (cloth, soft body)
- No automatic keyframe selection
- No multi-viewpoint screenshots
- No skeleton/bbox/trajectory overlay rendering
- Socket server uses fixed 0.5s wait (needs completion signal)
- Pose classification uses simplified heuristic

## Roadmap

- [ ] MCP Server protocol support
- [ ] Real-time frame-change listeners
- [ ] Animation curve sampling
- [ ] Automatic keyframe selection + screenshots
- [ ] Skeleton/bbox overlay rendering
- [ ] Shape key values
- [ ] Token-based socket authentication
- [ ] Non-Blender DCC support (Maya, etc.)

## License

MIT
