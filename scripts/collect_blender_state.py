import argparse
import json
import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from addon.collector import collect_animation, collect_scene


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def load_asset(path: str):
    suffix = Path(path).suffix.lower()
    if suffix in {".glb", ".gltf"}:
        clear_scene()
        bpy.ops.import_scene.gltf(filepath=path)
    elif suffix == ".fbx":
        clear_scene()
        bpy.ops.import_scene.fbx(filepath=path)
    elif suffix == ".blend":
        bpy.ops.wm.open_mainfile(filepath=path)
    else:
        raise ValueError(f"Unsupported input asset: {path}")


def main(argv=None):
    if argv is None and "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1:]
    parser = argparse.ArgumentParser(description="Collect Blender model/motion raw state for analyzer CLI.")
    parser.add_argument("--input", required=True, help="Input .blend, .glb, .gltf, or .fbx")
    parser.add_argument("--output", required=True, help="Output raw_state.json path")
    parser.add_argument("--frame", type=int, default=None, help="Single frame to inspect")
    parser.add_argument("--frame-start", type=int, default=None, help="Animation sampling start frame")
    parser.add_argument("--frame-end", type=int, default=None, help="Animation sampling end frame")
    parser.add_argument("--frame-step", type=int, default=1, help="Animation sampling step")
    parser.add_argument("--target", default="all", choices=["all", "selected"])
    parser.add_argument("--full-vertices", action="store_true", help="Include evaluated vertices in raw output")
    args = parser.parse_args(argv)

    load_asset(args.input)
    simplified = not args.full_vertices
    if args.frame_start is not None or args.frame_end is not None:
        raw = collect_animation(
            frame_start=args.frame_start,
            frame_end=args.frame_end,
            step=args.frame_step,
            target=args.target,
            simplified=simplified,
        )
    else:
        if args.frame is not None:
            bpy.context.scene.frame_set(args.frame)
        raw = collect_scene(target=args.target, simplified=simplified)

    Path(args.output).write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
