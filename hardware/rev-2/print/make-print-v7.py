"""Turn Blender-sampled surfaces into a closed assembled STL and a flat P1S plate.

The output directory must contain front.npy and rear.npy from sample-assembly-v7.py.
"""
import argparse
import importlib.util
from pathlib import Path
import struct

import manifold3d as m
import numpy as np

WIDTH, LENGTH, SEAM = 74, 152, .8
PINS = [(22, 89), (51, 93)]


def height_solid(height):
    ny, nx = height.shape
    y, x = np.indices((ny, nx))
    top = np.column_stack((x.ravel()/10, y.ravel()/10, height.ravel()))
    ids = np.arange(nx*ny, dtype=np.int32).reshape(ny, nx)
    border = np.concatenate([ids[0], ids[1:, -1], ids[-1, -2::-1], ids[-2:0:-1, 0]])
    bottom = top[border].copy()
    bottom[:, 2] = 0
    vertices = np.vstack([top, bottom, bottom.mean(axis=0)])
    a = ids[:-1, :-1].ravel()
    low = np.arange(len(border)) + len(top)
    nxt, ln = np.roll(border,-1), np.roll(low,-1)
    tri = np.vstack([np.column_stack(t) for t in
                     [(a,a+1,a+nx+1),(a,a+nx+1,a+nx),
                      (border,low,ln),(border,ln,nxt),
                      (np.full(len(border),len(vertices)-1),ln,low)]])
    solid = m.Manifold(m.Mesh(vertices.astype(np.float32), tri.astype(np.uint32)))
    assert solid.status() == m.Error.NoError
    return solid.simplify(.025)


def relief(source):
    height = np.round(np.load(source), 3)
    assert height.shape == (1521,741)
    np.maximum(height, SEAM, out=height)
    surface = height_solid(height)
    clip = pad(37,76,74,152,2,-.1,10)
    return surface ^ clip


def groove(x,y,w,h,r,width,lo,hi):
    outside = rounded(x,y,w,h,r)
    return (outside-outside.offset(-width)).extrude(hi-lo).translate((0,0,lo))


def legends():
    digits = ('abcdef','bc','abdeg','abcdg','bcfg',
              'acdfg','acdefg','abc','abcdefg','abcdfg')
    # Continuous, single-extrusion strokes make the two-digit legends legible in PLA.
    segments = dict(a=(0,.82,1.02,.40), b=(.34,.42,.40,.87),
                    c=(.34,-.42,.40,.87), d=(0,-.82,1.02,.40),
                    e=(-.34,-.42,.40,.87), f=(-.34,.42,.40,.87),
                    g=(0,0,1.02,.40))
    shapes=[]
    for i in range(20):
        row,col=divmod(i,5)
        x=11.5+12.75*col; y=152-(87.25+16*row+4.53)
        for char,dx in zip(f'{i+1:02}',(-.68,.68)):
            for seg in digits[int(char)]:
                sx,sy,w,h=segments[seg]
                shapes.append(pad(x+dx+sx,y+sy,w,h,.08,.75,1.20))
    return union(shapes)


def sockets(model):
    holes = []
    for x,y in PINS:
        holes.extend([cylinder(x,y,-.1,2.85,1.72), cylinder(x,y,-.01,.35,1.99,1.71)])
    return model-union(holes)


def printable_arrays(model):
    # Float32 STL can collapse thin coplanar triangles to lines. Split their
    # neighbour at the middle vertex to preserve both the surface and its edges.
    mesh=model.to_mesh()
    vertices, remap=np.unique(np.asarray(mesh.vert_properties[:,:3]),axis=0,return_inverse=True)
    faces=remap[np.asarray(mesh.tri_verts)]
    faces=faces[(faces[:,0]!=faces[:,1]) & (faces[:,1]!=faces[:,2]) & (faces[:,0]!=faces[:,2])]
    for _ in range(100):
        tri=vertices[faces].astype(np.float64)
        area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)
        collapsed=np.flatnonzero(area==0)
        if not len(collapsed):break
        for index in collapsed:
            f=faces[index]
            k=int(np.argmax(np.linalg.norm(tri[index]-np.roll(tri[index],-1,axis=0),axis=1)))
            a,c,b=np.roll(f,-k)
            adjacent=np.flatnonzero(np.any(faces==a,axis=1) & np.any(faces==c,axis=1) & (area>0))
            if len(adjacent)!=1:continue
            j=adjacent[0]
            opposite=next(v for v in faces[j] if v not in (a,c))
            assert np.roll(faces[j],-list(faces[j]).index(c))[1]==a
            faces[index]=[c,b,opposite]
            faces[j]=[b,a,opposite]
            break
        else:raise ValueError('Could not resolve collinear mesh edge')
    else:raise ValueError('Mesh cleanup did not converge')
    edges=np.sort(np.vstack([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
    assert np.all(np.unique(edges,axis=0,return_counts=True)[1]==2)
    return vertices,faces


def stl(model, path):
    vertices,faces=printable_arrays(model)
    triangles=vertices[faces].astype(np.float64)
    normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    normals/=np.linalg.norm(normals,axis=1)[:,None]
    data=np.zeros(len(normals),dtype=[('normal','<f4',3),('verts','<f4',(3,3)),('attr','<u2')])
    data['normal']=normals;data['verts']=triangles
    with path.open('xb') as f:
        f.write(b'LAB Pocket R2 v7 | assembled fit sample | millimetres'.ljust(80,b' '))
        f.write(struct.pack('<I',len(data)));f.write(data.tobytes())


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--helpers',type=Path,
                        default=Path(__file__).resolve().parents[2]/'rev-a/print/make_model.py')
    args=parser.parse_args();out=args.directory
    spec=importlib.util.spec_from_file_location('lab_print_geometry',args.helpers)
    helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
    rounded,pad,cylinder,union=helpers.rounded,helpers.pad,helpers.cylinder,helpers.union
    front=relief(out/'front.npy')
    rear=relief(out/'rear.npy')
    # Single-colour relief for features represented by printed ink or a texture in CAD.
    motifs=[groove(x,152-(16.3+i*7.25),7.6,4.4 if (x,i)==(69,4) else 5,.8,.48,.55,.96)
            for x in (5,69) for i in range(7)]
    motifs.append(groove(37,152-37.06,48.96,48.96,.5,.52,5.81,6.3))
    for y in (42.41,48.19):
        motifs.append(cylinder(67.72,152-y,.46,.54,.325))
    front=(front-union(motifs))+legends()
    # Represent the visible sheet-metal opening with a shallow, bridgeable mouth.
    mouth=pad(73.55,152-45.3,2.1,7.35,.35,1.52,3.44)
    jack=cylinder(0,0,0,1.65,1.65).rotate((0,90,0)).translate((-.15,152-48.925,3.35))
    rear=rear-union([mouth,jack])
    assembled=(front+rear.mirror((0,0,1))).translate((0,0,8.87)).set_tolerance(.015)
    pfront=sockets(front).set_tolerance(.015)
    prear=sockets(rear).mirror((1,0,0)).translate((74,0,0)).set_tolerance(.015)
    pin=helpers.pin()
    for body in (assembled,pfront,prear,pin):
        assert body.status()==m.Error.NoError and len(body.decompose())==1
    bounds=assembled.bounding_box()
    assert np.allclose(bounds,(0,0,0,74,152,14.967),atol=.006),bounds
    print('Assembled extent',bounds,'triangles',assembled.num_tri(),flush=True)
    stl(assembled,out/'LAB-Pocket-R2-v7-assembled-mm-r1.stl')
    objects=[('Front - 20 keys',pfront,40,55),('Rear - battery',prear,137,55),
             ('Alignment pin A',pin,119,45),('Alignment pin B',pin,135,45)]
    helpers.arrays=printable_arrays
    helpers.plate_3mf(objects,out/'base-plate.3mf')
