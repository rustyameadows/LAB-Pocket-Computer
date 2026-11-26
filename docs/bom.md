# Preliminary bill of materials (v0.4)

Planning model: USD per unit at an assumed 1,000-unit run. These are rough estimates from concept discussion, not live inventory, supplier quotations, electrical validation or a production-ready BOM. Candidate part numbers must be checked against datasheets and supply before ordering. All lines include assumptions.

| Component | Candidate / specification | Extended cost |
| --- | --- | ---: |
| Host processor module (original S3 baseline) | ESP32-S3-WROOM-1-N8R8 or equivalent; P4 with separate wireless is the leading camera-capable alternative, not priced here | $3.75 baseline |
| User processor | RP2350B | $1.00 |
| User external RAM | 8 MB PSRAM | $2.10 |
| User external flash | 16 MB | $0.80 |
| Internal user storage | Factory-installed 32 GB microSD (working target) and securely retained socket | TBD |
| External removable storage | User-accessible microSD socket, card detect/ESD as needed; no bundled card assumed | TBD |
| Display | 2.73-inch 320 × 320 IPS, candidate TTC273XSI-01 | $6.50 |
| Display support | Connector, backlight driver, protective lens | $1.50 |
| Buttons | 16 tactile switches and matrix diodes where needed | $1.20 |
| Capacitive touch rails | 14 PCB electrodes (7 per display side), routing and any protection/support parts; native S3 or P4 touch preferred | TBD |
| Rear camera | Seeed IMX219 114992267, MIPI CSI-2; ST CAM-6GY-084VIS alternate, not additive | TBD |
| Camera integration | FPC/connector, power, support parts and optical/mechanical mounting | TBD |
| Rear lighting | 12 addressable RGB LEDs plus support circuit | $0.85 |
| Battery, variant A (lead) | Protected ~5,000 mAh flat 1S LiPo, service-replaceable | TBD |
| Battery, variant B (alternate, not additive) | Two 21700 cells, matched/protected pack or engineered replaceable-cell system; holder and retention | TBD |
| Power management | USB-C charger, power path, regulators, fuel gauge and protection for chosen topology | TBD |
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
| **Priced subtotal** | **Raw-board device excluding revised storage, touch, camera, battery/power and any host/wireless change** | **$37.40 + TBD** |

Original v0.1 baseline: $46.40 raw-board / $50–55 enclosed. This included a single $3.00 microSD slot/card allowance; it is superseded as a total by the v0.4 subtotal until the two sockets, internal card, touch-related costs, camera integration, revised battery and power management and any P4/wireless processor changes are priced. The old $3 battery and $3 power management allowances are removed from the subtotal, not carried forward as new quotes. The previous $3.60–8.60 enclosure allowance is unchanged pending mechanical review. Tooling, certification, packaging, shipping, tariffs, yield loss, software and engineering are excluded. Prototype and small-run prices will differ substantially.

## Cost concentration

| Group | Subtotal |
| --- | ---: |
| Compute and memory (excluding microSD) | $7.65 |
| Internal and external microSD | TBD |
| Display and controls | $10.05 + touch costs TBD |
| Rear camera and integration | TBD |
| Battery and power management | TBD |
| Audio | $3.40 |
| Sensors, connectors and support | $6.30 |
| PCB, assembly, test and mechanical hardware | $10.00 |

The display is a major sourcing opportunity. The $6.50 figure assumes a comparable direct-sourced display, not the exact higher-priced DLC panel previously discussed. Substituting the earlier $21.48 distributor price would add $14.98 to the current subtotal before enclosure and unpriced items. Neither price is a verified 1,000-unit quote.

## Storage and touch sourcing notes

- Source both sockets through PCBA. Buy reputable 32 GB microSD cards through normal retail for prototypes. For production, purchase the internal card in bulk through an authorized distributor or directly from a reputable memory supplier; confirm a stable model, capacity, endurance and written 1,000-unit pricing. The external slot does not require a bundled card.
- Earlier catalog comparisons suggested removable microSD could be substantially cheaper than soldered eMMC; stock and pricing were not production quotes. Do not treat those catalog figures as approved BOM costs.
- Native capacitive touch electrodes are PCB copper features, not fourteen purchased switches. Price the incremental routing, PCB area, protection/conditioning or optional controller only after layout and electrical evaluation. Confirm all 14 touch-capable pins can coexist with the selected display, dual storage and other peripherals.

## Rear camera sourcing (prototype quantities)

These are small-quantity DigiKey catalog reference prices, not production estimates or confirmed checkout totals. Source camera modules through established distributors. Do not include both cameras in the same unit cost.

| Priority | Module / source | 1 unit | 2 units | 5 units |
| --- | --- | ---: | ---: | ---: |
| Lead | [Seeed 114992267, IMX219](https://www.digikey.com/en/products/detail/seeed-technology-co-ltd/114992267/12396961) | $9.90 | $19.80 | $49.50 |
| Alternative | [ST CAM-6GY-084VIS, VD66GY global shutter](https://www.digikey.com/en/products/detail/stmicroelectronics/CAM-6GY-084VIS/24737764) | $21.44 | $42.88 | $107.20 |

Totals assume the listed single-unit price, before shipping, tax or tariffs. Obtain current quotes separately for production volumes. Camera connector, power rails, optical mounting, support components and P4 plus radio BOM remain open. The 1,000-unit subtotal above deliberately excludes these unpriced changes.

## Prototype purchasing: battery, display, camera and storage

Prefer DigiKey direct (not third-party marketplace listings) for the three externally purchased assemblies: battery, display and camera. Established manufacturers and Adafruit are acceptable fallback suppliers. Purchase microSD cards separately through retail for early prototypes. Below are catalog prices in small quantities checked November 26, 2026; not production quotes or guaranteed checkout availability.

| Part | 1 prototype | 2 prototypes | 5 prototypes |
| --- | ---: | ---: | ---: |
| [Jauch 4,800 mAh flat LiPo LP735977JH+PCM+2 WIRES 70MM](https://www.digikey.com/en/products/detail/jauch-quartz/LP735977JH-PCM-2-WIRES-70MM/9560998) | $26.84 | $53.68 | $134.20 |
| [Jauch 5,000 mAh 21700 LIINR21700JD-50E5.0AH](https://www.digikey.com/en/products/detail/jauch-quartz/LIINR21700JD-50E5-0AH/26408513), two per alternate device | $29.80 | $59.60 | $123.90 |
| [Keystone 1124 dual 21700 holder](https://www.digikey.com/en/products/detail/keystone-electronics/1124/12751684), optional mechanical reference | $12.10 | $24.20 | $60.50 |
| [DLC Display DLC-T2.7DDS#1, 2.73-inch 320 × 320 IPS](https://www.digikey.com/en/products/detail/dlc-display-co-ltd/DLC-T2-7DDS-1/26822634) | $30.77 | $61.54 | $153.85 |
| [Seeed 114992267 IMX219](https://www.digikey.com/en/products/detail/seeed-technology-co-ltd/114992267/12396961) | $9.90 | $19.80 | $49.50 |

Quantity columns are extended prices for the stated number of devices; the 21700 row includes two cells per device and uses the published 10-cell tier for five devices. Other rows use the listed one-unit price. Exclude shipping, taxes, tariffs, connectors, charge/protection circuitry and microSD cards. The two battery variants are alternatives, not cumulative. Lithium shipments may be restricted to ground. No parts are ordered by this document.

- Flat battery: 3.7 V / 4.8 Ah, 78.5 × 59.5 × 7.8 mm, protection circuit and wire leads. Confirm charge and discharge ratings, connector, thermistor requirements and mechanical fit.
- Cylindrical reference: 21.4 × 70.8 mm flat-top cells; the holder is not a protection system. Do not assume loose bare cells are safe for a consumer-replaceable pack. Evaluate protected assembled packs as well: [GlobTek 3.6 V / 10 Ah BL5000C21701S2PFTM104IBC1NN](https://www.digikey.com/en/products/detail/globtek-inc/BL5000C21701S2PFTM104IBC1NN/22531458) is $44.79 in single quantities but had no stock in the checked listing.
- Display: the DigiKey DLC module is the high-brightness square candidate discussed earlier; the catalog lists an SPI interface (ST7365P). Validate actual supported interface, connector, scanout and frame rate. It is not assumed electrically interchangeable with the lower-cost RGB-interface TTC273XSI-01.
- Camera: verify exact IMX219 module pinout before powering it; its small-quantity purchase price is separate from the production camera estimate.
- microSD: use a reputable retail 32 GB card for internal storage and a second retail card as needed to test external imports.

## Candidate JLCPCB references

Prior discussion identified these catalog references. Recheck part descriptions, package, stock, variants and price against current listings; do not treat these as approved sourcing.

- RP2350B: C42415655.
- ESP32-S3 memory configuration: C2913201 (confirm whether this is the exact module or chip, and whether additional RF/flash components are needed).
- SK6812MINI-E: C5149201.

Most passives, switches, regulators, connectors, sensors and memory are conventional PCBA parts. Source display and battery separately if necessary. JLCPCB supports externally sourced components subject to its process; PCBA is not necessarily finished product assembly. Consider PCBWay or another box-build provider for final assembly, programming and tests if appropriate.

## Next steps

Obtain display datasheet, sample and written price; verify RP memory and programming topology; choose power/audio parts from reference designs; identify exact switch and LED footprints; create a real component-level BOM with MPNs, quantities, alternates, approved suppliers and footprint links; request PCBA quotes for 10, 100 and 1,000 units. Do not order the concept BOM as written.
