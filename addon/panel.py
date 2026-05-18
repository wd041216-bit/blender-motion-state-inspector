import bpy

from .collector import collect_scene, write_raw_state
from .socket_server import is_running, start_server, stop_server


class MOTIONSTATE_OT_inspect_scene(bpy.types.Operator):
    bl_idname = "motionstate.inspect_scene"
    bl_label = "Inspect Scene"
    bl_options = {"REGISTER"}

    target: bpy.props.EnumProperty(
        name="Target",
        items=[("all", "All", ""), ("selected", "Selected", "")],
        default="all",
    )
    simplified: bpy.props.BoolProperty(name="Simplified", default=False)

    def execute(self, context):
        raw = collect_scene(target=self.target, simplified=self.simplified)
        path = write_raw_state(raw)
        self.report({"INFO"}, f"State written to {path}")
        return {"FINISHED"}


class MOTIONSTATE_PT_panel(bpy.types.Panel):
    bl_label = "Motion State"
    bl_idname = "MOTIONSTATE_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Motion State"

    def draw(self, context):
        layout = self.layout
        layout.operator("motionstate.inspect_scene", text="Inspect Scene")
        layout.prop(context.scene, "motionstate_target")
        layout.prop(context.scene, "motionstate_simplified")
        running = is_running()
        if running:
            layout.label(text="Server: Running")
            layout.operator("motionstate.stop_server", text="Stop Server")
        else:
            layout.label(text="Server: Stopped")
            layout.operator("motionstate.start_server", text="Start Server")


class MOTIONSTATE_OT_start_server(bpy.types.Operator):
    bl_idname = "motionstate.start_server"
    bl_label = "Start Server"
    bl_options = {"REGISTER"}

    def execute(self, context):
        ok = start_server()
        if ok:
            self.report({"INFO"}, "Server started on 127.0.0.1:9658")
        else:
            self.report({"WARNING"}, "Server already running")
        return {"FINISHED"}


class MOTIONSTATE_OT_stop_server(bpy.types.Operator):
    bl_idname = "motionstate.stop_server"
    bl_label = "Stop Server"
    bl_options = {"REGISTER"}

    def execute(self, context):
        ok = stop_server()
        if ok:
            self.report({"INFO"}, "Server stopped")
        else:
            self.report({"WARNING"}, "Server not running")
        return {"FINISHED"}


classes = [
    MOTIONSTATE_OT_inspect_scene,
    MOTIONSTATE_OT_start_server,
    MOTIONSTATE_OT_stop_server,
    MOTIONSTATE_PT_panel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.motionstate_target = bpy.props.EnumProperty(
        name="Target", items=[("all", "All", ""), ("selected", "Selected", "")], default="all"
    )
    bpy.types.Scene.motionstate_simplified = bpy.props.BoolProperty(name="Simplified", default=False)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.motionstate_target
    del bpy.types.Scene.motionstate_simplified
