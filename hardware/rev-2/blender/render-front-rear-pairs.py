"""Render assembled and stripped front/rear pairs with the scene's original cameras.

Run in Blender with a LAB Rev 2 scene open and pass an output directory and
a new render revision after --, e.g. -- /tmp/lab-views r1.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

import bpy
from PIL import Image

output_dir, revision = sys.argv[sys.argv.index("--") + 1:]
output_dir = Path(output_dir)
output_dir.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
model = Path(bpy.data.filepath).stem
states = ("assembled", "screen-battery-removed")
deliveries = {state: output_dir / f"{model}-front-rear-{state}-{revision}.jpg"
              for state in states}
for path in deliveries.values():
    if path.exists():
        raise FileExistsError(path)

removable = []
for collection, retained_prefix in (
    ("02 · Panel and front assembly", "Display support"),
    ("04 · Cell and harness", "ADH · double-coated mounting strip"),
):
    objects = list(bpy.data.collections[collection].objects)
    assert sum(obj.name.startswith(retained_prefix) for obj in objects) == 2
    removable.extend(obj for obj in objects if not obj.name.startswith(retained_prefix))
assert all(any(obj.name.startswith(name) for obj in removable)
           for name in ("320 × 320 active area", "Display FPC", "BT1 · formed laminate pouch", "PHR-3"))
assert all(not obj.hide_render for obj in removable)
assert bpy.data.objects["J6 · housing bridge"] not in removable

cameras = {marker.frame: marker.camera for marker in scene.timeline_markers if marker.camera}
scene.render.resolution_x, scene.render.resolution_y = 1280, 1430
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.cycles.use_animated_seed = False
with TemporaryDirectory() as scratch:
    for state in states:
        for obj in removable:
            obj.hide_render = state == "screen-battery-removed"
        pair = Image.new("RGB", (2560, 1430))
        for index, (frame, side) in enumerate(((1, "front"), (2, "rear"))):
            scene.frame_set(frame)
            assert scene.camera == cameras[frame]
            assert scene.camera.name.lower().startswith(side)
            scene.render.filepath = str(Path(scratch) / f"{state}-{side}.png")
            bpy.ops.render.render(write_still=True)
            with Image.open(scene.render.filepath) as image:
                assert image.size == (1280, 1430)
                pair.paste(image.convert("RGB"), (index * 1280, 0))
        with deliveries[state].open("xb") as output:
            pair.save(output, format="JPEG", quality=96, subsampling=0)
        print(deliveries[state], flush=True)
