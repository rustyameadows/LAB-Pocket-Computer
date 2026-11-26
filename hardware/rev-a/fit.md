# Rev A · bare-board dimensional basis

The layout uses the flat-pack variant and the RGB panel from the preliminary BOM. Distances are in millimetres. Board dimensions are design choices. Supplier dimensions describe bodies. Solder joints, spring travel, adhesive, flex bends and assembly tolerances need separate clearance.

| Assembly | Dimension carried into the design | Evidence and limits |
| --- | --- | --- |
| TTC273XSI-01 display | 53.54 × 58.74 × 2.50 body, 48.96 × 48.96 active, 40 contacts at 0.50 pitch | Electrical interface on pp. 4–6 and mechanical drawing on p. 16. Uses 18-bit parallel RGB and three serial configuration lines. [Tailor Pixels drawing](https://tailorpixels.com/wp-content/uploads/2024/09/TTC273XSI-01.pdf) |
| Jauch LP735977JH | 59.5 × 78.5 max plan, 7.3 at delivery, 7.9 after cycling | Model the larger thickness and allow separate space above it. 70 mm leads need a guided exit, insulating tray and keyed connector. [Jauch pack drawing](https://www.bce.it/wp-content/uploads/2019/11/LP735977JH-4800mah_-_lp735977jh_1s1p_2_wire_70mm_BCE.pdf) |
| E-Switch TL3301NF160QG | 6 × 6 body, 4.3 height | Front switches use the corresponding library footprint and STEP model. Black actuator, 160 gf nominal. [E-Switch drawing](https://www.e-switch.com/wp-content/uploads/2024/03/TL3301.pdf) |
| RP2350B / ESP32-P4 | Both 10 × 10, QFN80 / QFN104 | Package bodies have different lands and power requirements. [Raspberry Pi](https://www.raspberrypi.com/products/rp2350/) · [Espressif](https://documentation.espressif.com/esp32-p4_datasheet_en.pdf) |
| ESP32-C6-MINI-1 | 13.2 × 16.6 × 2.4 nominal | Antenna clearance needs its own placement review. [Espressif mechanical drawing](https://documentation.espressif.com/esp32-c6-mini-1_mini-1u_datasheet_en.pdf) |
| PUI AS01808AO-SC18-WP-R, two | 18 × 13 × 2.8 published body | Reserve 3.5 high for spring/contact travel until seating and chamber drawings are reconciled. [PUI Audio](https://puiaudio.com/product/speakers-and-receivers/AS01808AO-SC18-WP-R) |
| IM70D122V01, four | 3.50 × 2.65 × 0.98 nominal | Bottom acoustic inlet. PCB port, sealing ring and acoustic mesh are critical. [Infineon drawing, fig. 13](https://www.infineon.com/assets/row/public/documents/30/49/infineon-im70d122-datasheet-en.pdf) |
| Seeed 114992267 IMX219 | 6.5 × 6.5 lens footprint only | Replacement optical module. Flex, mating connector, bias supplies and driver/carrier envelope remain to be measured. [Seeed specifications](https://www.seeedstudio.com/IMX219-77-Camera-77-FOV-Applicable-for-Raspberry-Pi-V2-Camera-p-4605.html) |
| VEML3328 | 2.0 × 1.25 × 1.0 | Model the sensing window separately from the illumination path. [Vishay drawing](https://www.vishay.com/docs/84968/veml3328.pdf) |

## Fit measured in the model

| Measurement | Result | Basis |
| --- | ---: | --- |
| Board profile | 82 × 146 × 1.60 | KiCad Edge.Cuts centerline, 4.5 radius outside corners, 4 copper layers |
| Touch electrodes | 7.60 × 5.00, 7.25 pitch | Seven exposed gold pads per side. Panel body to nearest pad is 2.03 on each side |
| Key pitch | 17 horizontal, 16 vertical | Switch centers span 51 × 48. Inboard service fasteners sit outside the grid |
| USB pocket | 11.6 wide × 1.8 deep | Bottom-center edge relief for rear J1. Check the overmold of an actual USB cable |
| Battery guard | 64 × 84 outside, 61.4 × 81.4 cavity | Maximum-cell clearance is 0.95 per side and 1.45 per end. Body keepout is recorded on the PCB |
| Front stack above front PCB face | 2.8 support + 2.5 LCD = 5.3 | Nominal rail adhesive/support allowance includes under-panel FPC connector |
| Rear section below back PCB face | 1.05 to pouch + 7.90 pouch + 1.30 air + 1.20 roof + 2.20 foot = 13.65 | The 0.45 liner sits within the first 1.05. The cavity uses the supplier's maximum cycled pouch thickness |
| Full assembled depth | 20.55 | 5.30 front + 1.60 board + 13.65 rear. Nominal and uncompressed. Excludes production stack tolerances |
| J6 service margin | 0.375 | Guard edge to battery receptacle courtyard. Mating housing and 70 mm lead dressing need a service trial |

The inspiration's 63.5 mm width would leave 4.98 mm on either side of the selected panel before adding electrodes. Each electrode here is 7.60 mm wide. The reference's 9 mm depth is also less than the 7.9 mm cycled pouch plus the 1.6 mm board alone. Rev A preserves the front arrangement at a size that accommodates these parts.

The large corner holes in the reference have been removed. Four 2.2 mm service holes sit inboard for the guard tabs. The bumper feet mount to the guard. They do not pierce the PCB.

## Checks still requiring hardware

- **LCD.** The 27.23 mm nominal tail folds beneath the display into J2. Fold direction, minimum bend radius, insertion depth, contact face, adhesive thickness and assembly order need a panel and connector. The Blender ribbon is a swept envelope.
- **Battery.** The guard, liner, tabs and retention studs are custom study geometry. The scene shows abbreviated wire dressing. Verify the guard relief, lead strain relief, protected pack tolerances and electrical isolation on the actual 70 mm leads. The two-wire pack supplies no temperature lead. Charging is inhibited in the schematic pending a qualified temperature-sensing arrangement.
- **Ports and mechanics.** Check headphone and USB overmolds, card insertion and extraction, local PCB stiffness, access to the internal card and guard removal. Verify camera height, flex/cable routing, antenna clearance, speaker contact travel and microphone seals. Lens footprint is documented. The modeled camera carrier and optics height are provisional.
- **Board finishing.** Gold touch pads are solder-mask openings in copper. Fabrication finish, tactile-surface lifetime, board edge finish and insulation still need a production specification.

[Full-scale A3 drawing](review/LAB-Pocket-fit.pdf) · [Component and document concordance](parts.csv) · [Original documents and checksums](datasheets/index.csv)
