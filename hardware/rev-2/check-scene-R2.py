"""Run inside Blender with the Rev 2 assembly open."""
from math import isclose
from pathlib import Path
import bpy
from mathutils import Vector

scene = bpy.context.scene
scene.frame_set(1)
root = bpy.data.objects['LAB · assembled device']
deps = bpy.context.evaluated_depsgraph_get()
objects = {obj.name: obj for obj in root.children_recursive if obj.type in {'MESH','CURVE','FONT'}}


def box(obj):
    evaluated = obj.evaluated_get(deps)
    points = [evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box]
    return tuple(tuple(fn(p[i] for p in points) for i in range(3)) for fn in (min,max))


def matches(values, expected, tolerance=.012):
    assert all(isclose(v,t,abs_tol=tolerance) for v,t in zip(values,expected)), (values,expected)


assert not any(any(word in name.lower() for word in ('guard','bumpon','sj5302','stud')) for name in objects)
boxes = {name: box(obj) for name,obj in objects.items()}
low = [min(b[0][i] for b in boxes.values()) for i in range(3)]
high = [max(b[1][i] for b in boxes.values()) for i in range(3)]
matches([b-a for a,b in zip(low,high)], [74,146,14.967])
for name in ('Lens pupil','320 × 320 active area'):
    a,b=boxes[name]
    matches([(a[i]+b[i])/2 for i in (0,1)], [0,35.94])
pack=[bounds for name,bounds in boxes.items() if name.startswith('BT1 ·')]
matches([max(b[1][i] for b in pack)-min(b[0][i] for b in pack) for i in range(3)], [59.5,78.5,7.9])
strips=[b for name,b in boxes.items() if name.startswith('ADH ·')]
assert len(strips)==2
for a,b in strips:
    matches([b[i]-a[i] for i in range(3)],[20,55,.17])
    matches([a[2],b[2]],[-.17,0.0])
leads=[obj for name,obj in objects.items() if name.startswith('BT1 lead')]
assert len(leads)==2
for obj in leads:
    points=[obj.matrix_world@Vector(p.co[:3]) for p in obj.data.splines[0].points]
    matches([sum((b-a).length for a,b in zip(points,points[1:]))],[70])
for image in bpy.data.images:
    if image.source=='FILE':
        assert image.packed_file is not None, image.name
print('Verified the assembled envelope, optical axis, bonded pack, both 70 mm leads and packed artwork.')
