"""Run with the Python interpreter that provides KiCad 10's pcbnew module."""
import csv
import hashlib
from math import isclose
from pathlib import Path

import pcbnew as pcb

# KiCad 10 on Ubuntu uses the Python 3 iterator spelling.
if not hasattr(pcb.SwigPyIterator, "next"):
    pcb.SwigPyIterator.next = pcb.SwigPyIterator.__next__

ROOT = Path(__file__).resolve().parent
board = pcb.LoadBoard(str(ROOT / "kicad/LAB-Pocket.kicad_pcb"))
footprints = {part.GetReference(): part for part in board.GetFootprints()}
mm = pcb.ToMM


def expect(label, actual, target, tolerance=0.001):
    if not isclose(actual, target, abs_tol=tolerance):
        raise ValueError(f"{label}: measured {actual:.4f}, expected {target:.4f}")
    print(f"{label:43} {actual:8.3f}")


def grid_position(ref):
    position = footprints[ref].GetPosition()
    return mm(position.x), mm(position.y)


edges = board.GetBoardEdgesBoundingBox()
# The bounding box includes half the outline stroke on each side.
strokes = {mm(item.GetWidth()) for item in board.GetDrawings()
           if item.GetLayer() == pcb.Edge_Cuts}
if len(strokes) != 1:
    raise ValueError("Use a single outline stroke width or measure the contour directly")
stroke, = strokes
width, height = mm(edges.GetWidth()) - stroke, mm(edges.GetHeight()) - stroke
origin_x, origin_y = mm(edges.GetLeft()) + stroke/2, mm(edges.GetTop()) + stroke/2
expect("Profile width, mm", width, 82)
expect("Profile height, mm", height, 146)
expect("PCB thickness, mm", mm(board.GetDesignSettings().GetBoardThickness()), 1.60)
expect("Copper layers", board.GetCopperLayerCount(), 4)

for n in range(1, 17):
    x, y = grid_position(f"SW{n}")
    assert isclose(x - origin_x, 15.5 + 17 * ((n-1) % 4), abs_tol=.001)
    assert isclose(y - origin_y, 83 + 16 * ((n-1) // 4), abs_tol=.001)
print("Keypad: 16 positions on a 17 × 16 mm grid")
panel_center = origin_x + width/2
for n in range(1, 15):
    pad, = footprints[f"E{n}"].Pads()
    size = pad.GetSize()
    x, y = grid_position(f"E{n}")
    assert pad.GetNetname() == f"TOUCH_{n:02d}"
    assert isclose(y-origin_y, 16.3 + 7.25*((n-1) % 7), abs_tol=.001)
    assert isclose(mm(size.y), 5) and isclose(mm(size.x), 7.6)
    gap = abs(x-panel_center) - 53.54/2 - mm(size.x)/2
    assert isclose(gap, 2.03, abs_tol=.001)
expect("Panel to exposed touch gold, mm", gap, 2.03)
guard_zone, = [z for z in board.Zones() if z.GetZoneName().startswith("Rear cell")]
box = guard_zone.GetBoundingBox()
expect("Rear guard width on PCB, mm", mm(box.GetWidth()), 64)
expect("Rear guard length on PCB, mm", mm(box.GetHeight()), 84)
assert guard_zone.GetDoNotAllowFootprints()
guard_end_y = mm(box.GetBottom())
j6_top = min(mm(shape.GetBoundingBox().GetTop()) for shape in
             footprints["J6"].GraphicalItems() if shape.GetLayer() == pcb.B_CrtYd)
expect("Guard to J6 courtyard, mm", j6_top-guard_end_y, .375, .005)
for ref, fp in footprints.items():
    for pad in fp.Pads():
        if not pad.GetDrillSize().x:
            continue
        x = mm(pad.GetPosition().x) - origin_x
        y = mm(pad.GetPosition().y) - origin_y
        if min(x, width-x) < 6 and min(y, height-y) < 6:
            raise ValueError(f"Board corner contains a drill at {ref}")
        if ref in {"H5", "H6", "H7", "H8"}:
            assert isclose(mm(pad.GetDrillSize().x), 2.2)
print("Four 6 × 6 mm corner regions are free of footprint drills")
assert {"H5","H6","H7","H8"} == {r for r in footprints if r.startswith("H")}

with (ROOT / "datasheets/index.csv").open() as source:
    docs = list(csv.DictReader(source))
for row in docs:
    path = ROOT / "datasheets" / row["Local document"]
    data = path.read_bytes()
    assert data.startswith(b"%PDF-") and hashlib.sha256(data).hexdigest() == row["SHA256"], path
with (ROOT / "parts.csv").open() as source:
    bom = list(csv.DictReader(source))
included = {row["Manufacturer document"] for row in bom}
assert included == {"datasheets/"+row["Local document"] for row in docs}
purchased = {ref for row in bom for ref in row["Refdes / assembly"].split()}
assert all(ref in purchased or ref.startswith(("E","TP","H")) for ref in footprints)
print(f"{len(docs)} archived supplier PDFs match the BOM and recorded SHA-256 digests")

