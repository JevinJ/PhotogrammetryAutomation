import bpy
from operators import AutomateMacro, OBJECT_OT_automate_remesh, WM_OT_exit
import sys


if __name__ == '__main__':
    high_poly_path, low_poly_path, target_count, adaptive_size, hard_edges_by_angle, \
    disallow_intersecting = sys.argv[5:]

    bpy.utils.register_class(OBJECT_OT_automate_remesh)
    bpy.utils.register_class(WM_OT_exit)
    bpy.utils.register_class(AutomateMacro)

    remesh = AutomateMacro.define('OBJECT_OT_automate_remesh')
    remesh.properties.high_poly_path = high_poly_path
    remesh.properties.low_poly_path = low_poly_path
    remesh.properties.target_count = int(target_count)
    remesh.properties.adaptive_size = int(adaptive_size)
    remesh.properties.hard_edges_by_angle = bool(hard_edges_by_angle)
    remesh.properties.disallow_intersecting = bool(disallow_intersecting)
    AutomateMacro.define('WM_OT_exit')
    bpy.ops.wm.automation_macro()