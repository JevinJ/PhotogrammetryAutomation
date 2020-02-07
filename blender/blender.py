import logging
import os
from pathlib import Path
from pprint import pformat
from subprocess import DEVNULL, PIPE, Popen


logging.basicConfig(level=logging.DEBUG)


class SelfIntersectingMeshError(Exception): pass


class Blender:
    def __init__(self, blender_path: str, reprocess_existing=True):
        self.blender_path = os.path.join(blender_path, 'blender.exe')
        self.command_count = 0
        self.reprocess_existing = reprocess_existing

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def remesh(self, high_poly_path, low_poly_path, target_count=5000, adaptive_size=50,
               disallow_intersection=True):
        """
        :param high_poly_path: Absolute path of the high poly .obj to remesh.
        :param low_poly_path: Absolute path to export the resulting .obj to.
        :param target_count: Desired number of quads.
        :param adaptive_size: How much quad size adapts locally to curvature. 0 gives uniform
         quad size.
        :param disallow_intersection: If resulting mesh self intersects, throw SelfIntersectingMeshError.
        """
        self._raise_path_not_exists(high_poly_path)
        if self.reprocess_existing or not Path(low_poly_path).exists():
            logging.info('START REMESH')
            process = self._run_process('remesh.py', high_poly_path, low_poly_path, target_count,
                                        adaptive_size, disallow_intersection)
            if process.returncode == 2 and disallow_intersection:
                raise SelfIntersectingMeshError('Remesh created a self intersecting mesh, try increasing'
                                                ' target_count or adaptive_size')
            logging.info('REMESH OK')
        else:
            logging.info(f'SKIPPING REMSESH FOR: {low_poly_path}. ALREADY EXISTS')

    def unwrap(self, filepath):
        """
        :param filepath: Absolute path of the mesh to unwrap UVs for.
        """
        logging.info('START UNWRAP')
        self._raise_path_not_exists(filepath)
        process = self._run_process('unwrap.py', filepath)
        logging.info('UNWRAP OK')

    def pack(self, filepath, margin: float, heuristic_search_time: int=10):
        """
        :param filepath: Absolute path of the mesh which has active UVs to pack.
        :param margin: Pixel margin/UV spacing used to bake texture.
        :heuristic_search_time: Amount of time to search for a better pack.
        """
        logging.info('START PACK')
        self._raise_path_not_exists(filepath)
        process = self._run_process('pack.py', filepath, margin, heuristic_search_time)
        logging.info('PACK OK')

    def create_cage(self, high_poly_path, low_poly_path, cage_path):
        """
        :param high_poly_path: Absolute path to the high poly .obj.
        :param low_poly_path: Absolute path to the low poly .obj.
        :param cage_path: Absolute path to export the cage .obj to.
        """
        if self.reprocess_existing or not Path(cage_path).exists():
            logging.info('START CREATE CAGE')
            self._raise_path_not_exists(high_poly_path, low_poly_path)
            process = self._run_process('create_cage.py', high_poly_path, low_poly_path, cage_path)
            if process.returncode == 2:
                raise SelfIntersectingMeshError(f'Low poly at: {low_poly_path} is self intersecting.'
                                                ' This must be fixed before creating a cage.')
            logging.info('CREATE CAGE OK')
        else:
            logging.info(f'SKIPPING CREATE CAGE FOR: {cage_path}. ALREADY EXISTS')

    def bake(self, high_poly_path, low_poly_path, cage_path, texture_output_path, base_texture_name,
             map_types: str, width: int, height: int, margin: int, tile_x=256, tile_y=256):
        """
        :param high_poly_path: Absolute path to the high poly .obj.
        :param low_poly_path: Absolute path to the low poly .obj.
        :param cage_path: Absolute path to the cage .obj.
        :param texture_output_path: Absolute path to save textures to.
        :param base_texture_name: Base name for textures.
         For example: a normal map for 'MyObject', gives 'MyObject_normal'.
        :param map_types: Space separated string list of textures to bake.
         For example: 'NORMAL OS_NORMAL DIFFUSE AO'.
        :param width: Pixel width of textures.
        :param height: Pixel height of textures.
        :param margin: Pixel/UV margin of textures.
        :param tile_x: Horizontal tile size to use while baking.
        :param tile_y: Vertical tile size to use while baking.
        """
        logging.info('START BAKE')
        self._raise_path_not_exists(high_poly_path, low_poly_path, cage_path, texture_output_path)
        process = self._run_process('bake.py', high_poly_path, low_poly_path, cage_path,
                                    texture_output_path, base_texture_name, str(width), str(height),
                                    str(margin), map_types)
        if process.returncode != 0:
            raise RuntimeError(process.stderr)
        logging.info('BAKE OK')

    def _run_process(self, python_filename, *args) -> Popen:
        self.command_count += 1
        args = [self.blender_path, '--disable-abort-handler', '--python', python_filename, '--'] + list(args)
        args = list(map(str, args))
        process = Popen(args=args)
        process.wait()
        return process

    def _fail_process(self, process_type, args, reason):
        self.failed_commands.append((process_type, args, reason))
        logging.error(f'{process_type} FAIL')
        logging.error(pformat(args))
        logging.error(f'REASON: {reason}')

    def _raise_path_not_exists(self, *paths):
        for path in paths:
            if not Path(path).exists():
                raise ValueError(f'Path: {path} does not exist.')
