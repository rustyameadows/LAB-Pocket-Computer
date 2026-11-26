# Preliminary bill of materials (v0.1)

Planning model: USD per unit at an assumed 1,000-unit run. These are rough estimates from concept discussion, not live inventory, supplier quotations, electrical validation or a production-ready BOM. Candidate part numbers must be checked against datasheets and supply before ordering. All lines include assumptions.

| Component | Candidate / specification | Extended cost |
| --- | --- | ---: |
| Host processor module | ESP32-S3-WROOM-1-N8R8 or equivalent, 8 MB flash / 8 MB PSRAM | $3.75 |
| User processor | RP2350B | $1.00 |
| User external RAM | 8 MB PSRAM | $2.10 |
| User external flash | 16 MB | $0.80 |
| Removable storage | MicroSD slot and card | $3.00 |
| Display | 2.73-inch 320 × 320 IPS, candidate TTC273XSI-01 | $6.50 |
| Display support | Connector, backlight driver, protective lens | $1.50 |
| Buttons | 16 tactile switches and matrix diodes where needed | $1.20 |
| Rear lighting | 12 addressable RGB LEDs plus support circuit | $0.85 |
| Battery | ~2,000 mAh protected LiPo | $3.00 |
| Power management | Charger, power path, regulators, fuel gauge | $3.00 |
| Audio electronics | Mic, codec, amp, headphone output | $2.50 |
| Speaker | Small mono speaker | $0.90 |
| Sensors | IMU, environmental, ambient light | $2.50 |
| RTC | RTC and backup supply | $0.80 |
| Connectors | USB-C, battery and expansion | $1.00 |
| Support components | Crystals, passives, protection | $2.00 |
| PCB | Four-layer estimate | $3.00 |
| Assembly | Double-sided SMT estimate | $4.50 |
| Testing | Firmware programming and functional tests | $1.50 |
| Mechanical hardware | Feet, standoffs, screws | $1.00 |
| **Total** | **Raw-board device with screen and battery** | **$46.40** |

Enclosed device planning estimate: $50–55 (adds roughly $3.60–8.60 per unit for enclosure). Tooling, certification, packaging, shipping, tariffs, yield loss, software and engineering are excluded. Prototype and small-run prices will differ substantially.

## Cost concentration

| Group | Subtotal |
| --- | ---: |
| Compute and memory | $10.65 |
| Display and controls | $10.05 |
| Power | $6.00 |
| Audio | $3.40 |
| Sensors, connectors and support | $6.30 |
| PCB, assembly, test and mechanical hardware | $10.00 |

The display is a major sourcing opportunity. The $6.50 figure assumes a comparable direct-sourced display, not the exact higher-priced DLC panel previously discussed. Substituting the earlier $21.48 distributor price would put this estimate near $61.38 before enclosure. Neither price is a verified 1,000-unit quote.

## Candidate JLCPCB references

Prior discussion identified these catalog references. Recheck part descriptions, package, stock, variants and price against current listings; do not treat these as approved sourcing.

- RP2350B: C42415655.
- ESP32-S3 memory configuration: C2913201 (confirm whether this is the exact module or chip, and whether additional RF/flash components are needed).
- SK6812MINI-E: C5149201.

Most passives, switches, regulators, connectors, sensors and memory are conventional PCBA parts. Source display and battery separately if necessary. JLCPCB supports externally sourced components subject to its process; PCBA is not necessarily finished product assembly. Consider PCBWay or another box-build provider for final assembly, programming and tests if appropriate.

## Next steps

Obtain display datasheet, sample and written price; verify RP memory and programming topology; choose power/audio parts from reference designs; identify exact switch and LED footprints; create a real component-level BOM with MPNs, quantities, alternates, approved suppliers and footprint links; request PCBA quotes for 10, 100 and 1,000 units. Do not order the concept BOM as written.
