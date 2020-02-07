import bpy
from operators import AutomateMacro, UV_OT_automate_unwrap, WM_OT_exit
import sys


if __name__ == '__main__':
    filepath = sys.argv[-1]
    bpy.utils.register_class(UV_OT_automate_unwrap)
    bpy.utils.register_class(WM_OT_exit)
    bpy.utils.register_class(AutomateMacro)

    unwrap = AutomateMacro.define('UV_OT_automate_unwrap')
    unwrap.properties.filepath = filepath
    AutomateMacro.define('WM_OT_exit')
    bpy.ops.wm.automation_macro()