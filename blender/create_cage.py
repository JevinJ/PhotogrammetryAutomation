import bpy
from operators import AutomateMacro, OBJECT_OT_automate_create_cage, WM_OT_exit
import sys


if __name__ == '__main__':
    high_poly_path, low_poly_path, cage_path = sys.argv[5:]
    bpy.utils.register_class(OBJECT_OT_automate_create_cage)
    bpy.utils.register_class(WM_OT_exit)
    bpy.utils.register_class(AutomateMacro)

    create_cage = AutomateMacro.define('OBJECT_OT_automate_create_cage')
    create_cage.properties.high_poly_path = high_poly_path
    create_cage.properties.low_poly_path = low_poly_path
    create_cage.properties.cage_path = cage_path
    AutomateMacro.define('WM_OT_exit')
    bpy.ops.wm.automation_macro()

