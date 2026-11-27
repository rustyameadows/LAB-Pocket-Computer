# LAB Pocket Computer Rev 3

Rev 3 is the routed prototype of the 74 × 152 mm LAB Pocket Computer. It retains the v9b perimeter, 2 mm corner radius, bottom USB-C, side audio input, top speakers, bottom card slots, centered camera, 20 front switches and exposed rear battery. The 12 perimeter LEDs are Worldsemi WS2812B-V6. Each switch retains its own 1 mm SK6805-EC10 pixel. [Pixel specification](LEDs-R3.md)

The KiCad 10.0.6 board passes schematic parity and the configured design rules with zero unconnected items, zero reported errors or warnings and zero item exclusions. All 22 schematic sheets pass ERC. The JLC assembly BOM and placement file cover the same 344 reference designators, with 227 on the front and 117 on the rear. [KiCad project](kicad/LAB-Pocket-R3.kicad_pro) · [Schematic PDF](manufacturing/LAB-Pocket-R3-schematics-r1.pdf) · [DRC report](validation/LAB-Pocket-R3-DRC-r1.json) · [ERC report](validation/LAB-Pocket-R3-ERC-r1.json)

## Fabrication and assembly

| Use | File |
|---|---|
| Eight copper layers, both masks, silkscreens and paste layers, board profile and both drill files | [Fabrication ZIP](manufacturing/LAB-Pocket-R3-fabrication-r1.zip) |
| JLC double-sided assembly uploads | [BOM r2](manufacturing/LAB-Pocket-R3-JLC-BOM-r2.csv) and [CPL r1](manufacturing/LAB-Pocket-R3-JLC-CPL-r1.csv) |
| Order settings and high-speed constraints | [JLC stackup](manufacturing/stackup-R3-r1.md) |
| Per-part stock, special sourcing and hand assembly | [Sourcing snapshot r2](manufacturing/LAB-Pocket-R3-sourcing-r2.csv) |
| Schematic parts and five footprint-compatible assembly substitutions | [Parts and datasheets](parts-R3.csv) and [approved alternates](manufacturing/LAB-Pocket-R3-approved-alternates-r1.csv) |
| Battery polarity, sensor installation and electrical tests | [Battery assembly](battery-R3.md) |
| Measured CAD paths, checks and first-article test scope | [Verification record](validation/LAB-Pocket-R3-checks-r1.md) |

Use JLC08161H-3313, 1.6 mm nominal, black solder mask, ENIG and epoxy-filled, copper-capped through-vias. The fabrication plot, drill and placement origin is the lower-left extent of the board. Placement angles are KiCad angles. Before releasing assembly, check the vendor's rotation preview against pin 1 on both faces, including the USB receptacle, camera connector, host QFN and all addressable pixels.

The November 27, 2026 inventory snapshot still requires sourcing for the ESP32-P4, camera connector, external PSRAM, two 2.8 V regulators and audio codec. The selected tactile switch also has a shortfall. Reserve or consign those exact parts before authorizing assembly. The battery, thermistor harness, panel, camera, speakers and adhesives are hand-fit items. [Item quantities and JLC part numbers](manufacturing/LAB-Pocket-R3-sourcing-r2.csv)

The charger supports a protected, bonded Jauch 246524 pack. Its wired thermistor, hardware charge inhibit, fuel gauge and USB input-current selection are part of the board. Qualify the first assembly with a battery simulator before attaching the cell. [Charge circuit and test procedure](battery-R3.md)
