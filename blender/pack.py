import bpy
from operators import AutomateMacro, UV_OT_automate_pack, WM_OT_exit
import sys


if __name__ == '__main__':
    filepath, margin = sys.argv[5:]
    bpy.utils.register_class(UV_OT_automate_pack)
    bpy.utils.register_class(AutomateMacro)
    bpy.utils.register_class(WM_OT_exit)

    pack = AutomateMacro.define('UV_OT_automate_pack')
    pack.properties.filepath = filepath
    pack.properties.margin = float(margin)
    AutomateMacro.define('WM_OT_exit')
    bpy.ops.wm.automation_macro()
