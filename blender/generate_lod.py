import bpy
from operators import AutomateMacro, OBJECT_OT_generate_lod, WM_OT_exit
import sys


if __name__ == '__main__':
    low_poly_path, output_path, number_of_levels, level_ratio = sys.argv[5:]
    bpy.utils.register_class(OBJECT_OT_generate_lod)
    bpy.utils.register_class(WM_OT_exit)
    bpy.utils.register_class(AutomateMacro)

    generate_lod = AutomateMacro.define('OBJECT_OT_generate_lod')
    generate_lod.properties.low_poly_path = low_poly_path
    generate_lod.properties.output_path = output_path
    generate_lod.properties.number_of_levels = int(number_of_levels)
    generate_lod.properties.level_ratio = float(level_ratio)

    AutomateMacro.define('WM_OT_exit')
    bpy.ops.wm.automation_macro()
