# LAB Pocket v9b manufacturing review

**27 November 2026 · USD · JLCPCB Standard, double-sided assembly**

The 74 × 152 mm bare-board design fits JLCPCB's process. Five finished prototypes budget at **$1,045 total, or $209 each**, once the electronics are complete. The immediate constraints are the unfinished power, audio and camera circuits and the availability of the exact host processor. I would fund a two-board bring-up run first and install one complete hand kit. [Editable cost model](LAB-Pocket-R2-v9b-JLCPCB-budget-r1.xlsx) · [JLCPCB assembly capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)

## Prototype purchase budget

Factory spend includes bare boards, components, two-sided assembly and an allowance for the circuits still to be specified. Hand kits include one battery, display, camera and card, two speakers, harness materials and retention materials per finished device. The cash budget adds $60 freight across suppliers and $25 for special sourcing per batch. It assumes US delivery and owner assembly. Numbers are rounded independently.

| Finished devices | Bare / populated boards | Factory spend | Hand kits | Total cash | Per finished device | Budget with extra reserve |
|---:|:---:|---:|---:|---:|---:|---:|
| 1 | 5 / 2 | $376 | $79 | **$540** | **$540** | $619 |
| 2 | 5 / 2 | $376 | $158 | **$619** | **$309** | $708 |
| 3 | 5 / 5 | $576 | $237 | **$898** | **$299** | $1,033 |
| 5 | 5 / 5 | $576 | $383 | **$1,045** | **$209** | $1,200 |
| 10 | 10 / 10 | $862 | $707 | **$1,655** | **$165** | $1,920 |

JLCPCB publishes a two-piece assembly minimum. The three-device case conservatively pays for five populated boards and leaves two without hand kits. **If the order form accepts three populated boards, three finished devices fall to $762 total, or $254 each.** The calculator requests Gerbers before it will expose the assembly configuration. For the one-device case, buying the second hand kit later adds about $79 in parts at these prices, before any incremental freight. [JLCPCB assembly quantities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities) · [Order workflow](https://jlcpcb.com/pcb-assembly)

The reserve column adds $45 per batch, $12 per populated board and $10 per finished unit for procurement, unresolved circuits and fit materials. It is a planning sensitivity. Tax, duties, engineering, tools, firmware development, certification, failed assemblies and another board spin are extra. The workbook also prices the option of paying for 30 minutes of finishing and repeatable testing per device at $40/hour. First-board debugging is a separate engineering task.

## What the vendor can make

I checked the v9b PCB against its parts list. It has four copper layers, a 1.6 mm board and **154 factory placements** across **30 part numbers**. There are 121 placements on the front and 33 on the rear, excluding the spring speakers and five bare test points. U1's measured lead pitch is 0.35 mm, the published minimum for Standard assembly. JLCPCB also explicitly lists this chip as Standard-only. Allow for breakaway assembly rails and fiducials while preserving the finished outline. [JLCPCB capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities) · [ESP32-P4 part listing](https://jlcpcb.com/partdetail/EspressifSystems-ESP32P4NRW32X/C54540373)

The online calculator returned **$57.90 for five bare boards** and **$66.10 for ten**, with black mask, white silkscreen, ENIG, 1 oz outer and 0.5 oz inner copper. The five-board price consists of $25 engineering, $7 board fabrication, $8 color and $17.90 finish. At ten the board line becomes $13.90 and finish $19.20. These are unpanelized prices before delivery. Panel rails, impedance requirements and the final via specification can change them. [JLCPCB calculator](https://cart.jlcpcb.com/quote)

For five populated boards, the factory estimate breaks down as follows. The final assembly price requires Gerbers, drill data, a verified BOM and a component-placement file for both faces. [JLCPCB order workflow](https://jlcpcb.com/pcb-assembly)

| Five-board cost driver | Batch USD | Basis |
|---|---:|---|
| Bare boards | $57.90 | Live dimension-only calculator |
| Listed components | $233.04 | JLC price tiers applied to batch quantities, including small-lot overage and conditional sourcing |
| Setup, stencil, fixtures, feeder loading | $135.98 | $51.12 setup, $16.42 stencil, $16.42 fixtures and 34 estimated loads at $1.53 |
| Placement, inspection and packing | $40.42 | 832 modeled solderable pads per board and eight assumed X-ray placements per board |
| Allowance for missing electronics and their assembly | $109.16 | $18 parts and 100 additional joints per board, plus 12 additional feeder loads for the run |
| **Factory subtotal** | **$576.49** | Before freight, local parts and special sourcing |

The $18 allowance covers power and backlight ($6), audio ($7), and clocks, camera mating and other support ($5). These are engineering estimates pending schematic and footprint selection. CAM review can change the actual solder, inspection, feeder, panel and handling charges. [JLCPCB published fees](https://jlcpcb.com/help/article/pcb-assembly-price)

## Sourcing and final assembly

- **Host processor.** The exact ESP32-P4NRW32X, JLC C54540373, showed zero stock. DigiKey also showed zero and listed 2,000 expected on 27 April 2027. That date is a distributor estimate. The workbook carries JLC's catalog price. Secure a small-lot allocation or qualify another silicon revision before committing this layout. [JLCPCB](https://jlcpcb.com/partdetail/EspressifSystems-ESP32P4NRW32X/C54540373) · [DigiKey](https://www.digikey.com/en/products/detail/espressif-systems/ESP32-P4NRW32X/30310797) · [Espressif revision comparison](https://documentation.espressif.com/esp32-p4_datasheet_en.html)
- **Keys, LEDs and battery socket.** JLC showed one switch against the plain TL3301NF160QG listing. The E-Switch listing with drawing suffix P010515 had 360, enough for all 200 keys on ten units. The archived switch drawing identifies P010515. The budget uses that listing and the stocked LF/SN suffix of the JST header, both subject to sign-off. The 20 SK6805 key LEDs per unit are available. The 12 perimeter WS2812B-V5/W LEDs showed zero factory stock. Their catalog preorder minimum was 94, which is budgeted even in the two-board run. Of the 30 factory lines, 26 had enough exact-match stock for ten boards, two use the suffix candidates, and two require sourcing. [E-Switch JLC listing](https://jlcpcb.com/partdetail/ESwitch-TL3301NF160QGP010515/C273527) · [JST header](https://jlcpcb.com/partdetail/JST-S3B_PH_SM4_TB_LF_SN/C265101) · [Perimeter LED](https://jlcpcb.com/partdetail/Worldsemi-WS2812B_V5W/C2874885) · [JLCPCB sourcing options](https://jlcpcb.com/help/article/pcba-parts-sourcing-instruction)
- **Battery, display and camera.** The Jauch 4,800 mAh pack is $26.84 at one or $22.326 each at ten, with wire leads. Crimp the polarized harness, verify polarity and fit the two adhesive strips locally. The TTC273XSI-01 panel is advertised at $5–8. The estimate uses $8 and assumes the bare RGB panel. The Seeed IMX219-77 replacement module costs $9.90 at one or $8.50 at ten. Fit both flexes after board test. [Jauch pack at DigiKey](https://www.digikey.com/en/products/detail/jauch-quartz/LP735977JH-PCM-2-WIRES-70MM/9560998) · [Tailor Pixels](https://tailorpixels.com/product/2-73-inch-ips-tft-square-lcd-rgbspi-320x320/) · [Seeed Studio](https://www.seeedstudio.com/IMX219-77-Camera-77-FOV-Applicable-for-Raspberry-Pi-V2-Camera-p-4605.html)
- **Sound and storage.** Fit the two spring-contact PUI speakers into a retainer after reflow. They cost $4.86 each, or $3.713 each when buying ten speakers. Both microSD sockets go through factory assembly. Install one internal card locally. Kingston discontinued the specified 32 GB model, so the budget uses $20.99 for a SanDisk 32 GB card pending qualification. The external slot ships empty. [PUI speakers at DigiKey](https://www.digikey.com/en/products/detail/pui-audio-inc/AS01808AO-SC18-WP-R/9687113) · [Kingston lifecycle notice](https://www.kingston.com/en/memory/search/discontinuedmodels?partid=SDCS2%2F32GB) · [SanDisk card at B&H](https://www.bhphotovideo.com/c/product/1961055-REG/sandisk_sdsqujq_032g_gz6ma_32gb_uhs_i_microsd_card.html)

## Engineering work before an order

1. **Make it power up and charge.** The v9b schematic holds charging disabled and leaves the 3.3 V buck-boost, display backlight supply, switched 5 V LED supply and MCU core rails unresolved. Complete the clock, reset, straps, decoupling and boot-flash interfaces. Validate the two-wire pack's temperature sensing and charge behavior. Verify load steps from the LEDs, wireless module, display and speakers.
2. **Complete the camera and audio paths.** Select and verify the camera's mating connector, rails, pinout, firmware support and flex route. The jack currently represents headphones plus a headset mic. Choose the intended input function, then complete the codec, input conditioning and speaker amplifier. Preserve the four microphone ports and prove speaker compression and retention on the bare PCB.
3. **Release manufacture-ready artwork.** The v9b DRC contains 304 unrouted connections, 104 processor clearance findings and four USB locator-hole clearance findings. A fresh ERC returned 143 errors and 18 warnings. Review the custom footprints, including the jack terminals and mic ground-ring paste aperture, against the manufacturer drawings. Then route and verify the high-speed interfaces, validate the stencil and both placement rotations, and generate Gerbers, drills, BOM and CPL from the same revision.
4. **Bring up two populated boards before buying ten kits.** Power the first board on a current-limited bench supply. Verify rails, boot, programming and USB before fitting the pack. Exercise each key and LED, both card slots, all microphones and both speakers. Check display and camera operation, then verify charging, temperature, battery retention and strain relief. Keep the second populated board available for comparison. The five-board run becomes attractive once those tests pass.

Design evidence comes from the v9b KiCad project, its versioned parts list, archived design-rule report and supplier drawings. The cost workbook retains the catalog IDs, price tiers, stock snapshot and editable allowances. No order or supplier reservation was placed.
