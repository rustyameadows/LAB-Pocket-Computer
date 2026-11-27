"""Sample both outer faces of the assembled v9b Blender model in PCB coordinates.

Invoke Blender with the original v9b scene, this script and -- output-directory.
The two 0.10 mm grids store outward height from the central print seam.
"""
from pathlib import Path
import sys

import bpy
from mathutils.bvhtree import BVHTree
import numpy as np

out = Path(sys.argv[sys.argv.index('--') + 1]); out.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
deps = bpy.context.evaluated_depsgraph_get()
root = bpy.data.objects['LAB · assembled device']
vertices, polygons = [], []
for obj in root.children_recursive:
    if obj.hide_render or obj.type not in {'MESH', 'CURVE', 'FONT'}:
        continue
    if obj.name.startswith('LAB-Pocket-R2-v9b_'):
        continue   # The exact PCB outline and printable marks are drawn separately.
    item = obj.evaluated_get(deps)
    mesh = item.to_mesh()
    mesh.calc_loop_triangles()
    start = len(vertices)
    vertices.extend([item.matrix_world @ v.co for v in mesh.vertices])
    polygons.extend([tuple(start + i for i in tri.vertices) for tri in mesh.loop_triangles])
    item.to_mesh_clear()
tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=True)
for name, z, direction in [('front', 20, -1), ('rear', -20, 1)]:
    height = np.full((1521, 741), .75, dtype=np.float32)
    for j in range(height.shape[0]):
        y = j / 10 - 79
        for i in range(height.shape[1]):
            hit, _, _, _ = tree.ray_cast((i / 10 - 37, y, z), (0, 0, direction), 45)
            if hit is not None:
                h = (hit.z - .8) * -direction
                if h > height[j, i]:
                    height[j, i] = h
    np.save(out / (name + '.npy'), height)
    print(name, 'maximum height above join', height.max(), flush=True)
