"""Check Rev 2 v6 key placement, copper connectivity and USB mounting in KiCad."""
from pathlib import Path

import pcbnew as pcb

# KiCad 9/10 SWIG iterator bindings on Debian expose the Python 3 spelling only.
if not hasattr(pcb.SwigPyIterator, 'next'):
    pcb.SwigPyIterator.next = pcb.SwigPyIterator.__next__

board_file = Path(__file__).parent / 'kicad' / 'LAB-Pocket-R2-v6.kicad_pcb'
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
           if ob.GetPosition().y >= pcb.FromMM(175))
assert not any(name in labels for name in ('KEY MATRIX', 'RP2350B   /   ESP32-P4', 'USB'))
xs = [edge.GetStart().x for edge in edges]
ys = [edge.GetStart().y for edge in edges]
assert max(xs) - min(xs) == pcb.FromMM(74)
assert max(ys) - min(ys) == pcb.FromMM(152)
switch = parts['SW18'].GetCourtyard(pcb.F_CrtYd).BBox()
socket = usb.GetCourtyard(pcb.B_CrtYd).BBox()
gap = pcb.ToMM(socket.GetTop() - switch.GetBottom())
assert abs(gap - 2.375) < .001, gap
print(f'Checked a 74 × 152 mm board and {gap:.3f} mm projected SW18–J1 courtyard gap.')
print('Verified twenty independent switch/diode paths, four scan rows, five pulled-up columns, '
      'twenty LED data links and bypass pairs, and keypad legends 01–20.')
