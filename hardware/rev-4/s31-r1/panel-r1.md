# Display and backlight

Choose one hand-fitted display per board. Both use J601, the same Omron 40-pin connector and independent 20 mA returns for the two strings in the backlight.

| Hand-fit part, DS601 | 4.0-inch Adafruit 5795 | 3.4-inch Adafruit 5825 |
|---|---|---|
| Manufacturer part | TL040HDS20-B1502A, Y17B | TL034WVS05-B1477A, ST7701S |
| Image | 720 × 720 | 480 × 480 |
| Module body W × H × T, mm | 74.83 ±0.15 × 78.98 ±0.15 × 1.46 ±0.15 | 70.45 ±0.15 × 70.32 ±0.15 × 1.89 ±0.10 |
| Active area W × H, mm | 71.93 × 71.93 | 60.48 × 60.48 |
| Active top-left (x, y), mm | (1.45, 1.45) | (3.93, 3.90) |
| Flex finger center x from front-left edge, mm | 37.54, calculated from 37.29 on rear drawing | 34.29, calculated from 24.04 left of 20.50 mm tongue |
| Bottom edge to flat, unbent tip, mm | 25.67 | 27.15 |
| Exposed finger length, mm | 3.00 | 3.50 |
| Logic supply current, color bars at 3.3 V | 65 mA maximum | 30 mA typical |

Coordinates use a front view with the flex leaving the bottom edge. The panel PDFs give mechanical details on page 15. Both flex tongues are 20.50 mm wide, 0.30 mm thick and have 40 contacts at 0.50 mm pitch. The drawings show exposed contact fingers on the rear side of the flat tongue, with pin 1 toward the viewer's left on the front projection. Omron's XF2M-4015-1A accepts top and bottom contacts. Inserting the tail still requires pin 1 to align with connector pad 1. [4-inch module PDF](https://cdn-shop.adafruit.com/product-files/5795/Specification_TL040HDS20-B1502A_20221208.pdf) · [3.4-inch module PDF](https://cdn-shop.adafruit.com/product-files/5825/Specification_TL034WVS05-B1477A.pdf) · [Omron drawing](https://omronfs.omron.com/en_US/ecb/products/pdf/en-xf2m.pdf)

The Omron X–X section shows 2.10 mm from the insertion mouth to the seated tip and an effective engagement length of 1.35 mm. In a straight, flat arrangement, the resulting bottom-edge-to-mouth budget is 23.57 mm for #5795 and 25.05 mm for #5825. For a folded installation, measure along the flex neutral axis through the bend, subtract the same insertion depth and reserve clearance at the reinforced contact end and the thickened component islands. The 3.4-inch drawing illustrates a lower-edge wrap and marks the component islands and single-layer flex zone separately. A final connector location and installed flex clearance need the actual PCB and a sample. Keep the latch accessible during assembly.

With a front-side connector and a 180° fold around the horizontal lower edge, each tongue moves toward the device top while pin 1 stays on the left in front projection. Use the stock J601 footprint at 0° in this orientation. Its pad 1 is at (−9.75, −2.05) mm relative to the footprint origin, its bottom-facing housing mouth is at y = +3.225 mm, and the seated tongue tip is at y = +1.125 mm. Rotation by 180° would reverse the pad order and point the socket away from the incoming flex. For a preliminary fold starting tangent at the lower edge with a 1.0 mm neutral radius, the connector origin is approximately 25.13 mm inward on #5825 or 23.65 mm inward on #5795. These coordinates assume no straight run outside the panel edge. Validate against actual fold height, usable bend zone, component islands and latch clearance before routing.

## Electrical interface

| J601 pin | Panel function | Host or supply net |
|---|---|---|
| 1, 2, 3 | Common anode, cathode 1, cathode 2 | LCD_LED_A, LCD_LED_K1, LCD_LED_K2 |
| 4, 34, 40 | Ground | GND |
| 5, 6 | VCI, active-low reset | 3V3, LCD_RESET_N |
| 7, 8 | 4.0-inch IM1/IM0 marked NC; 3.4-inch TE/PWM marked NC | Open on both |
| 9, 10, 11 | Serial data, clock, chip-select | LCD_SDI, LCD_SCK, LCD_CS |
| 12, 13, 14, 15 | Pixel clock, data enable, vertical sync, horizontal sync | LCD_PCLK through source-mounted 33 Ω, LCD_DE, LCD_VSYNC, LCD_HSYNC |
| 16, 17–21 | B0, B1–B5 | GND, LCD_B0–LCD_B4 |
| 22–27 | G0–G5 | LCD_G0–LCD_G5 |
| 28, 29–33 | R0, R1–R5 | GND, LCD_R0–LCD_R4 |
| 35–39 | Touch interface connections marked NC on these two SKUs | Open |
| MP × 2 | Mechanical anchors | Soldered, electrically isolated |

The FPC sees valid RGB666 samples for every RGB565 pixel. Red and blue top out at 62/63, green at 63/63. FPC pins 7 and 8 stay open, as called out by each module datasheet. No strap selects RGB565. Keep the module reset low with R603 until the shared logic rail is stable. The PCA9555 powers up in input mode. Preload its output latches before changing the relevant pins to outputs so CS stays high during reset. The pixel clock and parallel signals come directly from the S31. Route PCLK over a continuous reference plane with R605 at the host end.

A common rail with a 3.2235 V nominal setpoint and TPS63070 forced PWM fits both display and RP2350B DC windows. With 30.9 kΩ / 10.2 kΩ at 0.1% and ±1% converter DC accuracy, the divider/feedback calculation gives approximately 3.1865–3.2607 V. The inherited RP2350B VREG_AVDD/USB_OTP_VDD require at least 3.135 V. The allowable VCI range is 2.8–3.3 V for #5795 and 2.5–3.3 V for #5825. Probe VCI directly across the connector bypass, especially during cold start, backlight ramp, simultaneous camera/Wi-Fi activity and battery/USB transitions.

## Bring-up and timing

Power VCI with BL_PWM low. Once VCI is valid, hold reset low for at least 10 µs and allow 120 ms after releasing it before issuing commands. For #5825, send Adafruit's complete TL034WVS05 three-wire sequence, with the ninth command/data bit, COLMOD 0x66 and the delays after Sleep Out and Display On. For #5795, release reset and start the RGB stream with CS idle high. The 4-inch Qualia driver uses an empty init table. Start with the reference library settings and enable the backlight after valid frames. [Adafruit #5825 initialization and timing](https://github.com/adafruit/Adafruit_CircuitPython_Qualia/blob/8899e4a395f0fb74ec391d7156eac27d1f4d6efd/adafruit_qualia/displays/square34.py) · [Adafruit #5795 timing](https://github.com/adafruit/Adafruit_CircuitPython_Qualia/blob/8899e4a395f0fb74ec391d7156eac27d1f4d6efd/adafruit_qualia/displays/square40.py) · [Adafruit RGB565 pin assignment in its Arduino demo](https://github.com/adafruit/Adafruit_Learning_System_Guides/blob/main/Qualia/Qualia_S3_Product_Demo/Qualia_S3_Product_Demo.ino)

Horizontal entries are **sync pulse / front porch / back porch** in pixel clocks. Vertical entries use the same order in lines. Raster Hz is the pixel clock divided by total horizontal clocks and total lines. It describes panel scanout. Camera delivery, rendering and concurrent PSRAM traffic have their own rates.

| Panel / source | Pixel clock | H pulse / front / back | V pulse / front / back | Calculated raster |
|---|---:|---:|---:|---:|
| #5795, Adafruit Qualia settings | 16 MHz | 2 / 46 / 44 | 2 / 16 / 18 | 26.06 Hz |
| #5795, SKU-specific timing file | 30 MHz | 2 / 46 / 44 | 2 / 16 / 18 | 48.87 Hz |
| #5795, TDO panel PDF p. 9 typical | 35 MHz | 2 / 44 / 46 | 2 / 16 / 18 | 57.02 Hz |
| #5825, Adafruit Qualia settings | 16 MHz | 20 / 40 / 40 | 10 / 40 / 40 | 48.40 Hz |
| #5825, TDO panel PDF p. 9 typical | 16 MHz | 10 / 10 / 20 | 6 / 10 / 10 | 60.81 Hz |

Both Adafruit profiles set HSYNC and VSYNC idle high, DE idle low, and CircuitPython's pclk_active_high and pclk_idle_high flags false. Translate these to the S31 host driver's documented signal-edge convention. For the 4-inch production-speed trial, start with the SKU-specific 30 MHz profile, then measure frame stability, PCLK edge quality, rail dips and DMA underruns under camera and audio load before selecting a higher clock. [4-inch SKU timing file](https://cdn-shop.adafruit.com/product-files/5795/5795_B1502_PORCH_RGB_0710.txt)

## Backlight circuit and placement

Both manufacturer drawings specify a shared anode feeding two strings of four white LEDs. At 40 mA total the typical LED drop is 12.8 V, with 14 V maximum specified. The TPS61163A regulates each cathode independently. TI's full-scale equation gives 1.229 V × 1030 / 63.4 kΩ = 19.97 mA per string. At 3 V VSYS and an assumed 85% conversion efficiency, the 0.512 W typical LED load adds approximately 201 mA of battery-path current, excluding logic. Protect the pack current budget during concurrent audio, camera and perimeter LED operation.

VSYS drives L601 directly and feeds VIN through the 10 Ω / 1 µF filter. EN follows that filtered input as shown in TI Fig. 7-14. A 20 kHz native hardware PWM drives the PWM input. Leaving the input low during boot disables the converter through its internal pulldown. Use a 4.7 µH Coilcraft LPS4018, a band-to-LEDA MBR0540 Schottky and a 2.2 µF / 50 V output capacitor. A 330 nF capacitor from COMP to ground stabilizes the loop. Put the input capacitor, switch, diode, output capacitor and driver ground next to each other. Observe current in **both** returns and test one full dimming cycle from cold start at minimum and maximum VSYS. [TI application, limits and land pattern](https://www.ti.com/lit/ds/symlink/tps61163a.pdf)

U601 uses TI's YFF0009, 3 × 3 balls at 0.40 mm pitch. Its local land pattern has 0.23 mm NSMD copper pads, 0.29 mm mask openings and separate 0.25 mm rounded-square paste apertures corresponding to TI's 0.10 mm stencil drawing. B2 in the center is COMP. Allow for a filled and copper-capped via-in-pad escape to C604 on the reverse face, subject to assembler and stack-up DFM. Unfilled drilled pads can wick solder. Keep the feedback trace short, isolate it from the switching loop and avoid acoustic-microphone and RGB-clock routes. Use both LED return measurements, a 16-bit color-ramp test pattern and an aligned flex fit-check on the first physical board.

## Assembly parts and source PDFs

JLC's public parts API showed these catalogue numbers available on 2026-11-27. Each file below is supplied with the design. The Yageo RC family document covers all three resistor values. DS601 is hand-installed after assembly.

| Ref | Manufacturer part | Value | JLC code | Offline PDF |
|---|---|---|---|---|
| DS601, 4.0-inch | TL040HDS20-B1502A | 720 × 720 | hand-fit, Adafruit 5795 | TL040HDS20-B1502A.pdf |
| DS601, 3.4-inch | TL034WVS05-B1477A | 480 × 480 | hand-fit, Adafruit 5825 | TL034WVS05-B1477A.pdf |
| J601 | Omron XF2M-4015-1A | 40 pins, 0.50 mm | C225713 | XF2M-4015-1A.pdf |
| U601 | TI TPS61163AYFFR | Dual current-sink boost | C544314 | TPS61163A.pdf |
| L601 | Coilcraft LPS4018-472MRC | 4.7 µH | C4153163 | LPS4018-472MRC.pdf |
| D601 | onsemi MBR0540T1G | 40 V, 0.5 A | C21353 | MBR0540T1G.pdf |
| R601 | Uni-Royal 0603WAF6342T5E | 63.4 kΩ, 1% | C23093 | 0603WAF6342T5E.pdf |
| R602 | Yageo RC0603FR-0710RL | 10 Ω, 1% | C109318 | Yageo-RC0603-family.pdf |
| R603, R604 | Yageo RC0603FR-0710KL | 10 kΩ, 1% | C98220 | Yageo-RC0603-family.pdf |
| R605 | Yageo RC0603FR-0733RL | 33 Ω, 1% | C108661 | Yageo-RC0603-family.pdf |
| C601, C602, C606 | Murata GRM188R61E105KA12D | 1 µF, 25 V, X5R | C77046 | GRM188R61E105KA12D.pdf |
| C603 | Murata GRM31CR71H225KA88L | 2.2 µF, 50 V, X7R | C77095 | GRM31CR71H225KA88L.pdf |
| C604 | Murata GRM188R71C334KA01D | 330 nF, 16 V, X7R | C361106 | GRM188R71C334KA01D.pdf |
| C605 | Murata GRM188R71H104KA93D | 100 nF, 50 V, X7R | C77055 | GRM188R71H104KA93D.pdf |
