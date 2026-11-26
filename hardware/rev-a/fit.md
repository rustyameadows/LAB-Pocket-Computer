# Rev A · bare-board dimensional basis

The layout uses the flat-pack variant and the RGB panel from the preliminary BOM. Distances are in millimetres. Board dimensions are design choices. Supplier dimensions describe bodies; solder joints, spring travel, adhesive, flex bends and assembly tolerances need separate clearance.

| Assembly | Dimension carried into the design | Evidence and limits |
| --- | --- | --- |
| TTC273XSI-01 display | 53.54 × 58.74 × 2.50 body, 48.96 × 48.96 active, 40 contacts at 0.50 pitch | Manufacturer spec pp. 4–6. Uses 18-bit parallel RGB and three serial configuration lines. [Tailor Pixels drawing](https://tailorpixels.com/wp-content/uploads/2024/09/TTC273XSI-01.pdf) |
| Jauch LP735977JH | 59.5 × 78.5 max plan, 7.3 at delivery, 7.9 after cycling | Model the larger thickness and allow separate space above it. 70 mm leads need a guided exit, insulating tray and keyed connector. [Jauch pack drawing](https://www.bce.it/wp-content/uploads/2019/11/LP735977JH-4800mah_-_lp735977jh_1s1p_2_wire_70mm_BCE.pdf) |
| E-Switch TL3301, N actuator | 6 × 6 body, 4.3 height | Front switches use the corresponding library footprint and STEP model. Order code and force remain open. [E-Switch drawing](https://www.e-switch.com/wp-content/uploads/2024/03/TL3301.pdf) |
| RP2350B / ESP32-P4 | Both 10 × 10; QFN80 / QFN104 | Package bodies have different lands and power requirements. [Raspberry Pi](https://www.raspberrypi.com/products/rp2350/) · [Espressif](https://documentation.espressif.com/esp32-p4_datasheet_en.pdf) |
| ESP32-C6-MINI-1 | 13.2 × 16.6 × 2.4 nominal | Antenna clearance needs its own placement review. [Espressif mechanical drawing](https://documentation.espressif.com/esp32-c6-mini-1_mini-1u_datasheet_en.pdf) |
| PUI AS01808AO-SC18-WP-R, two | 18 × 13 × 2.8 published body | Reserve 3.5 high for spring/contact travel until seating and chamber drawings are reconciled. [PUI Audio](https://puiaudio.com/product/speakers-and-receivers/AS01808AO-SC18-WP-R) |
| IM70D122V01, four | 3.50 × 2.65 × 0.98 nominal | Bottom acoustic inlet. PCB port, sealing ring and acoustic mesh are critical. [Infineon drawing, fig. 13](https://www.infineon.com/assets/row/public/documents/30/49/infineon-im70d122-datasheet-en.pdf) |
| Seeed 114992267 IMX219 | 6.5 × 6.5 lens footprint only | Replacement optical module. Flex, mating connector, bias supplies and driver/carrier envelope remain to be measured. [Seeed specifications](https://www.seeedstudio.com/IMX219-77-Camera-77-FOV-Applicable-for-Raspberry-Pi-V2-Camera-p-4605.html) |
| VEML3328 | 2.0 × 1.25 × 1.0 | Model the sensing window separately from the illumination path. [Vishay drawing](https://www.vishay.com/docs/84968/veml3328.pdf) |

## Outline and approach

Start with an 82 × 146 × 1.6 PCB and rounded 4.5 mm corners. The display and sixteen unshrouded keys share the front with fourteen touch electrodes. A removable insulated battery guard occupies only part of the rear, leaving board edges, expansion and optical surfaces accessible. The CAD study establishes nominal fit. Physical samples and fabrication drawings are required to release land patterns and lock tolerances.
