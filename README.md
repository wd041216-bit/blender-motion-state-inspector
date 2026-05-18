# 3D Motion State Inspector

A tool that converts 3D character models, armatures, actions, materials, and scene relationships into LLM-readable structured state reports.

## Quick Start

1. Install the analyzer CLI:
   pip install -e .

2. Install the Blender addon:
   - In Blender: Edit > Preferences > Add-ons > Install
   - Select `addon/` folder as a zip (zip the folder first)
   - Enable "Motion State Inspector"

3. Use from Blender:
   - N-Panel > Motion State > Inspect Scene

4. Use from Claude Code / Codex:
   - The SKILL.md exposes `inspect_blender_scene`
