"""Measure pin-to-pin copper lengths including vertical travel on the Rev 3 stack."""
from collections import defaultdict
from heapq import heappop, heappush
from itertools import combinations
from pathlib import Path

import pcbnew as pcb

BOARD = Path(__file__).resolve().parents[1] / "kicad" / "LAB-Pocket-R3A.kicad_pcb"
LAYERS = [pcb.F_Cu, pcb.In1_Cu, pcb.In2_Cu, pcb.In3_Cu,
          pcb.In4_Cu, pcb.In5_Cu, pcb.In6_Cu, pcb.B_Cu]
DIELECTRICS = (.0994, .1000, .3568, .3000, .3568, .1000, .0994)
FOILS = (.0350, *([.0152] * 6), .0350)

# Quantization joins coordinates that the PCB exporter rounded differently at a via.
def node(position, layer):
    return round(pcb.ToMM(position.x), 4), round(pcb.ToMM(position.y), 4), layer


def measure(board, name, source_pin, connector, end_pin):
    copper = defaultdict(list)
    heights = [0.0]
    for i, dielectric in enumerate(DIELECTRICS):
        heights.append(heights[-1] + dielectric + (FOILS[i] + FOILS[i + 1]) / 2)

    def edge(a, b, distance):
        copper[a].append((b, distance))
        copper[b].append((a, distance))

    for item in board.GetTracks():
        if item.GetNetname() != name:
            continue
        if isinstance(item, pcb.PCB_VIA):
            for i, j in combinations(range(len(LAYERS)), 2):
                edge(node(item.GetPosition(), LAYERS[i]), node(item.GetPosition(), LAYERS[j]),
                     heights[j] - heights[i])
        else:
            layer = item.GetLayer()
            edge(node(item.GetStart(), layer), node(item.GetEnd(), layer), pcb.ToMM(item.GetLength()))

    def pin(ref, num, layer):
        pad = board.FindFootprintByReference(ref).FindPadByNumber(str(num))
        assert pad.GetNetname() == name, (ref, num, pad.GetNetname())
        return node(pad.GetPosition(), layer)

    start = pin("U1", source_pin, pcb.F_Cu)
    end = pin(connector, end_pin, pcb.B_Cu)
    queue, distances = [(0.0, start)], {start: 0.0}
    while queue:
        distance, position = heappop(queue)
        if distance > distances[position]:
            continue
        if position == end:
            return distance
        for next_position, step in copper[position]:
            candidate = distance + step
            if candidate < distances.get(next_position, float("inf")):
                distances[next_position] = candidate
                heappush(queue, (candidate, next_position))
    raise ValueError(f"Open path from U1.{source_pin} to {connector}.{end_pin} on {name}")


if __name__ == "__main__":
    if hasattr(pcb, "SwigPyIterator"):
        pcb.SwigPyIterator.next = pcb.SwigPyIterator.__next__
    board = pcb.LoadBoard(str(BOARD))
    assert board.GetCopperLayerCount() == 8
    sets = (
        [("CSI_D0_P", 43, "J7", 24), ("CSI_D0_N", 42, "J7", 23),
         ("CSI_CLK_P", 44, "J7", 27), ("CSI_CLK_N", 45, "J7", 26),
         ("CSI_D1_P", 47, "J7", 21), ("CSI_D1_N", 46, "J7", 20)],
        [("USB_D_P", 50, "J1", "A6"), ("USB_D_N", 49, "J1", "A7"),
         ("USB_D_P", 50, "J1", "B6"), ("USB_D_N", 49, "J1", "B7")],
    )
    for pins in sets:
        lengths = []
        for name, source, connector, end in pins:
            length = measure(board, name, source, connector, end)
            lengths.append(length)
            print(f"{name:10} U1.{source} to {connector}.{end}   {length:.4f} mm")
        assert max(lengths) - min(lengths) < .05, "Rev 3 CAD pin-to-pin skew exceeds 0.05 mm"
