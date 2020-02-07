# PhotogrammetryAutomation
API to automatically remesh, unwrap, pack, generate a baking cage, and bake textures of photoscanned meshes in Blender.

This is for my own use, but if you come across this and want to try it out you are free to do so.
If you have any issues, let me know.

### Requirements
* [Blender 2.8+](https://www.blender.org)
* [QuadRemesher by Exoside](https://exoside.com/quadremesher)
* [UVPackMaster2 Pro or Standard by glukoz](https://gumroad.com/l/uvpackmaster2)
* [uv_auto_seam_unwrap by vilemduha](https://github.com/vilemduha/blender-addons-vilem-duha/blob/master/addons/uv_auto_seam_unwrap.py)

### Installing
1. Install Blender 2.8+
2. Install QuadRemesher, UVPackMaster2, uv_auto_seam_unwrap according to their guides
   and/or [blender documentation](https://docs.blender.org/manual/en/latest/editors/preferences/addons.html).
   For UVPackMaster you must remember to set up the license file.
3. Install operators.py in the PhotogrammetryAutomation/blender folder in this project,
   as a [blender add-on](https://docs.blender.org/manual/en/latest/editors/preferences/addons.html).

### Usage
```python
from blender import Blender

# Get a list of paths to existing high poly meshes. (Absolute, includes extension)
high_poly_paths = ...

# Create output paths, or paths to existing to low poly/cage meshes. (Absolute, includes extension)
low_poly_paths = ...
cage_paths = ...

# Create a list of texture output paths, if you want to bake textures.
texture_output_paths = ...

# Create a list of base texture names, for example a normal map for "MyObject", gives "MyObject_normal"
base_texture_names = ...

# Absolute path to your blender folder
blender_path = r'C:\Program Files\Blender Foundation\Blender 2.81'
with Blender(blender_path) as blender:
    for i in range(len(high_poly_paths)):
        high_poly_path = high_poly_paths[i]
        low_poly_path = low_poly_paths[i]
        cage_path = cage_paths[i]
        texure_path = texture_output_paths[i]
        base_texture_name = base_texture_names[i]
        
        # Remesh using Quad Remesher
        blender.remesh(high_poly_path, low_poly_path, target_count=5000, adaptive_size=65)
        
        # Unwrap using uv_auto_seam_unwrap
        blender.unwrap(low_poly_path)
        
        # Pack using UVPackMaster, give an island margin for texture baking.
        blender.pack(low_poly_path, margin=16/2048)
        
        # Create a baking cage using the low poly
        blender.create_cage(high_poly_path, low_poly_path, cage_path)
        
        # Bake textures using blender, map_types is a space separated string list of
        # any number of the following:
        # COMBINED, AO, SHADOW, NORMAL, OS_NORMAL, UV, ROUGHNESS, EMIT,
        # ENVIRONMENT, DIFFUSE, GLOSSY, TRANSMISSION, SUBSURFACE
        blender.bake(high_poly_path, low_poly_path, cage_path, texure_path, base_texture_name,
                     width=2048, height=2048, margin=16, map_types='NORMAL DIFFUSE')

