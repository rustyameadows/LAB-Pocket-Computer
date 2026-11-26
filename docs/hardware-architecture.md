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

The ESP32-P4 was considered as a more powerful graphics-oriented host. It would require a separate wireless solution. The S3 reduces chip count and complexity. Revisit the P4 only if measured performance justifies it. The S3 does not support Bluetooth Classic, so conventional A2DP headphone audio is not available from this architecture.

## Ownership and communication

The RP2350B is the user's computer. The host provides stable virtual peripherals via a documented interprocessor protocol. Host firmware remains available when user firmware crashes or is replaced.

Prototype a high-throughput SPI link with DMA and interrupt/ready lines. Select the master direction, bus speed, framing, backpressure, reset behavior, version negotiation and buffer ownership after measurement. Explore command-based graphics (sprites, text, shapes, tiles, fills) and bitmap/framebuffer upload as complementary modes. Include explicit input events, audio, lighting, network, storage and sensor APIs.

At RGB565, 320 × 320 requires 204,800 bytes per full frame, or 12.29 MB/s at 60 FPS before overhead. A full framebuffer round trip may be impractical over a simple SPI link; host rendering, dirty rectangles or asset caching may be necessary. Validate display scanout bandwidth and PSRAM contention alongside Wi-Fi/audio activity. Display scanout is separate from the app-to-host protocol.

Host-controlled reset, boot mode and a validated programming path (e.g. SWD or supported bootloader transport) should allow recovery and reinstallation without requiring cooperating user firmware. Provide physical recovery/debug pads and an independent way to recover the host itself. Do not assume that a connection to the RP reset pin alone enables reflashing.

## Peripherals

- Sixteen tactile switches; grid wiring/diodes if matrix-scanned, or direct GPIO where practical. Measure debounce, simultaneous presses and input latency.
- Twelve individually controllable rear RGB LEDs, candidate SK6812MINI-E. Check current, voltage/logic compatibility, diffusion and heat. Power gate the rail when off, set a configurable brightness cap.
- USB-C for data and charging. Validate the host's USB-device path and provisioning/debug strategy.
- Protected ~2,000 mAh single-cell rechargeable battery; charger with power-path management, fuel gauge, regulators, protection, thermal and USB current limits. Prefer dedicated charging/protection hardware rather than relying on application firmware.
- Candidate digital microphone, small mono speaker with amplifier, wired headphone path. Verify audio routing and electrical compatibility before committing.
- Candidate microSD for removable assets and user files; host-side filesystem, controlled access across the processor link.
- Candidate IMU, ambient light sensor and environmental sensor. Board heat can bias temperature readings; validate placement.
- RTC or low-power timekeeping, plus Wi-Fi time synchronization.
- Accessible user GPIO, safe power rails, ESD protection and clearly documented voltage/current limits.

## Power modes

Active handheld, plugged-in ambient, battery-powered ambient and deep standby. Aim to power down or sleep the user processor independently, dim/disable the display, gate LEDs and schedule Wi-Fi polling. The host must not consume unnecessary power keeping an unused app alive.

For a nominal 2,000 mAh battery, ten hours implies about 200 mA average at the battery before derating; two weeks implies about 6 mA average. These are rough budgets, not measured endurance. Account for regulator efficiency, usable capacity, radio bursts, display backlight and LED current. Measure real workloads before selecting battery capacity or making claims.

## Development and manufacture

Start with accessible S3 and RP2350 development boards (the RP2350 variant may differ from the final B package), representative LCD, buttons and LEDs. Validate the link, recovery and graphics before a custom PCB. Target a compact four-layer board initially, but let routing and RF/power integrity determine the stackup. Keep the antenna clearance, battery safety, display FPC strain relief, test pads, assembly tolerances and enclosure standoffs in mind.

References: [RP2350](https://www.raspberrypi.com/products/rp2350/), [ESP32-S3](https://www.espressif.com/en/products/socs/esp32-s3), [ESP32-P4](https://www.espressif.com/en/products/socs/esp32-p4).
