bl_info = {
    "name": "Motion State Inspector",
    "author": "...",
    "version": (0, 1, 1),
    "blender": (4, 0, 0),
    "location": "View3D > N-Panel > Motion State",
    "description": "Inspect 3D character state and export structured reports for LLM consumption",
    "category": "3D View",
    "support": "COMMUNITY",
}

import bpy

from .panel import register as panel_register, unregister as panel_unregister

def register():
    panel_register()

def unregister():
    panel_unregister()
