"""Generate the Rev A ergonomic mock-up. Requires Python 3, manifold3d and numpy."""
import argparse
from pathlib import Path
import struct
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

import manifold3d as m
import numpy as np

WIDTH, LENGTH = 82.0, 146.0
HALF_PCB = 0.8
# Coordinates are measured on the front of the PCB, from its top left.
REGISTRATION = [(32.0, 50.0), (51.0, 60.5)]
N = 48


def rounded(x, y, width, length, radius):
    """Rounded rectangle with exact straight-edge datum and overall dimensions."""
    profile = m.CrossSection.square((width - 2*radius, length - 2*radius), center=True)
    return profile.offset(radius, circular_segments=N).translate((x, y))


def pad(x, y, width, length, radius, z0, z1):
    return rounded(x, y, width, length, radius).extrude(z1-z0).translate((0, 0, z0))


def cylinder(x, y, z, height, r0, r1=None):
    top_radius = r0 if r1 is None else r1
    return m.Manifold.cylinder(height, r0, top_radius, N).translate((x, y, z))


def union(shapes):
    return m.Manifold.batch_boolean(shapes, m.OpType.Add)


def board():
    return pad(WIDTH/2, LENGTH/2, WIDTH, LENGTH, 4.5, 0, HALF_PCB)


def front():
    shapes = [board()]
    # Filled below the LCD frame so the print grows from the PCB without support.
    lcd_top = HALF_PCB + 5.3
    lcd = pad(41, 39.75, 53.54, 58.74, .8, .6, lcd_top)
    active = pad(41, 37.06, 48.96, 48.96, .5, lcd_top-.30, lcd_top+.1)
    shapes.append(lcd - active)
    for row in range(4):
        for col in range(4):
            x, y = 15.5 + col*17, 83 + row*16
            shapes.append(pad(x, y, 6, 6, .4, .6, HALF_PCB+2.4))
            shapes.append(cylinder(x, y, HALF_PCB+2.39, 1.71, 1.8))
            shapes.append(cylinder(x, y, HALF_PCB+4.10, .2, 1.8, 1.60))
    model = union(shapes)
    # Trace each copper segment with a tool line. Contact surfaces stay flush with PCB.
    grooves = []
    for x in (8.4, 73.6):
        for index in range(7):
            y = 16.3 + index*7.25
            outer = rounded(x, y, 7.6, 5.0, .8)
            grooves.append((outer - outer.offset(-.52)).extrude(.4).translate((0, 0, HALF_PCB-.23)))
    return model - union(grooves)


def rear():
    shapes = [board()]
    # Guard envelope includes the standoff and the closed protective roof.
    cover_top = HALF_PCB + 11.45
    shapes.append(pad(41, 83.5, 64, 84, 4, .64, cover_top))
    for x in (15, 67):
        for y in (48, 119):
            # SJ5302 bumper diameter and height, with a small flat for tabletop contact.
            foot = m.CrossSection([[(0,-.04),(3.95,-.04),(3.90,.36),
                                    (3.35,1.05),(2.61,1.72),(1.45,2.20),(0,2.20)]])
            shapes.append(foot.revolve(N).translate((x,y,cover_top)))
    for x in (15.7,66.3):
        for row in range(9):
            shapes.append(pad(x,64+4.7*row,7,1.05,.46,cover_top-.1,cover_top+.36))
    for i in range(6):
        for x in (4.3, 77.7):
            shapes.append(pad(x,48+17*i,5,5,.55,.65,HALF_PCB+1.70))
    for x in (23,59):
        speaker = pad(x,134,18,13,1.65,.65,HALF_PCB+3.27)
        inset = rounded(x,134,15.1,10.1,2.4)
        face = (inset - inset.offset(-.75)).extrude(.7).translate((0,0,HALF_PCB+2.87))
        shapes.append(speaker-face)
    shapes.extend([
        pad(46,12,10,11,.8,.65,HALF_PCB+.90),
        pad(46,12,6.5,6.5,.65,HALF_PCB+.72,HALF_PCB+2.78),
        cylinder(46,12,HALF_PCB+2.74,1.50,2.83,2.18),
        pad(52,13,2,1.25,.2,.65,HALF_PCB+1),
        pad(55.7,13,1.6,.85,.15,.65,HALF_PCB+.65),
        pad(30,8.9,13.2,16.6,.5,.65,HALF_PCB+.8),
        pad(30,11.2,12,10.75,.65,HALF_PCB+.73,HALF_PCB+2.4),
        pad(36,29,10,10,.45,.65,HALF_PCB+.9),
        pad(53,29,10,10,.45,.65,HALF_PCB+.9),
        pad(13.2,20.2,14.0,14.2,.65,.65,HALF_PCB+1.8),
        pad(73,25,14.2,14.0,.65,.65,HALF_PCB+1.8),
        pad(8.75,34.425,15.2,6.0,.65,.65,HALF_PCB+4.3),
        pad(43.5,130,9.9,7,.45,.65,HALF_PCB+3.7),
    ])
    # Rear USB-C face sits back from the unbroken board edge. A shallow mouth
    # represents the finger/cable approach, with a short printable roof bridge.
    usb = pad(41,140.6,9,7,.45,.65,HALF_PCB+3.2)
    mouth = pad(41,144.20,6.9,2.0,.3,HALF_PCB+.8,HALF_PCB+2.25)
    shapes.append(usb-mouth)
    return union(shapes)


def sockets(part):
    holes = []
    for x, y in REGISTRATION:
        holes.append(cylinder(x, y, -.10, 2.85, 1.72))
        holes.append(cylinder(x, y, -.01, .35, 1.99, 1.71))
    return part - union(holes)


def pin():
    return union([cylinder(0,0,0,.24,1.32,1.5),
                  cylinder(0,0,.24,4.52,1.5),
                  cylinder(0,0,4.76,.24,1.5,1.32)])


def north_up(part):
    return part.mirror((0,1,0)).translate((0,LENGTH,0))


def arrays(part):
    assert part.status() == m.Error.NoError and len(part.decompose()) == 1
    mesh = part.to_mesh()
    return np.asarray(mesh.vert_properties[:, :3]), np.asarray(mesh.tri_verts)


def write_stl(part, path):
    vertices, triangles = arrays(part)
    with path.open('wb') as target:
        target.write(b'LAB Pocket Rev A | assembled ergonomic mock-up | mm'.ljust(80, b' '))
        target.write(struct.pack('<I',len(triangles)))
        for a,b,c in vertices[triangles]:
            n = np.cross(b-a,c-a)
            target.write(struct.pack('<12fH', *(n/np.linalg.norm(n)), *a,*b,*c,0))


def plate_3mf(objects, path):
    core = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    model = ET.Element('model', {'unit':'millimeter','xml:lang':'en-US','xmlns':core})
    ET.SubElement(model,'metadata', name='Title').text = 'LAB Pocket | full-scale hand model'
    resources = ET.SubElement(model,'resources')
    build = ET.SubElement(model,'build')
    for i,(name,part,tx,ty) in enumerate(objects,1):
        vertices,triangles = arrays(part)
        obj = ET.SubElement(resources,'object',id=str(i),type='model',name=name)
        mesh = ET.SubElement(obj,'mesh')
        verts = ET.SubElement(mesh,'vertices')
        for x,y,z in vertices:
            ET.SubElement(verts,'vertex',x=f'{x:.6f}',y=f'{y:.6f}',z=f'{z:.6f}')
        faces = ET.SubElement(mesh,'triangles')
        for a,b,c in triangles:
            ET.SubElement(faces,'triangle',v1=str(a),v2=str(b),v3=str(c))
        ET.SubElement(build,'item',objectid=str(i),transform=f'1 0 0 0 1 0 0 0 1 {tx} {ty} 0')
    with ZipFile(path,'w',ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml',
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        archive.writestr('_rels/.rels',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rel0" Target="/3D/3dmodel.model" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        archive.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='Directory for the 3MF and STL')
    output = parser.parse_args().output
    output.mkdir(parents=True,exist_ok=True)
    f, r = front(), rear()
    assembled = north_up(f + r.mirror((0,0,1))).translate((0,0,14.45))
    assert np.allclose(assembled.bounding_box(), (0,0,0,82,146,20.55))
    write_stl(assembled, output/'LAB-Pocket-assembled-mm.stl')
    objects = [
        ('Front',north_up(sockets(f)),38,55),
        ('Rear',north_up(sockets(r)).mirror((1,0,0)).translate((WIDTH,0,0)),136,55),
        ('Alignment pin A',pin(),123,40),
        ('Alignment pin B',pin(),138,40),
    ]
    plate_3mf(objects, output/'LAB-Pocket-plate.3mf')


if __name__ == '__main__':
    main()
