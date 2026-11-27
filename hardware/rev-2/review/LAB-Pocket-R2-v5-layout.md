# LAB Pocket Rev 2 v5

The board measures 74 × 146 mm. All four corners have a 2 mm radius, reduced from 4.5 mm in v4. The headset mounting clearance required moving the switch grid 2.25 mm toward the bottom. The key pitch remains 17 × 16 mm.

Each TL3301 switch is rotated 90°. A 1.1 × 1.1 × 0.33 mm SK6805-EC10-000 sits between the upper solder lands. The gap measures 3.10 mm, leaving 1.00 mm on each side of the nominal LED body. Its number, 01 through 16, is printed between the lower lands. LED13 through LED28 follow the twelve perimeter LEDs in row-major order. Each has a local 100 nF bypass. Full white across the sixteen added LEDs calls for about 240 mA at 5 V before controller idle current. The switched 5 V supply still needs sizing and validation. [OPSCO drawing and application circuit](../datasheets/SK6805-EC10-000.pdf)

The GCT USB4110-GF-A mounts entirely on the rear surface for USB 2.0 data and power. The four shell tabs solder to rear copper. Two plastic locating pegs use 0.65 mm unplated through holes, visible from the front. The socket opens at the straight bottom edge. The STEP envelope is drawn from GCT’s dimensions. JLCPCB lists the part as C5143397 for Economic and Standard assembly. [GCT drawing](../datasheets/USB4110-GF-A.pdf) · [JLCPCB part](https://jlcpcb.com/partdetail/5762033-USB4110_GFA/C5143397)

KiCad found no schematic-to-board mismatches. The routed keypad data links and both local rails pass the [connectivity check](../check-keypad-v5.py). The board is a placement prototype with 387 outstanding connections. KiCad reports 104 ESP32-P4 clearance findings and four USB pad-to-locator clearance findings. The tightest J1 clearance measures 0.1944 mm against the project's 0.25 mm rule. Resolve the connector footprint clearance and finish routing before ordering.

[Parts list](../parts-v5.csv) · [Datasheet archive index](../datasheets/index-v5.csv) · [Assembly and close-ups](../renders/LAB-Pocket-R2-v5-keypad-and-usb.jpg)
