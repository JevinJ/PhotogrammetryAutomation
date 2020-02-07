import bpy
from operators import AutomateMacro, OBJECT_OT_automate_bake, WM_OT_exit
import sys


if __name__ == '__main__':
    high_poly_path, low_poly_path, cage_path, texture_output_path, base_texture_name, \
    map_types, width, height, margin, tile_x, tile_y = sys.argv[5:]

    bpy.utils.register_class(OBJECT_OT_automate_bake)
    bpy.utils.register_class(WM_OT_exit)
    bpy.utils.register_class(AutomateMacro)

    bake = AutomateMacro.define('OBJECT_OT_automate_bake')
    bake.properties.high_poly_path = high_poly_path
    bake.properties.low_poly_path = low_poly_path
    bake.properties.cage_path = cage_path
    bake.properties.output_path = texture_output_path
    bake.properties.base_texture_name = base_texture_name
    bake.properties.map_types = map_types
    bake.properties.width = int(width)
    bake.properties.height = int(height)
    bake.properties.margin = float(margin)
    bake.properties.tile_x = int(tile_x)
    bake.properties.tile_y = int(tile_y)
    AutomateMacro.define('WM_OT_exit')
    bpy.ops.wm.automation_macro()
