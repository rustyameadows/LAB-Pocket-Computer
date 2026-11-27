# LAB Pocket Computer Rev 3A

Rev 3A replaces the discontinued WM8960 with the Nuvoton NAU88C22YG stereo codec and Diodes PAM8406DR stereo speaker amplifier. The 74 × 152 mm board retains the CTIA headset jack, two independent 8 Ω speakers, four digital microphones, bonded battery and connector positions. The public-price budget and November 27, 2026 inventory check are below. No purchase, design submission or vendor quote request was made.

## Build costs

| Finished devices | PCBs fabricated / populated | JLC-priced parts, total | JLC-priced parts, per device | Selected outside buys, total | Selected outside buys, per device |
|---:|---:|---:|---:|---:|---:|
| 1 | 5 / 2 | $1,035.01 | $1,035.01 | $1,035.01 | $1,035.01 |
| 3 | 5 / 5 | $1,499.77 | $499.92 | $1,499.77 | $499.92 |
| 5 | 5 / 5 | $1,651.56 | $330.31 | $1,651.56 | $330.31 |
| 10 | 10 / 10 | $2,459.79 | $245.98 | $2,459.79 | $245.98 |
| 500 | 516 / 516 | $86,042.28 | $172.08 | $76,892.52 | $153.79 |
| 1,000 | 1,031 / 1,031 | $169,515.51 | $169.52 | $150,609.87 | $150.61 |

The two price columns both cover complete devices and both keep PCBA at JLC. The second uses selected exact manufacturer parts from other sources where the public tiers lower the modeled batch cost. It includes an additional $1.25 per board started for inbound handling. The workbook retains the earlier alternate three-unit case and adds the two larger runs to the same table. For one to ten units, the buyer supplies finishing labor. For 500 or 1,000, the estimate pays for it. [Editable workbook](manufacturing/LAB-Pocket-R3A-build-cost-r2.xlsx)

At 1,000, $150.61 per finished unit is the mixed-source estimate. A conditional $135.87 target uses the same production labor and yield, plus three further changes, including a $6 bare board, the display manufacturer's $5 low-end price, and a $13.69 blank Raspberry Pi A2 microSD card in place of the $20.99 SanDisk retail allowance. The card needs qualification. A supply allocation for these quantities and actual volume PCB pricing are open. Budgeting $18 per fabricated board puts the mixed-source case at $158.86 per device with the original panel and media assumptions. [Panel manufacturer](https://tailorpixels.com/product/2-73-inch-ips-tft-square-lcd-rgbspi-320x320/) · [32 GB card comparison](https://www.adafruit.com/product/6010)

### What drives the 1,000-unit cost

| Cost for the program | JLC-priced parts | Selected outside buys |
|---|---:|---:|
| Bare eight-layer boards | $10,310.00 | $10,310.00 |
| Factory parts and overage | $72,792.11 | $52,597.72 |
| Double-sided SMT services | $3,638.04 | $3,638.04 |
| Components for hand finishing | $67,872.36 | $67,872.36 |
| Finishing, flashing and functional test labor | $7,732.50 | $7,732.50 |
| Production test setup | $1,500.00 | $1,500.00 |
| Combined inbound freight | $4,639.50 | $4,639.50 |
| Sourcing and receiving | $1,031.00 | $2,319.75 |

The 1,000-unit case prices 1,031 starts to allow for 97% good yield. The 500-unit case prices 516. The model counts 1,451 solderable lands and 91 part/side feeder loads. Two runs of approximately 515 boards keep each run inside JLC's published 100,001–1,000,000-joint Standard pricing tier. The estimate counts setups, fixtures and expected component losses per run, and pools purchasing across both runs. Its 1% volume procurement overage is separate from the assembly yield. Published fixture and X-ray tiers accommodate these quantities. JLC determines final CAM and inspection charges. [JLC assembly pricing](https://jlcpcb.com/help/article/pcb-assembly-price) · [Assembly capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)

The volume fabrication input is an editable $10 per board, with $6 and $18 sensitivity cases. The design requires eight layers, ENIG, controlled impedance, and 0.15 mm drilled, filled and capped vias. The prototype budgets reuse the earlier public calculator results for this stack and outline. Volume freight is assumed at $4.50 per start, general parts sourcing at $1 per start, and finishing at 15 minutes per start at $30/hour. Another ten minutes per start would add about $5.16 per delivered unit. The estimate includes a $1,500 production test setup allowance. Taxes, duties, firmware engineering, certification, service, warranty and outbound consumer packaging or delivery are outside the totals. [Fabrication specification](manufacturing/LAB-Pocket-R3A-stackup-r1.md)

### Parts buying and scale

The model prices every factory part at its required component quantity. It compares 15 exact ordering IDs with additional public supplier listings. The greatest savings at 1,000 finished devices come from the same three Coilcraft inductors, KEMET bulk capacitors and Abracon oscillator already in the circuit. Coilcraft lists the XAL4020-152MEC at $0.70 at 1,000, compared with about $10 on JLC's assembly catalog. The population uses 25 of the KEMET 10 µF capacitors per board. Whole 3,000-piece reels at Mouser's published $0.046 rate save about $3.88 per finished device. External pricing assumes the parts can be supplied to JLC in accepted packaging. The workbook records the source, tier, pack quantity and known stock limits for each offer. [Coilcraft L1](https://www.coilcraft.com/en-us/products/power/high-voltage-inductors/xal/xal40xx/xal4020-152/) · [KEMET at Mouser](https://www.mouser.com/en/ProductDetail/KEMET/C0805C106K4PACTU?qs=LOQsJ2JwiRQzQlGR%2F0Z13g%3D%3D) · [JLC consignment terms](https://jlcpcb.com/help/article/consignment-part-terms-conditions)

Eighteen of 78 factory part IDs fall below modeled requirements for each volume run in the JLC snapshot. U1 ESP32-P4NRW32X has zero listed. For the 1,000-device program, 20,827 keypad switches are budgeted against 360 in library stock, and 4,166 microphones against 265. The camera connector, PSRAM and 2.8 V regulators also require procurement. Some exact parts are available through other distributors. The protected Jauch pack, panel, camera and internal card need delivery schedules of their own. Secure traceable stock and validate a prototype before a volume release. [Per-part quantities and shortages](manufacturing/LAB-Pocket-R3A-volume-stock-r1.csv) · [Processor](https://www.digikey.com/en/products/detail/espressif-systems/ESP32-P4NRW32X/30310797) · [Battery](https://www.digikey.com/en/products/detail/jauch-quartz/LP735977JH-PCM-2-WIRES-70MM/9560998)

## Audio implementation

| Function | Schematic and software behavior |
|---|---|
| Control and clocks | U31 runs on the existing 3.3 V supplies. MODE selects two-wire control at seven-bit address 0x1A. The host provides MCLK, BCLK and frame sync. Firmware must initialize this codec's registers. |
| Headset and recording | J5 retains AC-coupled stereo headphone outputs and the MICBIAS-fed CTIA mic. Enable the left single-ended mic PGA path and disable its unused negative-input switch. GPIO2 senses the jack switch with the slow timer enabled. The four board microphones retain their separate digital interface. |
| Speakers | Route the left DAC to AUXOUT2 and right DAC to AUXOUT1. Each line drives an AC-coupled PAM8406 input via 100 kΩ in series with its internal input impedance. The approximate differential voltage gain is 2.4. Set conservative DAC and mixer levels before enabling playback. Two independent bridge outputs feed LS1 and LS2. |
| Startup | R74 pulls amplifier SHDN low while the codec GPIO is high impedance. Start with digital outputs muted, program the reference and clocks, allow the AC-coupled paths to settle, and drive GPIO1 high to enable the amp. Verify shutdown thresholds and pops across power and headset transitions. |
| Expansion | The stereo ADC/DAC provides programmable five-band EQ, automatic gain control, limiting and on-chip mixing. The installed jack supplies one analog microphone channel. These processing modes require firmware configuration. |

The selected NAU88C22YG is the 5 × 5 mm QFN-32 version with a nominal 3.5 mm exposed pad. The PAM8406DR uses the manufacturer's active SO-16 package, with a custom footprint matching its suggested lands. The four BTL output routes use 0.38 mm copper. Local power and ground vias connect the amplifier and its bypass network to the board planes. The JLC check found 8,816 codecs and 19,105 amplifiers. DigiKey also listed both order codes. This supports two procurement channels. Allocation and future lead times still vary. [Nuvoton datasheet](datasheets/NAU88C22YG.pdf) · [Diodes datasheet](datasheets/PAM8406DR.pdf) · [JLC codec](https://jlcpcb.com/partdetail/C914209) · [JLC amplifier](https://jlcpcb.com/partdetail/C86270) · [DigiKey codec](https://www.digikey.com/en/products/detail/nuvoton-technology-corporation/NAU88C22YG/8747860) · [DigiKey amplifier](https://www.digikey.com/en/products/detail/diodes-incorporated/PAM8406DR/4033289)

## Prototype files and verification

Use Standard double-sided PCBA. The 78-line BOM and placement file agree on all 357 reference designators, with 240 front and 117 rear. The original 344 placements retain their coordinates and rotation. Check the assembler's rotation preview against pin 1 and LED polarity. [Gerbers and drills](manufacturing/LAB-Pocket-R3A-fabrication-r1.zip) · [Assembly BOM](manufacturing/LAB-Pocket-R3A-JLC-BOM-r1.csv) · [Placement file](manufacturing/LAB-Pocket-R3A-JLC-CPL-r1.csv) · [Stackup](manufacturing/LAB-Pocket-R3A-stackup-r1.md)

KiCad 10.0.6 reports zero ERC violations across 22 sheets, zero DRC violations, zero unconnected items and zero schematic parity issues. The USB/CSI route-length and battery charge-window checks pass. The board and budget remain pre-prototype. Measure the regulated 3.3 V and audio output with the real speakers and battery, verify left/right mapping, headphone DC, jack detection, microphone bias/recording, idle noise and clipping. Confirm both speaker-current returns, charge temperatures, USB/CSI operation and enclosure-free fit on the physical prototype. [Native KiCad project](kicad/LAB-Pocket-R3A.kicad_pro) · [Schematic PDF](manufacturing/LAB-Pocket-R3A-schematics-r1.pdf) · [DRC](validation/LAB-Pocket-R3A-DRC-r1.json) · [ERC](validation/LAB-Pocket-R3A-ERC-r1.json) · [Battery assembly](LAB-Pocket-R3A-battery-r1.md) · [Parts and datasheets](LAB-Pocket-R3A-parts-r1.csv)
