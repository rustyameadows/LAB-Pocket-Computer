# Hardware architecture

Status: candidate architecture, not a schematic or engineering release.

## Proposed dual-processor design

| Subsystem | Candidate | Role |
| --- | --- | --- |
| Host | ESP32-S3-WROOM-1-N8R8 or equivalent | System firmware, launcher, display, inputs, audio, storage, network, lighting and recovery |
| User computer | RP2350B | Independently programmable application processor with 48 GPIOs, two Cortex-M33 cores (150 MHz), PIO and 520 KB on-chip SRAM |
| Host memory | 8 MB flash and 8 MB PSRAM | Module configuration to verify |
| User memory | 8 MB external PSRAM, 16 MB external flash | Independent storage and execution resources; verify compatible PSRAM and pin/boot configuration |
| Display | ~2.73-inch 320 × 320 square IPS | Candidate RGB-interface panel, e.g. TTC273XSI-01; confirm availability, interface, timings and mechanical drawing |
| Wireless | ESP32-S3 integrated 2.4 GHz Wi-Fi and BLE | App transfers, live data, sensors, phone/controller communication |

The table above records the original S3-based baseline, not a locked design. With the rear camera now in scope, the ESP32-P4 is the leading host candidate for evaluation: its native MIPI CSI-2 receiver and image-processing hardware suit the selected cameras. Pair it with a separate wireless processor such as ESP32-C6 for Wi-Fi and BLE, while retaining the independently programmable RP2350B. The S3 remains an alternative if the camera or architecture changes; it has no native MIPI CSI-2 interface. A final processor decision, memory configuration, power budget and radio interconnect are still open. Neither the S3 nor C6 supports conventional Bluetooth Classic A2DP headphone audio.

## Ownership and communication

The RP2350B is the user's computer. The host provides stable virtual peripherals via a documented interprocessor protocol. Host firmware remains available when user firmware crashes or is replaced.

Prototype a high-throughput SPI link with DMA and interrupt/ready lines. Select the master direction, bus speed, framing, backpressure, reset behavior, version negotiation and buffer ownership after measurement. Explore command-based graphics (sprites, text, shapes, tiles, fills) and bitmap/framebuffer upload as complementary modes. Include explicit input events, audio, lighting, network, storage and sensor APIs.

At RGB565, 320 × 320 requires 204,800 bytes per full frame, or 12.29 MB/s at 60 FPS before overhead. A full framebuffer round trip may be impractical over a simple SPI link; host rendering, dirty rectangles or asset caching may be necessary. Validate display scanout bandwidth and PSRAM contention alongside Wi-Fi/audio activity. Display scanout is separate from the app-to-host protocol.

Host-controlled reset, boot mode and a validated programming path (e.g. SWD or supported bootloader transport) should allow recovery and reinstallation without requiring cooperating user firmware. Provide physical recovery/debug pads and an independent way to recover the host itself. Do not assume that a connection to the RP reset pin alone enables reflashing.

## Peripherals

- Sixteen tactile switches; grid wiring/diodes if matrix-scanned, or direct GPIO where practical. Measure debounce, simultaneous presses and input latency.
- Two vertical capacitive touch rails flanking the display, seven copper electrode segments per side. Use native capacitive sensing where possible: S3 GPIO1–14 or P4 GPIO2–15, subject to the full pin map and board breakout. See [P4 capacitive touch reference](https://docs.espressif.com/projects/esp-idf/en/latest/esp32p4/api-reference/peripherals/cap_touch_sens.html). Expose independent touch states and derived slider positions/gestures through the host. Validate electrode size/spacing, exposed versus covered finish, ESD protection, noise, calibration, moisture and accidental grip touches. An external touch controller is a fallback only if integration requires it.
- Twelve individually controllable rear RGB LEDs, candidate SK6812MINI-E. Check current, voltage/logic compatibility, diffusion and heat. Power gate the rail when off, set a configurable brightness cap.
- USB-C for data and charging. Validate the host's USB-device path and provisioning/debug strategy.
- USB-C rechargeable battery with power-path management, fuel gauge, regulators, protection, thermal monitoring and USB current limits. Lead concept is a protected ~5,000 mAh flat pouch; alternate concept is dual 21700 cells. See battery architecture below.
- Candidate digital microphone, small mono speaker with amplifier, wired headphone path. Verify audio routing and electrical compatibility before committing.
- Two microSD slots: one factory-installed internal card for persistent user/application storage, and one externally accessible removable card for imports, exports and expansion. See storage architecture below.
- Rear-mounted color camera, connected to the host's camera interface and accessible to apps. See camera architecture below.
- Candidate IMU, ambient light sensor and environmental sensor. Board heat can bias temperature readings; validate placement.
- RTC or low-power timekeeping, plus Wi-Fi time synchronization.
- Accessible user GPIO, safe power rails, ESD protection and clearly documented voltage/current limits.

## Rear-facing camera

The camera is a general-purpose creative input, not a dedicated photography subsystem. Mount one camera on the rear, facing away from the display, with a protected optical opening and clearance from the twelve rear RGB LEDs, feet and battery. Avoid glare or light leakage from the rear LEDs. Final mechanical placement remains open.

| Priority | Module | Sensor / interface | Small-quantity reference |
| --- | --- | --- | --- |
| Lead candidate | [Seeed 114992267](https://www.digikey.com/en/products/detail/seeed-technology-co-ltd/114992267/12396961) | Sony IMX219, 8 MP color, fixed focus, 77° FOV, MIPI CSI-2, rolling shutter | DigiKey $9.90 each |
| Alternative / specialized upgrade | [STMicroelectronics CAM-6GY-084VIS](https://www.digikey.com/en/products/detail/stmicroelectronics/CAM-6GY-084VIS/24737764) | VD66GY, 1.5 MP color, fixed focus, global shutter, 84° FOV, MIPI CSI-2 | DigiKey $21.44 each |

The IMX219 is preferred for its lower cost, useful image quality and existing community P4 development work. The global-shutter VD66GY trades spatial resolution for simultaneous exposure across the image, making it interesting for motion tracking, moving subjects and optical experiments. It is not necessarily an upgrade for general photography. Neither module is a finalized component or a proven drop-in replacement for the other.

- Host captures and buffers frames, manages exposure and other supported controls, and provides display preview and storage services. Expose live frames, pixel access and snapshots to user applications through the interprocessor protocol. Avoid copying full-resolution frames over the processor link when host-side rendering, downsampling or processing will suffice.
- Target a low-resolution live preview appropriate to the 320 × 320 display. Sensor megapixel ratings do not imply full-resolution processing or a particular frame rate on the P4. Higher-resolution stills, video and frame rates are validation items rather than product promises.
- [Community IMX219/P4 driver](https://github.com/mushBrainDave/esp32-p4-imx-camera) is a starting point, not verification of this exact module. ST driver work, connector, power rails and sensor configuration need separate evaluation. Verify lane count/rate, pinout, clocks, supported pixel formats, ISP limits and cable/connector fit for both modules.
- [P4 camera controller reference](https://docs.espressif.com/projects/esp-idf/en/latest/esp32p4/api-reference/peripherals/camera_driver.html). P4 camera/ISP throughput, memory and power should be benchmarked concurrently with graphics, audio and storage.
- Camera should be power-managed and app access should be explicit; user-facing capture and permissions behavior is to be designed.

## Storage architecture

- Dedicated soldered flash for host firmware, launcher/recovery and configuration required to boot; separate dedicated RP2350B flash for user firmware. The core recovery path should not depend on either card.
- Internal microSD: factory-installed, service-replaceable, securely retained socket; target 32 GB initially, capacity and supplier subject to cost/endurance validation. Stores installed app packages, assets, recordings, music and user files. Device remains useful without an external card.
- External microSD: accessible without opening the enclosure, for removable user media, transfers and expansion. No external card required or bundled by default (working assumption).
- Host owns the filesystems and exposes scoped file operations to the user processor. Evaluate independent SDMMC/SPI interfaces or shared SPI with independent chip selects; verify simultaneous access, throughput, hot-plug handling and pin allocation alongside the display, touch rails, wireless and processor link. Do not assume two full-width SDMMC buses fit the selected module.
- Choose a traceable, reputable card model; validate write endurance, power-loss behavior, safe removal, recovery from missing/corrupt internal media and drop/vibration retention. Consider bulk direct sourcing of cards and PCBA-installed sockets. Soldered eMMC remains an alternative if price or reliability warrants it.

## Battery architecture and physical variants

The earlier 2,000 mAh assumption is superseded. Do not choose a battery topology solely on capacity; compare packaging, mass, replaceability, safety, cost, runtime and desk posture.

| Variant | Candidate | Nominal energy | Mechanical reference |
| --- | --- | ---: | --- |
| A: Thin | Protected 1S 4,800–5,000 mAh LiPo; [Jauch LP735977JH+PCM+2 WIRES 70MM](https://www.digikey.com/en/products/detail/jauch-quartz/LP735977JH-PCM-2-WIRES-70MM/9560998) | 17.76 Wh for the 4,800 mAh sample at 3.7 V | 78.5 × 59.5 × 7.8 mm for the sample, excluding enclosure allowance |
| B: Cylindrical | Two matched 4,000–5,000 mAh 21700 Li-ion cells; [Jauch LIINR21700JD-50E5.0AH](https://www.digikey.com/en/products/detail/jauch-quartz/LIINR21700JD-50E5-0AH/26408513) as a 5,000 mAh reference | 37 Wh total for two 5,000 mAh cells at the listed 3.7 V | 21.4 mm diameter × 70.8 mm long per reference cell; roughly 71 × 43 × 22 mm bare envelope when placed side by side, before holder and shell |

### Variant A: flat pouch

- Favor a broad, thin battery behind the PCB rather than making the product thick throughout. The sample is 7.8 mm thick; look for a 5–7 mm alternative if practical. Explore 6,000 mAh only if the physical envelope allows.
- Design for service replacement through a removable back panel and a keyed, appropriately rated connector. The Jauch sample has wire leads, not a ready-to-plug connector; select/verify connector and polarity before connecting it to a development board.
- Allow pouch expansion, cable bend radius, puncture protection and clearance from sharp components, hot spots and camera/LED apertures.

### Variant B: dual 21700

- Explore a purposeful cylindrical battery spine across the upper rear of the device, inspired by the Pocket Operator's battery-driven posture. The battery housing can provide the desk angle and potentially replace or integrate with the rear feet. Also compare a lower-rear arrangement. Keep the LED light wash, camera and comfortable handheld grip.
- Compare a professionally assembled, protected two-cell pack with an engineered user-replaceable cell system. Standard 21700 dimensions do not guarantee electrical compatibility; protected cells may be longer than nominal dimensions.
- 1S2P (~10 Ah at 3.7 V) and 2S1P (~5 Ah at 7.4 V) have similar nominal energy but different charging and regulation requirements. Do not lock either topology yet. A removable-cell design must prevent unsafe mixing, polarity errors and uncontrolled equalization currents; series charging requires appropriate per-cell monitoring/balancing. Do not connect loose unmatched cells in parallel or charge bare cells without a validated protection system.
- [Keystone 1124 two-cell holder](https://www.digikey.com/en/products/detail/keystone-electronics/1124/12751684) is a mechanical prototype reference, not a complete battery protection or charging solution. [GlobTek BL5000C21701S2PFTM104IBC1NN](https://www.digikey.com/en/products/detail/globtek-inc/BL5000C21701S2PFTM104IBC1NN/22531458) is a packaged 3.6 V / 10 Ah reference for the alternative protected-pack path (verify protection details; not currently stocked in the checked catalog).
- Validate retention, electrical contacts, insulation, current/temperature limits, charge behavior and replacement instructions before permitting live user replacement. Use inert dummy cells for initial ergonomic mock-ups.

### Charging and measurement

Both variants should support USB-C recharge and continuous plugged-in desk operation through a properly designed load-sharing/power-path circuit. Choose the USB-C input and charge rate, charger, cell monitoring, protection, fuel gauge, thermal limits and regulators to match the final topology and battery datasheets. Validate simultaneous operation and charging without overheating. Higher-capacity packs may warrant USB-C PD; USB-C alone does not imply PD or a specific charging speed. Expose battery state and charging status to the host.

## Power modes

Active handheld, plugged-in ambient, battery-powered ambient and deep standby. Aim to power down or sleep the user processor independently, dim/disable the display, gate LEDs and schedule Wi-Fi polling. The host must not consume unnecessary power keeping an unused app alive.

Use watt-hours for comparison across cell voltages and topologies. With the 17.76 Wh flat sample, ideal runtime at 1 W / 2 W / 3 W average battery draw is approximately 17.8 / 8.9 / 5.9 hours. With the 37 Wh dual-cell reference, the corresponding ideal figures are 37 / 18.5 / 12.3 hours. Actual runtime depends on usable energy and conversion efficiency; load-side power must be adjusted for conversion losses. Ten hours of use implies a nominal average battery draw budget of about 1.78 W or 3.7 W respectively. The two-week standby goal implies about 53 mW or 110 mW respectively before derating. Measure graphics, Wi-Fi, camera, audio, storage, backlight and rear LED workloads; these estimates are not runtime commitments.

## Development and manufacture

Start with accessible P4 (for the MIPI camera path) and RP2350 development boards; S3 remains a comparison platform. Begin with the IMX219 module and verify its physical connector before powering it. The RP2350 development-board variant may differ from the final B package. Use a representative LCD, buttons and LEDs. Validate the link, recovery and graphics before a custom PCB. Target a compact four-layer board initially, but let routing and RF/power integrity determine the stackup. Keep the antenna clearance, battery safety, display FPC strain relief, test pads, assembly tolerances and enclosure standoffs in mind.

References: [RP2350](https://www.raspberrypi.com/products/rp2350/), [ESP32-S3](https://www.espressif.com/en/products/socs/esp32-s3), [ESP32-P4](https://www.espressif.com/en/products/socs/esp32-p4).
