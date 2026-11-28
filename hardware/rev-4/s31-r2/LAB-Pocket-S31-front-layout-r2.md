# LAB Pocket · front layout R2

The green marks on the 4-inch print identified two sets of margins. R2 applies those marks to both non-touch S31 variants. Each printed page is 1:1 on US Letter. [Desk-camera reference](reference/LAB-Pocket-front-markup-ipevo-r2.jpg) · [Dimensioned front and rear](review/LAB-Pocket-S31-panel-fit-letter-r2.pdf) · [Front with and without the screen](review/LAB-Pocket-S31-screen-off-letter-r2.pdf)

| Design | R2 board | Height increase | Top, left and right of glass | All four keypad margins | Switch-center pitch X × Y |
| --- | --- | --- | --- | --- | --- |
| [3.4-inch project](34/LAB-Pocket-S31-34-r2.kicad_pro) | 74 × 154.295 mm | 2.295 mm | 1.775 mm | 10.000 mm | 12 × 17 mm |
| [4-inch project](40/LAB-Pocket-S31-40-r2.kicad_pro) | 80 × 163.765 mm | 5.765 mm | 2.585 mm | 10.000 mm | 13.5 × 17 mm |

The widths carry forward from R1. The two 10 mm horizontal gaps are measured from the PCB edge to the outermost switch body. The vertical gaps run from the bottom of the glass to the uppermost solder land and from the lowest solder land to the board edge. LEDs, paired bypass capacitors and individual key legends fall within that rectangle. The screen margin is measured to the actual glass outline, which has its own asymmetric black border around the active image.

All 206 other front footprints, including both ribbon sockets, sit fully within the glass projection. Their footprint bounds have at least 0.55 mm horizontal clearance to the edge of that projection. Each key’s bypass capacitor stays alongside its pixel. The ceramic antenna and its matching components occupy the lower-left rear area, away from the glass. The USB ESD clamp sits behind the bottom connector area. The eleven service pads are on the rear and accessible with the panel installed.

The rear camera follows the active-image center. Moving the glass up on the 3.4-inch board also required moving the slot and front camera socket to preserve the estimated flex path and a 5 mm web to the top edge. The 4-inch board has a 6 mm web. The glass projection is a planar clearance check. Glass support, component-to-glass height, flex bend and antenna tuning need physical verification. The new RF feed also needs a controlled-impedance route and a loss check with the hand and battery in place.

Both exported projects passed ERC, placement DRC and schematic parity. Each board has 499 unrouted connections. [Measured margins and component coverage](validation/LAB-Pocket-front-dimensions-r2.txt) · [Electrical connectivity and FPC checks](validation/LAB-Pocket-S31-connectivity-r2.txt)

The two KiCad projects open directly with their bundled libraries and datasheets. For regeneration, prepare a new working copy using source/prepare-projects-r2.py and the S31 R1 study. The placement builder takes the Rev 3A PCB, the R2 project and its KiCad XML netlist. The front-dimension verifier operates on the saved boards. The drawing generator uses ReportLab, and its --inspection option produces the panel-removed comparison. Use fresh output paths for later revisions.
