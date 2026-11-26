# LAB Pocket Computer · Rev 2

The Rev 2 bare board measures **74 × 146 mm**. The exposed Jauch pack bonds to the rear PCB. The nominal maximum-cycled stack is **14.97 mm** from the front display surface to the back of the pouch. Rev A measured 82 × 146 × 20.55 mm.

[Actual-size US Letter drawing](review/LAB-Pocket-R2-letter-v1-core.pdf) · [Rear render](renders/LAB-Pocket-R2-rear.png) · [Front render](renders/LAB-Pocket-R2-front.png) · [Full Blender assembly](blender/LAB-Pocket-R2.blend) · [Assembled GLB](blender/LAB-Pocket-R2-assembled.glb) · [KiCad project](kicad/LAB-Pocket-R2.kicad_pro) · [Nine schematic sheets](review/LAB-Pocket-R2-schematics.pdf)

## Mechanical layout

- The 59.5 mm pouch width sets the board width. Each side adds a 1.25 mm pouch-to-LED gap, a 5 mm LED body and 1 mm from that body to the PCB edge. The 53.54 mm LCD leaves 1.43 mm between its body and each 7.6 mm touch electrode. Switches retain their 17 × 16 mm pitch. All sixteen have individual references on the drawing.
- Both rear Hirose slots open toward the short top edge. From the rear, external J4 is on the left and internal J3 is on the right. Their origin points are 22 mm to either side of the centerline and 20.2 mm down from the top. Each slot has a clear card approach. J3 includes the seated card.
- The twelve LEDs form two six-pixel columns. LED12 starts at the upper left in rear view. Centers are 3.5 mm from the side edges, at 10.5, 35.5, 60.5, 85.5, 110.5 and 135.5 mm down the board. The top microphones moved below the top LEDs to keep the card approaches clear.
- The rear lens is directly behind the center of the active display at **37.00 mm from either side and 37.06 mm from the top**. This leaves 1.69 mm from the nominal camera carrier to the pouch. The headset jack moved to the lower side and the speakers moved down 3 mm for clearance.
- The guard, four feet, tabs, studs and guard mounting holes have been removed. The pouch is the outermost surface on the back.

## Pack and bond

The 4,800 mAh LP735977JH has a 59.5 × 78.5 mm maximum footprint. Jauch specifies 7.3 mm at delivery and 7.9 mm after cycling. The model uses the cycled envelope and includes a folded laminate rim, a shallow protection-board end, two separate wire exits, and label artwork taken from the manufacturer's drawing. The short-end details are visual approximations. Each modeled lead is 70 mm from its pad to its J6 terminal. The service loops and termination are proposed integration geometry. The supplier part comes with wire leads. [Jauch source drawing, p. 1](datasheets/LP735977JH.pdf)

Two candidate 20 × 55 mm strips of 3M 9495LE bond the pack to the rear solder mask. The installed tape thickness is 0.17 mm. The dimensional stack is 6.90 mm from the back of the PCB to the front display, plus 0.17 mm of bondline and 7.90 mm of pouch. The pack area excludes rear components and the matrix vias are tented on the pack side. [3M technical data](datasheets/3M-9495LE.pdf)

Confirm wrapper-to-adhesive compatibility with the pack supplier and validate retention, swelling clearance, insulation and wire dressing on a physical sample. The exposed pouch and its protection circuitry remain accessible to contact. Pocket carry, drops and abrasion require mechanical validation.

## Review status

KiCad and Blender checks confirm the dimensions above. PCB DRC reports **zero courtyard overlaps, keepout violations, shorts or schematic-parity mismatches**. Electrical completion is open. There are 388 unrouted connections and 108 inherited DRC violations, comprising 104 ESP32-P4 pad-clearance violations and four USB-C pad-to-hole clearance violations. ERC reports 143 errors and 18 warnings. Camera electrical integration, power, clocking, radio and high-speed routing require further work. Charging remains inhibited in the study schematic.

Run the board checker with the system Python containing KiCad 10's pcbnew module. The Blender checker reads the evaluated assembly at frame 1. The assembled GLB uses metres, while the Blender scene and drawing use millimetres. The second GLB contains the KiCad board export alone.

```sh
/usr/bin/python3 check-fit-R2.py
blender -b blender/LAB-Pocket-R2.blend --python-exit-code 1 -P check-scene-R2.py
```

[Rev 2 BOM](parts.csv) · [Index and SHA-256 digests for all 32 supplier documents](datasheets/index.csv)
