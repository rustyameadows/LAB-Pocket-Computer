# Rev 2 v4 · electronics beneath the display

The front face exposes the 16 keys, 14 touch electrodes and display. Removing the display gives access to the PCA9555 keypad expander, CY8CMBR3116 touch controller, 16 BAS316 steering diodes, nine resistors and capacitors, five SWD/debug pads and the display connector. The flex folds between the connector and the lower edge of the panel.

The modeled backlight sits 2.80 mm above the front PCB surface. The PCA9555 TSSOP has a 1.20 mm maximum package height, leaving 1.60 mm nominal headroom at that chip before assembly tolerances, board bow and display deflection. The diode package is 1.10 mm maximum. A physical sample is needed to verify loaded clearance. [PCA9555 drawing](../datasheets/PCA9555PW.pdf) · [BAS316 drawing](../datasheets/BAS316.pdf)

The keypad switch-to-diode traces run on the second inner copper layer. The original 17 × 16 mm key pitch is preserved. The five debug pads are accessible with the screen lifted.

## Rear pouch

The entire 59.5 × 78.5 mm pouch footprint reserves the rear face for a smooth mounting surface. Mask-covered copper, internal copper and vias tented on the battery side can use this area. Components can use the opposite face of the PCB subject to their own clearance and temperature limits. The 0.17 mm tape bondline provides no usable space for mounted parts between the strips. Physical retention, insulation and temperature rise still need validation. [Jauch pack drawing](../datasheets/LP735977JH.pdf) · [3M tape](../datasheets/3M-9495LE.pdf) · [Jauch integration guide, section III](https://www.jauch.com/downloadfile/5c8fa8421814625c73ecb3a6beacac920/white_paper_guide_to_the_design_of_lipo_batteries_02-2019_en.pdf)

J5's pad 2 formerly extended 1.85 mm into the pouch footprint. The jack moved 2.50 mm toward the bottom and 1.35 mm inboard. Its nearest solder land now clears the pouch outline by 0.65 mm nominally. The matrix shifted 2.00 mm toward the bottom to clear the jack locating pins. Both speaker centers moved 1.55 mm toward the bottom, and R16 moved clear of the jack. Check plug shoulder access and the 0.65 mm placement margin with physical parts. The KiCad area excludes both rear footprints and rear pads.

## Verification

The footprint check covers all 32 relocated front footprints, the display rails, display connector, flex corridor, rear pouch and battery-side via tenting. KiCad DRC reports zero shorts, courtyard overlaps, keepout violations and schematic mismatches. The layout still has 388 open connections and 108 existing violations in the ESP32-P4 and USB connector footprints. This is a placement prototype.

[KiCad project](../kicad/LAB-Pocket-R2-v4.kicad_pro) · [Blender assembly](../blender/LAB-Pocket-R2-v4.blend) · [Assembled and screen-off views](../renders/LAB-Pocket-R2-v4-under-screen.jpg)
