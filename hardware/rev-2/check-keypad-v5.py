"""Check Rev 2 v5 key placement, copper connectivity and USB mounting in KiCad."""
from pathlib import Path

import pcbnew as pcb

# KiCad 9/10 SWIG iterator bindings on Debian expose the Python 3 spelling only.
if not hasattr(pcb.SwigPyIterator, 'next'):
    pcb.SwigPyIterator.next = pcb.SwigPyIterator.__next__

board_file = Path(__file__).parent / 'kicad' / 'LAB-Pocket-R2-v5.kicad_pcb'
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
for n in range(1, 17):
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

print('Verified four R2 corners, straight USB edge, two 0.65 mm locators, '
      'all 16 rotated keys and legends, 16 data links, and both local power rails.')
