"""Inspect the assembled v8 scene in Blender at frame 1."""
import bpy, numpy as np
from mathutils import Vector
s=bpy.context.scene;s.frame_set(1)
root=bpy.data.objects['LAB · assembled device']
dep=bpy.context.evaluated_depsgraph_get()
def box(o):
    o=o.evaluated_get(dep);v=np.array([o.matrix_world@Vector(c) for c in o.bound_box])
    return np.stack((v.min(axis=0),v.max(axis=0)))
bodies={o.name:box(o) for o in root.children_recursive if o.type in ('CURVE','FONT','MESH')}
bb=np.array(list(bodies.values()));dim=bb[:,1].max(axis=0)-bb[:,0].min(axis=0)
print('Envelope',dim,flush=True)
assert np.allclose(dim,[74,152,14.967],atol=.02),dim
pouch=bodies['BT1 · sealed rim']
assert np.allclose((pouch[0]+pouch[1])[:2]/2,[0,-20.65],atol=.012)
assert bodies['BT1 · protected short end'][0][1]>-1
pts=[]
for label,start,end in [('Positive',(47.4,57.95),(58.5,44.65)),('Ground',(34.6,57.95),(62.5,44.65))]:
    o=next(o for o in s.objects if o.name.startswith('BT1 lead · '+label));v=np.array([o.matrix_world@Vector(n.co[:3]) for n in o.data.splines[0].points])
    assert np.allclose(v[0,:2],[start[0]-41,73-start[1]],atol=.02)
    assert np.allclose(v[-1,:2],[end[0]-41,73-end[1]],atol=.02)
    assert abs(np.linalg.norm(np.diff(v,axis=0),axis=1).sum()-70)<.02
    # At most 0.03 mm between samples. Bounds the wire-to-wire clearance estimate.
    pts.append(np.vstack([np.linspace(a,b,max(2,int(np.ceil(np.linalg.norm(a-b)/.03))+1)) for a,b in zip(v,v[1:])]))
clear=min(np.linalg.norm(a[:,None,:]-pts[1][None,:,:],axis=2).min() for a in np.array_split(pts[0],50))-.9
print('Minimum harness surface gap, mm',clear,flush=True)
assert clear>.1
for label in ('LS1','LS2'):
    b=bodies[label+' • PUI speaker shell'];assert np.allclose(b[0][1:2],[52],atol=.02)
for name in ('Lens pupil','320 × 320 active area'):
    a,b=bodies[name];assert np.allclose((a+b)[:2]/2,(0,35.94),atol=.01)
frame=bodies['TTC273XSI-01 • backlight frame']
refs=('U1','U2','U4','U5','U6','U8','U9','U10','U11')
for ref in refs:
    group=[v for name,v in bodies.items() if name.startswith(ref+' ·')];assert group,ref
    maxz=max(v[1][2] for v in group);print(ref,'clear air to LCD',round(frame[0][2]-maxz,3))
    assert frame[0][2]-maxz>.60, (ref,maxz)
for tex in bpy.data.images:
    if tex.source=='FILE':assert tex.packed_file,tex.name

jack = bodies['TRRS barrel rim']
axis_jack = (jack[0][1]+jack[1][1])/2
# Use the actual GCT STEP shell. Its mouth is symmetric about the travel axis.
shells=[v for k,v in bodies.items() if k.startswith('J1 ·')]
assert shells
shell=max(shells,key=lambda b:(b[1][0]-b[0][0])*(b[1][1]-b[0][1])*(b[1][2]-b[0][2]))
axis_usb=(shell[0][1]+shell[1][1])/2
print('Board top to audio and USB axes in assembled scene, mm',73-axis_jack,73-axis_usb)
assert abs(axis_jack-axis_usb)<.008 and abs(73-axis_usb-45.3)<.008
