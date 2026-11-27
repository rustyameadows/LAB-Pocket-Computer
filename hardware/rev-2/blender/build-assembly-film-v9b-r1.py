"""Build the editable v9b assembly film from the finished v9b product scene.

blender -b LAB-Pocket-R2-v9b.blend -P build-film.py -- output-directory
"""
from collections import defaultdict
from pathlib import Path
import math
import re
import sys

import bpy
from mathutils import Matrix, Vector

OUT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
NAME = "LAB-Pocket-R2-v9b-assembly-film-r1"
destination = OUT / (NAME + ".blend")
if destination.exists():
    raise FileExistsError(destination)

scene = bpy.context.scene
scene.frame_set(1)
root = bpy.data.objects["LAB · assembled device"]
parts = list(root.children)
original = {o.name: o.matrix_world.copy() for o in parts}
root.animation_data_clear()
root.location = (0, 0, 0)
root.rotation_euler = (0, 0, 0)
floor = bpy.data.objects["Studio sweep"]
floor.animation_data_clear()
floor.location.z = -9.0
for marker in list(scene.timeline_markers):
    scene.timeline_markers.remove(marker)

rig = bpy.data.collections.new("08 · Assembly animation")
captions = bpy.data.collections.new("09 · Group captions")
scene.collection.children.link(rig)
scene.collection.children.link(captions)
camera_data = bpy.data.cameras.new("Assembly orthographic")
camera = bpy.data.objects.new("Assembly camera", camera_data)
rig.objects.link(camera)
camera_data.type = "ORTHO"
camera_data.ortho_scale = 309
camera_data.clip_end = 1200
camera_data.lens = 53
direction = Vector((0.235, -0.50, 1.48)).normalized()
camera.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
right = camera.rotation_euler.to_matrix() @ Vector((1, 0, 0))
up = camera.rotation_euler.to_matrix() @ Vector((0, 1, 0))
aim = Vector((0, -2.7, 0.3)) - right * 19
camera.location = aim + direction * 380
scene.camera = camera

# Stage boundaries are also markers in the delivered Blender timeline.
stages = [
    ("board", "Bare PCB", 1, 33),
    ("radio", "Radio & microphones", 34, 77),
    ("ports", "Ports & card sockets", 78, 125),
    ("edge", "Perimeter LEDs", 126, 164),
    ("speakers", "Stereo speakers", 165, 198),
    ("camera", "Camera", 199, 232),
    ("battery", "Battery & harness", 233, 289),
    ("turn", "", 290, 336),
    ("chips", "Processors & electronics", 337, 386),
    ("keyled", "Key backlights", 387, 431),
    ("keys", "20 tactile switches", 432, 481),
    ("lcd", "Display & flex", 482, 540),
    ("end", "LAB Pocket · v9b", 541, 578),
]
stage_data = {key: (label, start, stop) for key, label, start, stop in stages}
for key, label, start, _ in stages:
    scene.timeline_markers.new(label or "Turn to the front", frame=start)

def classify(o):
    name = o.name
    group = o.users_collection[0].name[:2]
    if name.startswith("LAB-Pocket-R2-v9b_"):
        return "board", "PCB"
    if group == "04":
        return ("battery", "adhesive" if name.startswith("ADH") else "pack and harness")
    if group == "02":
        return ("lcd", "supports" if name.startswith("Display support") else "panel")
    if group == "03":
        if name.startswith(("C6 ", "RF antenna")):
            return "radio", "RF module"
        if name.startswith(("IM70D122", "Mic marking")):
            suffix = re.search(r"\.(\d+)$", name)
            return "radio", f"MK{int(suffix[1]) + 1 if suffix else 1}"
        if name.startswith(("CTIA", "Headset socket", "TRRS")):
            return "ports", "J5"
        if name.startswith("SDCS2"):
            return "ports", "card"
        if name.startswith("LS"):
            return "speakers", name[:3]
        if name.startswith(("Camera ", "IMX219", "Focus barrel", "Anodized lens", "Lens ")):
            return "camera", "camera"
        if name.startswith("Pixel "):
            return "edge", "LED" + str(int(name.split()[1]))
        if name.startswith("Perimeter bounce"):
            suffix = re.search(r"\.(\d+)$", name)
            number = 1 + 2 * (int(suffix[1]) if suffix else 0)
            return "edge", "LED" + str(number)
        if name.startswith("Key "):
            return "keyled", "LED" + str(12 + int(name.split()[1]))
    if name in ("body", "pins", "lock"):
        return "chips", "J2"
    ref = re.match(r"^([A-Z]+)(\d+)(?= |$)", name)
    if not ref:
        raise ValueError(name)
    prefix, n = ref[1], int(ref[2])
    id_ = prefix + str(n)
    if prefix == "J": return ("chips" if n == 2 else "ports"), id_
    if prefix == "LED": return ("edge" if n <= 12 else "keyled"), id_
    if prefix == "SW": return "keys", id_
    if prefix == "C" and 21 <= n <= 40: return "keyled", "LED" + str(n - 8)
    if prefix not in ("U", "R", "C", "D"):
        raise ValueError(name)
    z = sum((original[name] @ Vector(point)).z for point in o.bound_box) / 8
    return ("radio" if z < 0 else "chips"), id_

units = defaultdict(list)
for obj in parts:
    stage, unit = classify(obj)
    units[(stage, unit)].append(obj)
assert len(units["board", "PCB"]) == 8
assert all(len(units["keys", "SW" + str(i)]) == 1 for i in range(1, 21))
assert all(len(units["keyled", "LED" + str(i)]) >= 7 for i in range(13, 33))

def key(obj, path, frame, value):
    setattr(obj, path, value)
    obj.keyframe_insert(data_path=path, frame=frame)

def visibility(obj, frame, hide):
    for prop in ("hide_viewport", "hide_render"):
        key(obj, prop, frame, hide)

def flight(stage, unit, center):
    number = re.search(r"\d+", unit)
    n = int(number[0]) if number else 0
    # Opposing banks move in pairs. Keys seat row by row, left to right.
    if stage == "edge":
        index = int(round((73 - center.y - 10.5) / 25))
        return 2 * index, 23, 1 if center.x < 0 else -1
    if stage in ("keys", "keyled"):
        idx = n - (1 if stage == "keys" else 13)
        row, col = divmod(idx, 5)
        return row * 4 + col, 26 if stage == "keys" else 21, -1 if stage == "keys" else 1
    if stage == "ports":
        if unit == "card": return 22, 17, -1
        order = ["J1", "J5", "J3", "J4", "J6"].index(unit)
        return 2 * order, 26, 1 if order % 2 == 0 else -1
    if stage == "battery": return (0, 18, -1) if unit == "adhesive" else (12, 35, 1)
    if stage == "lcd": return (0, 23, -1) if unit == "supports" else (12, 34, 1)
    if stage == "speakers": return (0 if n == 1 else 4), 24, (1 if n == 1 else -1)
    if stage == "camera": return 1, 24, -1
    if stage == "radio":
        return (8 if unit == "RF module" else (n % 6)), 25, (1 if center.x < 0 else -1)
    if stage == "chips":
        return (9 if unit in ("U1", "U2", "U11") else (n % 8)), 29, (1 if center.x > 0 else -1)
    raise ValueError(stage)

def centroid(objects):
    corners = [original[o.name] @ Vector(c) for o in objects
               if o.type in ("MESH", "CURVE", "FONT") for c in o.bound_box]
    return Vector([(min(v[i] for v in corners) + max(v[i] for v in corners)) / 2 for i in range(3)])

front_stages = {"chips", "keys", "keyled", "lcd"}
for (stage, unit), objects in units.items():
    if stage == "board": continue
    center = centroid(objects)
    node = bpy.data.objects.new(f"{stage} | {unit}", None)
    rig.objects.link(node)
    node.parent = root
    node.empty_display_size = 1.5
    node.location = center
    for obj in objects:
        obj.parent = node
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_basis = Matrix.Translation(-center) @ original[obj.name]
    lag, duration, side = flight(stage, unit, center)
    start = stage_data[stage][1] + lag
    face = 1 if stage in front_stages else -1
    lateral = Vector((right.x * face, right.y, 0)).normalized() * side
    lead = 246 if unit != "card" else 0
    lift = 29 if stage in ("lcd", "camera", "battery") else 17
    normal = Vector((0, 0, face))
    if unit == "card":
        # The removable card slides along its actual bottom-entry slot.
        travel = Vector((0, -148, 0))
        poses = [(0, travel, 0), (.50, travel * .21, 0), (.82, travel * .035, 0), (1, Vector(), 0)]
    else:
        # A broad approach becomes normal to the board for the final seat.
        poses = [(0, lateral * lead + normal * (lift + 17), 14),
                 (.43, lateral * 38 + normal * lift, 6),
                 (.78, lateral * 2.7 + normal * 6.0, 1.2),
                 (1, Vector(), 0)]
    for obj in objects:
        visibility(obj, 1, True)
        visibility(obj, start - 1, True)
        visibility(obj, start, False)
    for fraction, offset, angle in poses:
        frame = start + round(fraction * duration)
        key(node, "location", frame, center + offset)
        key(node, "rotation_euler", frame, (0, math.radians(face * side * angle), math.radians(side * angle * .47)))

# Raise the 74 mm board as it turns about its long axis, keeping the table clear.
camera_home = camera.location.copy()
turn_start, turn_end = stage_data["turn"][1:]
for f in (1, *range(turn_start, turn_end + 1), 578):
    t = min(1, max(0, (f - turn_start) / (turn_end - turn_start)))
    t = t*t*(3 - 2*t)
    theta = math.pi*(1-t)
    z = -9 + 1.6*max(0, -math.cos(theta)) + 8.07*max(0, math.cos(theta)) + 37*math.sin(theta) + 1.1
    key(camera, "location", f, camera_home + Vector((0, 0, 33 * math.sin(theta))))
    key(root, "rotation_euler", f, (0, theta, 0))
    key(root, "location", f, (0, 0, z))

# The screen comes on after the bezel is seated.
screen_mat = bpy.data.materials["IPS · color synth application"]
signal = screen_mat.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for frame, value in ((1, 0), (528, 0), (539, 1.05), (578, 1.05)):
    signal.default_value=value
    signal.keyframe_insert(data_path="default_value",frame=frame)

# Pin the native type to the camera. Its only contribution is to camera rays.
font = bpy.data.fonts.load("/usr/share/fonts/truetype/lato/Lato-Regular.ttf")
font.pack()
for stage, label, start, end in stages:
    if not label: continue
    data = bpy.data.curves.new(label, "FONT")
    data.body=label; data.font=font; data.size=8.0; data.resolution_u=8
    obj=bpy.data.objects.new("Caption | " + label, data)
    captions.objects.link(obj); obj.parent=camera
    obj.location=(-camera_data.ortho_scale*.45, -camera_data.ortho_scale*9/16*.408, -40)
    for prop in ("visible_shadow","visible_diffuse","visible_glossy","visible_transmission","visible_volume_scatter"):
        setattr(obj, prop, False)
    mat=bpy.data.materials.new("Ink | "+label);mat.use_nodes=True
    nodes=mat.node_tree.nodes; links=mat.node_tree.links;nodes.clear()
    out=nodes.new("ShaderNodeOutputMaterial");mix=nodes.new("ShaderNodeMixShader")
    transparent=nodes.new("ShaderNodeBsdfTransparent");ink=nodes.new("ShaderNodeEmission")
    ink.inputs[0].default_value=(.023,.025,.025,1)
    links.new(transparent.outputs[0],mix.inputs[1]);links.new(ink.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs[0])
    data.materials.append(mat)
    factor=mix.inputs[0]
    points=[(start,1 if start==1 else 0),(start+4,1),(end-5,1),(end,1 if end==578 else 0)]
    for frame,value in points:factor.default_value=value;factor.keyframe_insert(data_path="default_value",frame=frame)
    if start>1: visibility(obj,1,True);visibility(obj,start-1,True)
    visibility(obj,start,False)
    if end<578:visibility(obj,end+1,True)

scene.frame_start,scene.frame_end=1,578
scene.render.fps=24;scene.render.fps_base=1
scene.render.resolution_x,scene.render.resolution_y=1280,720
scene.render.resolution_percentage=100
scene.render.engine="CYCLES";scene.cycles.samples=12
scene.cycles.use_denoising=True
scene.cycles.use_animated_seed=False
scene.cycles.max_bounces=4;scene.cycles.diffuse_bounces=2;scene.cycles.glossy_bounces=2
scene.render.use_persistent_data=True
scene.render.threads_mode="FIXED";scene.render.threads=15
scene.render.image_settings.media_type="VIDEO";scene.render.image_settings.file_format="FFMPEG"
scene.render.ffmpeg.format="MPEG4";scene.render.ffmpeg.codec="H264";scene.render.ffmpeg.constant_rate_factor="HIGH"
scene.render.ffmpeg.audio_codec="NONE"
scene.render.filepath="//renders/"+NAME+"-"
scene.frame_set(578)
bpy.context.view_layer.update()
inv=root.matrix_world.inverted()
for obj in parts:
    error=max(abs(v-w) for row, refrow in zip(inv@obj.matrix_world, original[obj.name]) for v,w in zip(row,refrow))
    assert error < .0007,(obj.name,error)
    assert not obj.hide_render,obj.name
scene.frame_set(1)
assert sum(not o.hide_render for o in parts)==8
assert all(im.packed_file for im in bpy.data.images if im.source=="FILE")
for ws in bpy.data.screens:
    for a in ws.areas:
        if a.type=="VIEW_3D":
            a.spaces.active.region_3d.view_perspective="CAMERA"
            a.spaces.active.overlay.show_overlays=False
            a.spaces.active.shading.color_type="MATERIAL"
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(destination),compress=True)
print(f"Checked {len(parts)} original objects, {len(units)} moving assemblies including the PCB, 578 frames.")
