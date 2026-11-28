# LAB Pocket Computer · Rev 4 S31 · R1

Open either project in KiCad 10. Each contains 27 schematic sheets and an eight-layer placement board. Both use the bare ESP32-S31NRV16 and the Seeed 114993115 autofocus OV5640 module. Their host, camera, connector pinouts, battery and peripherals are electrically identical. DS601 and its firmware timing profile identify the panel fitted to each.

| Design | Panel | Body including bezel | Proposed PCB | Editable project | Full schematic |
| --- | --- | --- | --- | --- | --- |
| Compact | Adafruit 5825, 3.4-inch 480 × 480, non-touch | 70.45 × 70.32 × 1.89 mm | 74 × 152 mm | [Open compact project](34/LAB-Pocket-S31-34-r1.kicad_pro) | [Compact schematic PDF](review/LAB-Pocket-S31-34-schematics-r1.pdf) |
| Large | Adafruit 5795, 4-inch 720 × 720, non-touch | 74.83 × 78.98 × 1.46 mm | 80 × 158 mm | [Open large project](40/LAB-Pocket-S31-40-r1.kicad_pro) | [Large schematic PDF](review/LAB-Pocket-S31-40-schematics-r1.pdf) |

Print the two-page fit sheet on US Letter at 100%. It shows each complete front and rear, the real active area, the camera, both ribbon sockets and the battery. The scale bar should measure exactly one inch. [Full-size fit comparison](review/LAB-Pocket-S31-panel-fit-letter-r1.pdf)

### Electrical changes

U1 drives the 16-bit RGB565 LCD bus and receives the camera’s eight-bit DVP bus. Its dedicated USB 2.0 high-speed device signals terminate at the bottom USB-C receptacle. The external NOR provides 16 MB of flash, and the S31 package contains 16 MB of PSRAM. The onboard antenna replaces the Rev 3A companion radio. The combined display, DVP, storage, RP2350B and audio interfaces use all 54 application GPIOs after the six flash signals. The second PCA9555 at address 0x21 handles slow controls. Backlight PWM uses an S31 pin. The RP2350B retains its original SPI bus and separate SWD recovery pads. [Host pin map and RF design](host-r1.md)

J501 takes the Seeed autofocus flex through the same bottom-contact Jushuo receptacle used on Seeed’s carrier. The camera’s 1.8 V digital interface uses directional translation. Separate enables sequence the digital and 2.8 V analog/autofocus rails. J601 mates to either display through a 40-contact Omron socket. Each backlight string has an independent regulated current sink. The 3.4-inch ST7701S needs a 9-bit serial initialization sequence. The 4-inch Y17B uses the module defaults and a different RGB raster timing. RGB565 framebuffers occupy 460,800 and 1,036,800 bytes respectively. The 4-inch panel takes 2.25 times the framebuffer bandwidth at the same refresh and pixel format. [Camera circuit and sequencing](camera-r1.md) · [Panel timings, initialization, and backlight](panel-r1.md)

The Jauch pack, battery interlock, USB current detection, four microphones, stereo codec and amplifier, IMU, 20 individually illuminated switches, 12 perimeter LEDs, and dual microSD sockets carry forward from Rev 3A. Both designs use the existing bonded pouch without a back cover. R42/R43 and U18’s forced-PWM selection give the shared logic rail a 3.2235 V nominal target. The calculated static interval is 3.1834–3.2638 V. This gives headroom for both the RP2350B analog supply and the panel’s 3.30 V maximum. Measure ripple, startup overshoot and RF load steps at the actual devices; forced PWM also affects idle battery life. [Verification results](validation/LAB-Pocket-S31-connectivity-r1.txt)

### Placement decisions

- The compact carrier preserves the 74 × 152 mm Rev 3A outline. A centered panel body leaves 1.775 mm per side. The large carrier adds 6 mm in width and length. It leaves 2.585 mm per side. Both use 2 mm outside corner radii.
- The optical center is aligned to the **active pixels**. The 3.4-inch panel’s asymmetric bezel moves that center about 1.06 mm left of the PCB center. The pack keeps its 59.5 × 78.5 mm rear footprint. Use the Jauch drawing’s 7.9 mm cycled thickness when checking rear clearances.
- The camera tail reaches from the rear lens through a 14 × 4 mm internal slot to the front J501 under the display. The traced fold assumes a 1.5 mm radius and the manufacturer’s seated-contact geometry. Confirm insertion, bend radius, a smooth insulated bearing surface, and local cable-guide and panel standoff heights with the actual flex. Install and latch both ribbons before securing the glass. Screen support, adhesive and the bend guide still need a mechanical design and physical fit test.
- The screen tail turns back toward the top of the device. J601 faces the lower edge. The candidate location allows a 1.5 mm bend radius with a 1 mm straight section beyond the lower glass edge. Verify the folded tail, its stiffener islands, all mounted components under the glass and clearance to the first row of keys. Neither Rev 3A’s smaller display frame nor its display Z stack has been qualified on these boards.
- ANT401 has a 6.5 × 6.5 mm local keepout, extended to the physical board edge. Its placement includes a 0.55 mm inset from the square-corner reference to clear the R2 outside curve. The check from KiCad covers pads, drilled holes and courtyards. Antenna match, RF performance in a hand, USB impedance, bus skew and power returns remain routing and prototype tasks.

### Build status

KiCad 10.0.6 reports **zero ERC violations, zero placement-rule violations, zero schematic-to-PCB parity mismatches, and 499 unrouted connections on each board**. The independent audit checked the 81 S31 pads, 265 retained Rev 3A components and 876 of their terminals, translated camera lanes, panel bit order, USB polarity, 372 physical footprints and 1,389 numbered lands on each board. The source checks include identical electrical connectivity between variants. [Validation reports](validation)

The next electrical milestone is a reviewed routing pass. First place the RF matching network and processor bypass parts against their actual U1 pins, resolve the backlight driver’s center-ball escape with the chosen fabricator, then route USB, clock/flash and the parallel video buses over continuous return planes. Complete the power loops and remaining interfaces, and repeat DRC and impedance/length checks. Fabrication follows mechanical ribbon and screen-support sign-off. Firmware for the S31 port, camera capture and panel-specific initialization has not been built or tested in this revision.

All purchased symbol references resolve to a local datasheet. The eleven etched test points are PCB features. The external display and camera appear separately in the schematic BOM as hand-installed parts. [Component and datasheet index](datasheet-index-r1.md)

### Reproduction

The checked-in native projects open directly. Rebuilding the electrical sheets starts from the repository’s hardware/rev-3a directory and the configuration under source. Use a separate working copy of this revision for regenerating files. Keep the bundled libraries and datasheets with both project directories. The independent checker expects KiCad XML netlists exported with the kicadxml format. Running it with the system Python also checks the physical PCB pads.

```sh
python3 source/build-schematics-r1.py ../../rev-3a .
kicad-cli sch export netlist --format kicadxml -o /tmp/LAB-r3a.xml ../../rev-3a/kicad/LAB-Pocket-R3A.kicad_sch
for v in 34 40; do
  p="$v/LAB-Pocket-S31-$v-r1"
  kicad-cli sch export netlist --format kicadxml -o "/tmp/LAB-s31-$v.xml" "$p.kicad_sch"
  /usr/bin/python3 source/build-placement-r1.py ../../rev-3a/kicad/LAB-Pocket-R3A.kicad_pcb "$p.kicad_pro" "/tmp/LAB-s31-$v.xml"
done
/usr/bin/python3 source/verify-r1.py --baseline /tmp/LAB-r3a.xml --pcb34 34/LAB-Pocket-S31-34-r1.kicad_pcb --pcb40 40/LAB-Pocket-S31-40-r1.kicad_pcb /tmp/LAB-s31-34.xml /tmp/LAB-s31-40.xml
```
