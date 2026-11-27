"""Check Rev 2 v9 key placement, copper connectivity and USB mounting in KiCad."""
from pathlib import Path

import pcbnew as pcb

# KiCad 9/10 SWIG iterator bindings on Debian expose the Python 3 spelling only.
if not hasattr(pcb.SwigPyIterator, 'next'):
    pcb.SwigPyIterator.next = pcb.SwigPyIterator.__next__

board_file = Path(__file__).parent / 'kicad' / 'LAB-Pocket-R2-v9.kicad_pcb'
board = pcb.LoadBoard(str(board_file))
parts = {fp.GetReference(): fp for fp in board.GetFootprints()}
labels = {s.GetText(): s for s in board.GetDrawings() if isinstance(s, pcb.PCB_TEXT)}
board.BuildConnectivity()
connectivity = board.GetConnectivity()


def network(reference, pin):
    pad = parts[reference].FindPadByNumber(pin)
    return {(item.GetParentFootprint().GetReference(), item.GetNumber())
            for item in connectivity.GetConnectedItems(pad) if isinstance(item, pcb.PAD)}


edges = [item for item in board.GetDrawings() if item.GetLayer() == pcb.Edge_Cuts]
arcs = [edge for edge in edges if edge.GetShape() == pcb.SHAPE_T_ARC]
assert len(edges) == 8 and len(arcs) == 4
assert all(abs(pcb.ToMM(arc.GetRadius()) - 2) < .001 for arc in arcs)
bottom = max(edge.GetEnd().y for edge in edges)
assert any(edge.GetStart().y == edge.GetEnd().y == bottom
           and abs(pcb.ToMM(edge.GetLength()) - 70) < .001 for edge in edges)

usb = parts['J1']
assert usb.IsFlipped()
holes = [pad for pad in usb.Pads() if pad.GetAttribute() == pcb.PAD_ATTRIB_NPTH]
smt = [pad for pad in usb.Pads() if pad.GetAttribute() == pcb.PAD_ATTRIB_SMD]
assert len(holes) == 2 and len(smt) == 20 and len(list(usb.Pads())) == 22
assert all(pad.GetDrillSize().x == pad.GetDrillSize().y == pcb.FromMM(.65) for pad in holes)
assert [pad.GetNumber() for pad in smt].count('SH') == 4

supply = network('LED4', '1')
ground = network('LED4', '3')
previous, output = 'LED12', '2'
for n in range(1, 21):
    switch = parts[f'SW{n}']
    pixel = f'LED{n+12}'
    bypass = f'C{n+20}'
    label = labels[f'{n:02}']
    assert switch.GetOrientationDegrees() == 90
    assert not switch.IsFlipped() and not parts[pixel].IsFlipped()
    center = switch.GetPosition()
    led = parts[pixel].GetPosition()
    legend = label.GetPosition()
    assert center.x == led.x == legend.x
    assert center.y - led.y == pcb.FromMM(4.17)
    assert legend.y - center.y == pcb.FromMM(4.53) and label.GetLayer() == pcb.F_SilkS
    assert (pixel, '2') in network(previous, output), (previous, pixel)
    assert {(pixel, '3'), (bypass, '1')} <= supply, pixel
    assert {(pixel, '1'), (bypass, '2')} <= ground, pixel
    previous, output = pixel, '4'


    row, column = divmod(n - 1, 5)
    expected_x = pcb.FromMM(60 + 15.5 + 12.75 * column)
    expected_y = pcb.FromMM(40 + 87.25 + 16 * row)
    assert center.x == expected_x and center.y == expected_y, n
    diode = 'D' + str(n if n <= 16 else n + 1)
    assert (diode, '2') in network(f'SW{n}', '1'), n
    assert ('U4', str(4 + row)) in network(diode, '1'), (n, 'row')
    assert ('U4', str(13 + column)) in network(f'SW{n}', '2'), (n, 'column')
    pullup = ('R1', 'R2', 'R3', 'R4', 'R29')[column]
    assert (pullup, '2') in network(f'SW{n}', '2'), (n, 'pull-up')

assert {label for label in labels if label.isdigit()} == {f'{n:02}' for n in range(1, 21)}
assert all(ob.GetText().isdigit() for ob in labels.values()
           if ob.GetPosition().y >= pcb.FromMM(175) and ob.GetLayer() == pcb.F_SilkS)
assert not any(name in labels for name in ('KEY MATRIX', 'RP2350B   /   ESP32-P4', 'USB'))
xs = [edge.GetStart().x for edge in edges]
ys = [edge.GetStart().y for edge in edges]
assert max(xs) - min(xs) == pcb.FromMM(74)
assert max(ys) - min(ys) == pcb.FromMM(152)

def center(ref):
    pos = parts[ref].GetPosition()
    return pcb.ToMM(pos.x) - 60, pcb.ToMM(pos.y) - 40


def rect(box):
    return (pcb.ToMM(box.GetLeft()) - 60, pcb.ToMM(box.GetTop()) - 40,
            pcb.ToMM(box.GetRight()) - 60, pcb.ToMM(box.GetBottom()) - 40)


def bounds(fp):
    boxes = [rect(p.GetBoundingBox()) for p in fp.Pads()]
    boxes.extend(rect(g.GetBoundingBox()) for g in fp.GraphicalItems()
                 if g.GetLayer() in (pcb.F_CrtYd, pcb.B_CrtYd))
    return min(v[0] for v in boxes), min(v[1] for v in boxes), max(v[2] for v in boxes), max(v[3] for v in boxes)


def apart(a,b):
    return a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]


assert center('J1') == (41,148.325) and usb.GetOrientationDegrees()==180
assert abs(center('J1')[1]+3.675-152)<.001
assert center('J5')==(5.5,45.3) and parts['J5'].GetOrientationDegrees()==0
assert bounds(parts['LED2'])[3]<bounds(parts['J5'])[1] and bounds(parts['J5'])[3]<bounds(parts['LED3'])[1]
assert center('J6')==(40,137) and parts['J6'].GetOrientationDegrees()==0
assert ('C20','1') in network('J6','3')
for ref in ('J3','J4'):
    assert parts[ref].IsFlipped() and parts[ref].GetOrientationDegrees() == 180
    assert abs(center(ref)[1] + 9.725 - 151.925) < .001
assert center('J3')[1] == center('J4')[1]
for i,side in enumerate(('L','R'),1):
    f = parts[f'LS{i}']
    assert f.IsFlipped() and center(f'LS{i}')[1] == 14.5
    assert [f.FindPadByNumber(str(n)).GetNetname() for n in (1,2)] == [f'SPK_{side}_P',f'SPK_{side}_N']
    for pad in f.Pads():
        assert pcb.ToMM(pad.GetSize().x) == pcb.ToMM(pad.GetSize().y) == 2.5
        assert not pad.IsOnLayer(pcb.B_Paste)
zones = {z.GetZoneName():z for z in board.Zones()}
battery = zones['Bonded battery envelope']
assert battery.GetDoNotAllowFootprints() and battery.GetDoNotAllowPads()
pouch = rect(battery.GetBoundingBox())
assert all(abs(a-b)<.001 for a,b in zip(pouch,(11.25,52.0,70.75,130.5))),pouch
for ref, fp in parts.items():
    if fp.IsFlipped():assert apart(bounds(fp),pouch),ref
assert center('MK1')[1] == center('MK2')[1] and center('MK3')[1] == center('MK4')[1]
removed={'U5','R5','C2','C3','C4'} | {f'E{index}' for index in range(1,15)}
assert removed.isdisjoint(parts)
assert 'TOUCH' not in labels
assert not any('TOUCH' in p.GetNetname() for f in parts.values() for p in f.Pads())
assert not any('TOUCH' in t.GetNetname() for t in board.GetTracks())
assert {r for r in parts if r.startswith('LED')}=={f'LED{i}' for i in range(1,33)}
hidden = [ref for ref,fp in parts.items() if not fp.IsFlipped()
          and not ref.startswith(('LED','SW','E'))
          and ref != 'J2' and not (ref.startswith('C') and int(ref[1:]) >= 21)]
for ref in hidden:
    x0,y0,x1,y1 = bounds(parts[ref])
    assert 14.23<=x0<=x1<=67.77 and 10.38<=y0<=y1<=69.12, ref
    assert all(apart((x0,y0,x1,y1),reserve) for reserve in (
        (14.8,13.25,17.2,66.25),(64.8,13.25,67.2,66.25),(30.65,49.95,51.35,74.85),
        bounds(parts['J2']))),ref
assert len(hidden)==67
left=bounds(parts['J1'])[0]-bounds(parts['J3'])[2]
right=bounds(parts['J4'])[0]-bounds(parts['J1'])[2]
key_gap=bounds(parts['J1'])[1]-bounds(parts['SW18'])[3]
assert left>7.4 and right>7.3 and key_gap>2.3
assert bounds(parts['J1'])[1]-bounds(parts['J6'])[3]>1.4
print(f'Bottom USB gaps to card footprints: {left:.3f} / {right:.3f} mm. Gap to key 18: {key_gap:.3f} mm.')
print('Verified 20 keys and pixel paths, 12 perimeter LEDs, 67 under-screen parts plus J2 and a touch-free board.')
