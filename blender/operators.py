import bmesh
import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, CollectionProperty, IntProperty, FloatProperty, StringProperty
from mathutils import bvhtree, Vector
import os
from pathlib import Path
import sys
from uvpackmaster2.operator import UVP2_OT_PackOperatorGeneric


def name_from_path(filepath: str):
    return Path(filepath).stem


def set_active_by_name(name):
    bpy.context.view_layer.objects.active = bpy.data.objects[name]


def rename_active(name):
    bpy.context.active_object.name = name
    bpy.context.active_object.data.name = name
    bpy.context.active_object.active_material.name = name


def export_selected(filepath):
    exporters = {'.obj': bpy.ops.export_scene.obj, '.fbx': bpy.ops.export_scene.fbx}
    extension = Path(filepath).suffix
    exporters[extension](filepath=filepath, use_selection=True, check_existing=True)


def import_from_path(filepath):
    bpy.ops.import_scene.obj(filepath=filepath)


def mesh_self_intersects(bmesh) -> bool:
    tree = bvhtree.BVHTree.FromBMesh(bmesh, epsilon=0.00001)
    return len(tree.overlap(tree)) > 0


def bmesh_from_mesh(mesh_data):
    bm = bmesh.new()
    bm.from_mesh(mesh_data)
    return bm


def smooth_bmesh(bmesh):
    for face, edge in zip(bmesh.faces, bmesh.edges):
        face.smooth = True
        edge.smooth = True


def update_obj_from_bmesh(obj, bmesh):
    bmesh.to_mesh(obj.data)
    obj.data.update()


def output_modal(func, output: set):
    """Updates output with the result of func, a modal which returns a set.
     Cheap way to monitor the modal result of a bpy.Operator."""
    def wrap(self, context, event):
        result = func(self, context, event)
        output.update(result)
        return result
    return wrap


class AutomateMacro(bpy.types.Macro):
    bl_idname = "wm.automation_macro"
    bl_label = "Automation Macro"


class OBJECT_OT_automate_remesh(Operator):
    bl_idname = 'object.automate_remesh'
    bl_label = 'Automate Remesh'
    high_poly_path: StringProperty()
    low_poly_path: StringProperty()
    target_count = IntProperty(default=5000)
    adaptive_size = IntProperty(default=50)
    disallow_intersecting = BoolProperty(default=True)

    def execute(self, context):
        import_from_path(self.high_poly_path)
        high_poly_name = name_from_path(self.high_poly_path)
        set_active_by_name(high_poly_name)

        props = context.scene.qremesher
        props.target_count = self.target_count
        props.adaptive_size = self.adaptive_size

        context.window_manager.modal_handler_add(self)
        return bpy.ops.qremesher.remesh()

    def modal(self, context, event):
        if len(bpy.data.objects) == 2:
            low_poly_name = name_from_path(self.low_poly_path)
            # Retopo is already selected by QuadRemesher
            rename_active(low_poly_name)
            low_poly_obj = context.active_object
            low_poly_bmesh = bmesh_from_mesh(low_poly_obj.data)
            if self.disallow_intersecting and mesh_self_intersects(low_poly_bmesh):
                sys.exit(2)

            smooth_bmesh(low_poly_bmesh)
            bmesh.ops.triangulate(low_poly_bmesh, faces=low_poly_bmesh.faces,
                                  quad_method='BEAUTY', ngon_method='BEAUTY')
            update_obj_from_bmesh(low_poly_obj, low_poly_bmesh)
            export_selected(self.low_poly_path)
            return {'FINISHED'}
        return {'PASS_THROUGH'}


class UV_OT_automate_unwrap(Operator):
    bl_idname = 'uv.automate_unwrap'
    bl_label = 'Automate Unwrap'
    filepath: StringProperty()

    def execute(self, context):
        import_from_path(self.filepath)
        object_name = name_from_path(self.filepath)
        set_active_by_name(object_name)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.uv.auto_seams_unwrap(grow_iterations=5, merge_iterations=5,
                                     small_island_threshold=300)
        export_selected(self.filepath)
        return {'FINISHED'}


class UV_OT_automate_pack(Operator):
    bl_idname = 'uv.automate_pack'
    bl_label = 'Automate Pack'
    filepath = StringProperty()
    margin = FloatProperty(default=0.005)
    heuristic_search_time = IntProperty(default=10)

    def execute(self, context):
        import_from_path(self.filepath)
        object_name = name_from_path(self.filepath)
        set_active_by_name(object_name)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.uv.select_all(action='SELECT')

        uvp_properties = context.scene.uvp2_props
        uvp_properties.margin = self.margin
        uvp_properties.heuristic_enable = True
        uvp_properties.heuristic_search_time = self.heuristic_search_time

        self.uvp_modal_output = set()
        UVP2_OT_PackOperatorGeneric.modal = output_modal(
            UVP2_OT_PackOperatorGeneric.modal, self.uvp_modal_output)
        context.window_manager.modal_handler_add(self)
        return bpy.ops.uvpackmaster2.uv_pack()

    def modal(self, context, event):
        if 'FINISHED' in self.uvp_modal_output:
            export_selected(self.filepath)
            return {'FINISHED'}
        return {'RUNNING_MODAL'}


class OBJECT_OT_automate_create_cage(Operator):
    bl_idname = 'object.automate_create_cage'
    bl_label = 'Create Cage'
    high_poly_path = StringProperty()
    low_poly_path = StringProperty()
    cage_path = StringProperty()
    _CAGE_PADDING = .0001

    def execute(self, context):
        import_from_path(self.high_poly_path)
        import_from_path(self.low_poly_path)

        high_poly_name = name_from_path(self.high_poly_path)
        low_poly_name = name_from_path(self.low_poly_path)
        cage_name = name_from_path(self.cage_path)

        high_poly_obj = bpy.data.objects[high_poly_name]
        low_poly_obj = bpy.data.objects[low_poly_name]

        high_poly_obj.select_set(True)
        low_poly_obj.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        context.view_layer.objects.active = low_poly_obj

        bpy.ops.object.select_all(action='DESELECT')
        low_poly_obj.select_set(True)
        bpy.ops.object.duplicate()
        cage_obj = context.object

        high_poly_bmesh = bmesh_from_mesh(high_poly_obj.data)
        cage_bmesh = bmesh_from_mesh(cage_obj.data)
        if mesh_self_intersects(cage_bmesh):
            sys.exit(2)

        # baseline inflation for low poly/cage intersections
        for face in cage_bmesh.faces:
            face_normal = face.normal.copy()
            for vert in face.verts:
                vert.co += face_normal * self._CAGE_PADDING
        update_obj_from_bmesh(cage_obj, cage_bmesh)
        cage_obj.hide_set(True)

        scene = context.scene
        view_layer = context.view_layer

        # raycast & move cage faces to high poly
        cage_bmesh.faces.ensure_lookup_table()
        cage_bmesh.faces.index_update()
        cage_bmesh.verts.ensure_lookup_table()
        for face in cage_bmesh.faces:
            ray_origin = face.calc_center_median_weighted()
            # raycast to search for high poly face
            hit, hit_point, hit_normal, hit_index, hit_object, _ = scene.ray_cast(
                view_layer, origin=ray_origin, direction=face.normal)
            if hit and hit_object is low_poly_obj:
                if not self._normals_are_facing(face.normal, hit_normal):
                    # point inside low poly, recast from hit point
                    hit, hit_point, hit_normal, _, hit_object, _ = scene.ray_cast(
                        view_layer, origin=hit_point, direction=face.normal)
            if hit and hit_object is high_poly_obj:
                if not self._normals_are_facing(face.normal, hit_normal):
                    face_normal = face.normal.copy()
                    for vert in face.verts:
                        distance = (hit_point - vert.co).dot(face_normal)
                        if distance > 0:
                            vert.co += face_normal * (distance + self._CAGE_PADDING)

        self._inflate_beyond_intersection(cage_bmesh, high_poly_bmesh)

        update_obj_from_bmesh(cage_obj, cage_bmesh)
        set_active_by_name(cage_obj.name)
        rename_active(cage_name)
        bpy.ops.object.select_all(action='DESELECT')
        cage_obj.hide_set(False)
        cage_obj.select_set(True)
        cage_obj.data.materials.clear()
        export_selected(self.cage_path)
        return {'FINISHED'}

    def _inflate_beyond_intersection(self, bmesh_a, bmesh_b):
        bmesh_a.faces.ensure_lookup_table()
        bmesh_b.faces.ensure_lookup_table()
        bmesh_a_tree = bvhtree.BVHTree.FromBMesh(bmesh_a)
        bmesh_b_tree = bvhtree.BVHTree.FromBMesh(bmesh_b)

        intersecting_polygons = bmesh_a_tree.overlap(bmesh_b_tree)
        while intersecting_polygons:
            intersect_len = len(intersecting_polygons)
            for a_index, b_index in intersecting_polygons:
                a_face = bmesh_a.faces[a_index]
                b_face = bmesh_b.faces[b_index]

                a_face_normal = a_face.normal.copy()
                for a_vert in a_face.verts:
                    for b_vert in b_face.verts:
                        distance = (b_vert.co - a_vert.co).dot(a_face_normal)
                        if distance > 0:
                            a_vert.co += a_face_normal * (distance + self._CAGE_PADDING)

            bmesh_a_tree = bvhtree.BVHTree.FromBMesh(bmesh_a)
            intersecting_polygons = bmesh_a_tree.overlap(bmesh_b_tree)
            if len(intersecting_polygons) == intersect_len:
                # mesh is stable, remaining intersections shouldn't interfere with baking
                return

    def _normals_are_facing(self, normal_a: Vector, normal_b: Vector) -> bool:
        return normal_a.dot(normal_b) < 0

    def _area(self, p1: Vector, p2: Vector, p3: Vector) -> float:
        """Calculate area of triangle using points."""
        v1 = (p2 - p1)
        v2 = (p3 - p1)
        return ((v1.x * v2.y) - (v1.y * v2.x)) / 2


class OBJECT_OT_automate_bake(Operator):
    bl_idname = 'object.automate_bake'
    bl_label = 'Automate Texture Bake'
    width: IntProperty()
    height: IntProperty()
    tile_x: IntProperty(default=256)
    tile_y: IntProperty(default=256)
    margin: IntProperty()
    output_path: StringProperty()
    high_poly_path: StringProperty()
    low_poly_path: StringProperty()
    cage_path: StringProperty()
    base_texture_name: StringProperty()
    map_types: StringProperty()

    def execute(self, context):
        import_from_path(self.high_poly_path)
        import_from_path(self.low_poly_path)
        import_from_path(self.cage_path)

        high_poly_name = name_from_path(self.high_poly_path)
        low_poly_name = name_from_path(self.low_poly_path)
        self.cage_name = name_from_path(self.cage_path)

        high_poly_obj = bpy.data.objects[high_poly_name]
        low_poly_obj = bpy.data.objects[low_poly_name]

        for edge in list(high_poly_obj.data.edges) + list(low_poly_obj.data.edges):
            edge.use_edge_sharp = False

        bpy.ops.object.select_all(action='DESELECT')
        high_poly_obj.select_set(True)
        low_poly_obj.select_set(True)
        bpy.ops.object.shade_smooth()
        set_active_by_name(low_poly_name)

        low_poly_mat = low_poly_obj.active_material
        bpy.data.materials.remove(low_poly_mat, do_unlink=True)
        low_poly_mat = bpy.data.materials.new(low_poly_name)
        low_poly_obj.active_material = low_poly_mat

        low_poly_mat.use_nodes = True
        nodes = low_poly_mat.node_tree.nodes
        node_links = low_poly_mat.node_tree.links
        principled_node = nodes['Principled BSDF']

        render_settings = context.scene.render
        render_settings.tile_x = self.tile_x
        render_settings.tile_y = self.tile_y
        image_settings = render_settings.image_settings
        image_settings.color_depth = '16'
        image_settings.file_format = 'PNG'
        image_settings.color_mode = 'RGBA'
        image_settings.compression = 15
        image_settings.quality = 100

        for map_type in self.map_types.split():
            image_name = f'{self.base_texture_name}_{map_type.lower()}.png'
            image = bpy.data.images.new(image_name, alpha=True, width=self.width, height=self.height)
            image.filepath = os.path.join(self.output_path, image_name)

            image_node = nodes.new(type='ShaderNodeTexImage')
            image_node.image = image
            nodes.active = image_node

            if map_type == 'OS_NORMAL':
                self._bake(map_type='NORMAL', normal_space='OBJECT')
            else:
                self._bake(map_type)
            image.save()

            if map_type == 'DIFFUSE':
                node_links.new(image_node.outputs['Color'], principled_node.inputs['Base Color'])
            elif map_type == 'NORMAL':
                normal_map_node = nodes.new('ShaderNodeNormalMap')
                node_links.new(image_node.outputs['Color'], normal_map_node.inputs['Color'])
                node_links.new(normal_map_node.outputs['Normal'], principled_node.inputs['Normal'])

        bpy.ops.object.select_all(action='DESELECT')
        low_poly_obj.select_set(True)
        export_selected(self.low_poly_path)
        return {'FINISHED'}

    def _bake(self, map_type, normal_space='TANGENT'):
        bpy.ops.object.bake(type=map_type, use_selected_to_active=True, cage_object=self.cage_name,
                            use_cage=True, margin=self.margin, normal_space=normal_space,
                            pass_filter={'COLOR'})


class OBJECT_OT_generate_lod(Operator):
    bl_idname = 'object.generate_lod'
    bl_label = 'Automate LOD Creation'
    low_poly_path: StringProperty()
    output_path: StringProperty()
    number_of_levels: IntProperty(default=1)
    level_ratio: FloatProperty(default=.5)

    def execute(self, context):
        import_from_path(self.low_poly_path)
        object_name = name_from_path(self.output_path)

        low_poly_obj = context.selected_objects[0]
        low_poly_obj.name = f'{object_name}_LOD0'
        low_poly_obj.data.name = f'{object_name}_LOD0'
        low_poly_obj.active_material.name = object_name

        current_ratio = self.level_ratio
        for i in range(1, self.number_of_levels):
            bpy.ops.object.select_all(action='DESELECT')
            low_poly_obj.select_set(True)
            set_active_by_name(low_poly_obj.name)
            bpy.ops.object.duplicate()

            new_lod = context.active_object
            new_lod.name = f'{object_name}_LOD{i}'
            new_lod.data.name = f'{object_name}_LOD{i}'

            decimate = new_lod.modifiers.new(f'decimate', type='DECIMATE')
            decimate.ratio = current_ratio
            current_ratio *= self.level_ratio

        bpy.ops.export_scene.fbx(filepath=self.output_path)
        return {'FINISHED'}


class WM_OT_exit(Operator):
    bl_idname = 'wm.exit'
    bl_label = 'Close Blender'

    def execute(self, context):
        sys.exit(0)


