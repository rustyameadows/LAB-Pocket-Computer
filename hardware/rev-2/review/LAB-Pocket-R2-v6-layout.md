# LAB Pocket Rev 2 v6

The keypad has four rows of five TL3301 switches. Numbers 01–20 read left to right from the top row. The outer columns stay in their v5 positions. The horizontal pitch is 12.75 mm and the vertical pitch is 16 mm. Each switch has an SK6805-EC10-000 in the upper terminal gap and a printed number in the lower gap. The front footer and rear USB legend have been removed.

The board is 74 × 152 mm with 2 mm corner radii. The bottom edge and rear USB4110 moved 6 mm beyond their v5 positions. Measured perpendicular to that edge, there is a 2.375 mm gap between the projected KiCad courtyards of the bottom-center switch (18) and USB-C. This compares the full assembly allowances on opposite faces, including the connector lands. It is a CAD measurement.

The PCA9555 scans rows on P0.0–P0.3 and reads columns on P1.0–P1.4. R29 is the fifth 10 kΩ column pull-up. Four extra BAS316 diodes fit under the LCD. LED13–LED32 run in row-major key order, each with a local 100 nF bypass. At 5 mA per channel, twenty keys at full white add approximately 300 mA to the 5 V rail before controller idle current. All added quantities use parts already in the component archive. [Parts list](../parts-v6.csv) · [Archived datasheets](../datasheets/index-v5.csv)

The [KiCad check](../check-keypad-v6.py) verifies all twenty key paths to the scanner, each pull-up connection to its column, the individual pixel data links and both local LED rails. Board-to-schematic parity passes. The overall board remains a prototype with 344 unrouted connections, 104 inherited ESP32-P4 clearance findings, and four inherited USB locator-to-pad clearance findings.

The paired images share the v5 camera angles, magnification, and lighting. Both pairs are shifted vertically by the same amount to fit the longer outline. [Assembled](../renders/LAB-Pocket-R2-v6-front-rear-assembled-r1.jpg) · [Screen and battery removed](../renders/LAB-Pocket-R2-v6-front-rear-screen-battery-removed-r1.jpg)
