"""Check the Rev 2 v4 under-display placement with KiCad's Python bindings."""
from pathlib import Path
import pcbnew as pcb

if not hasattr(pcb.SwigPyIterator, "next"):
    pcb.SwigPyIterator.next = pcb.SwigPyIterator.__next__

board_file = Path(__file__).resolve().parent / "kicad/LAB-Pocket-R2-v4.kicad_pcb"
board = pcb.LoadBoard(str(board_file))
parts = {part.GetReference(): part for part in board.GetFootprints()}
# Reference model datum is 60,40 mm in KiCad. These rectangles are in that
# local coordinate system. Include the FPC insertion and fold in the reserve.
display = (14.23, 10.38, 67.77, 69.12)
reserves = [(14.8, 13.25, 17.2, 66.25), (64.8, 13.25, 67.2, 66.25),
            (30.75, 50.15, 51.25, 74.75)]

def bounds(part):
    boxes = [p.GetBoundingBox() for p in part.Pads()]
    boxes.extend(item.GetBoundingBox() for item in part.GraphicalItems()
                 if item.GetLayer() in (pcb.F_CrtYd, pcb.B_CrtYd))
    return (min(pcb.ToMM(b.GetLeft()) for b in boxes)-60,
            min(pcb.ToMM(b.GetTop()) for b in boxes)-40,
            max(pcb.ToMM(b.GetRight()) for b in boxes)-60,
            max(pcb.ToMM(b.GetBottom()) for b in boxes)-40)

def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

groups = {"U": range(4, 6), "D": range(1, 17), "C": range(1, 5),
          "R": range(1, 6), "TP": range(1, 6)}
hidden = {f"{prefix}{i}" for prefix, indices in groups.items() for i in indices}
front = {ref for ref, fp in parts.items() if not fp.IsFlipped()}
controls = {f"E{i}" for i in range(1, 15)} | {f"SW{i}" for i in range(1, 17)}
assert front == hidden | controls | {"J2"}
reserves.append(bounds(parts["J2"]))
for ref in hidden:
    b = bounds(parts[ref])
    assert display[0] < b[0] and b[2] < display[2], ref
    assert display[1] < b[1] and b[3] < display[3], ref
    assert not any(overlaps(b, reserve) for reserve in reserves), ref

battery = next(z for z in board.Zones() if z.GetZoneName() == "Bonded battery envelope")
assert battery.GetLayer() == pcb.B_Cu
assert battery.GetDoNotAllowFootprints() and battery.GetDoNotAllowPads()
b = battery.GetBoundingBox()
footprint = (pcb.ToMM(b.GetLeft())-60, pcb.ToMM(b.GetTop())-40,
             pcb.ToMM(b.GetRight())-60, pcb.ToMM(b.GetBottom())-40)
for ref, part in parts.items():
    if part.IsFlipped():
        assert not overlaps(bounds(part), footprint), ref
for trace in board.GetTracks():
    if isinstance(trace, pcb.PCB_VIA) and b.Contains(trace.GetPosition()):
        assert trace.GetBackTentingMode() == pcb.TENTING_MODE_TENTED
print(f"Verified {len(hidden)} hidden footprints, LCD supports and flex clearance, rear pouch keepout and via tenting.")
