"""Run with the system Python that provides KiCad 10's pcbnew module."""
import csv
import hashlib
from math import isclose
from pathlib import Path

import pcbnew as pcb

if not hasattr(pcb.SwigPyIterator, "next"):
    pcb.SwigPyIterator.next = pcb.SwigPyIterator.__next__

here = Path(__file__).resolve().parent
board = pcb.LoadBoard(str(here / "kicad/LAB-Pocket-R2.kicad_pcb"))
footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
mm = pcb.ToMM
edge_widths = {mm(item.GetWidth()) for item in board.GetDrawings()
               if item.GetLayer() == pcb.Edge_Cuts}
stroke, = edge_widths
bb = board.GetBoardEdgesBoundingBox()
x0, y0 = mm(bb.GetLeft()) + stroke/2, mm(bb.GetTop()) + stroke/2
width, height = mm(bb.GetWidth()) - stroke, mm(bb.GetHeight()) - stroke


def expect(actual, expected):
    if not isclose(actual, expected, abs_tol=.002):
        raise ValueError(f"Expected {expected:.4f}, measured {actual:.4f}")


def position(ref):
    p = footprints[ref].GetPosition()
    return mm(p.x) - x0, mm(p.y) - y0


def zone_bounds(name):
    area, = [z for z in board.Zones() if z.GetZoneName() == name]
    bounds = area.GetBoundingBox()
    return (mm(bounds.GetLeft())-x0, mm(bounds.GetTop())-y0,
            mm(bounds.GetRight())-x0, mm(bounds.GetBottom())-y0)


expect(width, 74)
expect(height, 146)
expect(mm(board.GetDesignSettings().GetBoardThickness()), 1.6)
assert board.GetCopperLayerCount() == 4
assert not any(r.startswith("H") for r in footprints)

battery = zone_bounds("Bonded battery envelope")
expect(battery[2]-battery[0], 59.5)
expect(battery[3]-battery[1], 78.5)
for i in range(12):
    x, y = position(f"LED{i+1}")
    expect(x, 3.5 if i < 6 else width-3.5)
    expect(y, 10.5+25*(i if i < 6 else 11-i))
    expect(min(x,width-x)-2.5, 1)
    expect(min(abs(x-battery[0]),abs(x-battery[2]))-2.5, 1.25)

# Both socket IDs, orientation and power-contact offsets must match, including mirroring.
a, b = footprints["J3"], footprints["J4"]
assert a.IsFlipped() and b.IsFlipped()
assert a.GetFPIDAsString() == b.GetFPIDAsString()
expect(a.GetOrientationDegrees(), 0)
expect(b.GetOrientationDegrees(), 0)
expect(sum(position(ref)[0] for ref in ("J3","J4")), width)
expect(position("J3")[1], position("J4")[1])
for f in (a,b):
    pad1=next(p for p in f.Pads() if p.GetNumber()=="1")
    # KiCad's DM3AT card mouth is the low-Y edge; the signal contacts are behind it.
    assert mm(pad1.GetPosition().y)>mm(f.GetPosition().y)
for x in (19,63):
    zone_bounds("Top entry card lane "+str(x))
lens=zone_bounds("Lens and carrier envelope")
aperture=[(37-24.48,37.06-24.48),(37+24.48,37.06+24.48)]
edges=[(item.GetStart(),item.GetEnd()) for item in board.GetDrawings()
       if item.GetLayer()==pcb.Dwgs_User]
for x,y in aperture:
    assert any(abs(mm(p.x)-x0-x)<.002 and abs(mm(p.y)-y0-y)<.002 for segment in edges for p in segment)
expect((lens[0]+lens[2])/2, width/2)
expect((lens[1]+lens[3])/2, 37.06)
expect(battery[1]-lens[3], 1.69)
for track in board.GetTracks():
    if isinstance(track, pcb.PCB_VIA):
        expect(track.GetBackTentingMode(), pcb.TENTING_MODE_TENTED)

docs = list(csv.DictReader((here/'datasheets/index.csv').read_text().splitlines()))
for row in docs:
    blob = (here/'datasheets'/row['Local document']).read_bytes()
    assert blob.startswith(b'%PDF-')
    assert hashlib.sha256(blob).hexdigest() == row['SHA256']
bom = list(csv.DictReader((here/'parts.csv').read_text().splitlines()))
assert {p['Manufacturer document'] for p in bom} == {'datasheets/'+row['Local document'] for row in docs}
assert any(row['Candidate MPN']=='9495LE' for row in bom)
print(f"Verified {width:.0f} × {height:.0f} mm, 12 LEDs, both card slots, camera axis, and {len(docs)} datasheets.")
