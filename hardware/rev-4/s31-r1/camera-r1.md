# Seeed 114993115 autofocus camera

The board accepts the separately sold 5 MP OV5640 autofocus flex marked MJY5OAF-F3M-V1. J501 is Jushuo AFC01-S24FCC-00, the exact receptacle Seeed populated at JA1 on its XIAO Sense carrier. The camera and its supplied heatsinks arrive as a separate hand-fit item. [Retail module and drawing](https://www.seeedstudio.com/OV5640-Camera-for-XIAO-ESP32S3-Sense-With-Heat-Sink-p-5739.html) · [Seeed carrier CAD](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_ESP32S3_ExpBoard_v1.0_SCH%26PCB_230324.zip) · [J501](https://jlcpcb.com/partdetail/JUSHUO-AFC01_S24FCC00/C262276)

## Connector orientation and continuity

The Seeed retail drawing, page 3, shows the exposed contacts facing the reader, the tail tip pointing down and flex contact 1 at the right. The Jushuo drawing identifies circuit 1 at the left in the top view with the mouth toward the reader. The board uses Jushuo's circuit numbers. Seeed’s Eagle JA1 land instead calls the rightmost solder land “1”. The resulting mating rule is **J501 pad = 25 − flex contact**. The exposure is on the side opposite the lens. Insert the flex contact side toward the PCB.

| Flex | J501 | Function | Flex | J501 | Function |
|---:|---:|---|---:|---:|---|
| 1 | 24 | Strobe, open | 13 | 12 | MCLK/XCLK input |
| 2 | 23 | Analog ground | 14 | 11 | Y8, host D6 |
| 3 | 22 | SCCB data, 1.8 V | 15 | 10 | Digital ground |
| 4 | 21 | Analog 2.8 V | 16 | 9 | Y7, host D5 |
| 5 | 20 | SCCB clock, 1.8 V | 17 | 8 | PCLK output |
| 6 | 19 | Active-low reset | 18 | 7 | Y6, host D4 |
| 7 | 18 | VSYNC | 19 | 6 | Y2, host D0 |
| 8 | 17 | PWDN, active high | 20 | 5 | Y5, host D3 |
| 9 | 16 | HSYNC/HREF | 21 | 4 | Y3, host D1 |
| 10 | 15 | Internally supplied 1.5 V core, bypass only | 22 | 3 | Y4, host D2 |
| 11 | 14 | Digital I/O 1.8 V | 23 | 2 | AF ground |
| 12 | 13 | Y9, host D7 | 24 | 1 | VCM supply 2.8 V |

Pads 25 and 26 ground the mounting tabs. J501 uses the component supplier’s land pattern. Crossing the signal row from left to right with the mouth down, pad 1 is at x = −5.75 mm and pad 24 at +5.75 mm. The signal lands are 0.30 × 1.30 mm. The fitting lands are 2.00 × 1.60 mm, centered at x = ±7.45 mm and y = +2.70 mm. The camera pages derive their voltage rails from the retail flex drawing. Seeed’s older multi-camera carrier schematic uses different camera supply wiring. [Exact flex drawing](https://files.seeedstudio.com/wiki/OV5640_for_ESP32S3_sense/OV5640_Datasheet.pdf) · [Reference carrier schematic](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_ESP32S3_ExpBoard_v1.0_SCH.pdf)

## Power, signal direction and firmware

1. Before applying sensor power, preload the expander output latch to CAM_ENABLE=0, CAM_ANALOG_ENABLE=0, CAM_PWDN=1 and CAM_RESET_N=0. Then set those bits to outputs. The camera sheet supplies these startup biases and keeps both DVP translators disabled until the analog enable rises.
2. Raise CAM_ENABLE to power the digital I/O and the SCCB translator. After the 1.8 V rail settles, raise CAM_ANALOG_ENABLE to power both 2.8 V branches. The lens motor and sensor analog supply each have a separate ferrite and connector-side bypass. For first bring-up, use 10 ms between enables and measure the actual settle time.
3. Wait at least 5 ms after analog voltage settles. Start XCLK, drive PWDN low, wait at least 1 ms, then release RESET. Wait at least another 20 ms before initializing the sensor. Begin at 100 kHz SCCB and test a conservative DVP mode. The sensor uses 7-bit address 0x3C. Read 0x300A/0x300B and expect 0x56/0x40.
4. Configure U503’s host pins as inputs. U503 translators have DIR1=DIR2=0 and pass all eight data channels from B (camera) to A (host). U504 has DIR1=DIR2=1. Channels 1–4 pass from A to B. Channels 5–8 pass from B to A. Host XCLK, PWDN and RESET therefore drive the camera, while PCLK, HREF and VSYNC drive the host. The TCA9406 provides bidirectional SCCB translation, internal 10 kΩ pullups and power-off isolation. The 3.3 V system bus also has its host pullups.
5. Load the OV5640 autofocus firmware after sensor configuration. Request autofocus over SCCB and read the reported focus status. Compare near/far targets optically after each complete power cycle.
6. Before switching off, set PWDN high, assert RESET low and stop XCLK. Disable the analog/AF rail, wait for it to discharge, then disable the 1.8 V rail. Scope the shutdown before assigning the minimum production firmware delay.

[OmniVision sensor timing, §2.7.1](https://cdn.sparkfun.com/datasheets/Sensors/LightImaging/OV5640_datasheet.pdf) · [TI AXC8 direction table 7-1](https://www.ti.com/lit/ds/symlink/sn74axc8t245.pdf) · [TI TCA9406](https://www.ti.com/lit/ds/symlink/tca9406.pdf) · [Seeed autofocus example](https://wiki.seeedstudio.com/xiao_esp32s3_camera_usage/#ov5640-autofocus)

## Mechanical datums

The flex tip to far head edge measures 70.5 ±0.2 mm. The head is 8.5 ±0.2 mm square and the image shows its optical axis centered, giving a **nominal 66.25 mm from flex tip to optical axis along the flat tail**. The optical-center position has no separate tolerance on this drawing. The neck is 6.0 ±0.1 mm wide, the terminal is 12.5 ±0.1 mm wide, the insertion thickness is 0.30 ±0.03 mm and the flex neck is 0.12 ±0.03 mm thick. The complete head is 5.4 ±0.2 mm high before either heatsink is fitted. J501 closes to 2.0 mm and requires approximately 3.6 mm of clearance to open.

Jushuo section A–A dimensions the receiver mouth to the back-contact datum at 2.8 mm. Using this nominal datum gives **63.45 mm of developed tail length from the mouth to the optical axis**. Measure the hard-stop seating depth on an actual pair and substitute the measured value in the placement formula. The closed housing is about 6.1 mm deep including leads. The flex drawing gives no minimum bend radius or durability rating.

The selected layout uses J501 on the front face under the screen, with the mouth facing the top edge. It permits one 180° wrap through a horizontal slot in the PCB to the rear-mounted camera. This rotation brings the lens to the outside rear. A bottom-contact receptacle and camera both mounted on the same face need an even number of half-turns to preserve lens orientation. A two-return vertical fold creates a thickness stack of about four bend radii when the three runs overlap without touching. Reserve camera shipping/heat-sink clearance independently. Fit the cable before installing the screen.

For a front-to-rear slot layout, measure board Y downward in the front view and let yC be the rear optical-center Y, yT the wrap’s tangent Y and R the bend centerline radius. With parallel straight runs, an ideal semicircle and no tension, the approximate mouth position is yJ = 2yT − yC + 63.45 − πR. The plane separation across that bend is 2R. A 14 mm wide by 4 mm deep radiused through-slot with its south lip at yC − 30 mm gives the following placement model for an illustrative R = 1.5 mm static guide. The PCB slot, the display clearance and the radius must be qualified separately for each board.

| Display | Optical center X, Y (mm) | Proposed slot Y span (mm) | Calculated mouth X, Y (mm) |
|---|---|---|---|
| 3.4-inch | 99.945, 82.140 | 48.140–52.140 | 99.945, 80.878 |
| 4.0-inch | 101.000, 79.415 | 45.415–49.415 | 101.000, 78.153 |

The placement numbers reference the mouth, while the footprint origin is the center of the signal-land row. The manufacturer’s dimensioned pad and dashed housing drawings give a nominal +5.70 mm mouth offset in the unrotated footprint. At 180° on the front, the pad-row origin is approximately 5.70 mm south of the mouth. The trial origins are (99.945, 86.578) and (101.000, 83.853) mm. Verify this drawing-derived offset and the actual flex seating against a sample. The upper slot frees the rear battery area. Thread the tail before latching the connector. Use a smooth formed guide and support the neck beyond each stiff region. Confirm room for the 12.5 mm wide terminal during insertion, the open latch beneath the panel, clearance to either speaker and the final heatsink. Compare the actual selected layout to these datums before fabricating.

## Prototype verification

- With power off, insert a numbered passive breakout tongue or a known-ground reference flex to check mating handedness. Confirm the three ground fingers 2/15/23, the analog and AF supply fingers 4/24, and digital I/O finger 11. Keep the internal core finger 10 isolated from both external regulators.
- With the module removed, measure both rail voltages and verify the 2.8 V branch discharges before digital I/O switches off. On the first module, current-limit the bench supply, measure AF inrush and monitor the head and pouch temperatures in the assembled stack.
- Scope XCLK at J501 and compare D0–D7 timing at the host with translated PCLK. Check HREF, VSYNC, static color bars, frame drops and autofocus at the highest required operating mode while the panel and audio are active.
- Dry-fit the real module before committing its adhesive or selecting a heatsink. Measure lens-to-mouth length, local bend radius, assembled Z and image pointing. Validate that the slot or return path leaves the pouch clear under flex and hand pressure.
