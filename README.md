# LAB Pocket Computer

A pocket-sized creative computer for making, playing and living with tiny programs.

LAB combines the tactile character of a Pocket Operator, the playful immediacy of a Game Boy, the programmability of a calculator and the openness of a microcontroller development board. It is a platform for small games, visual and musical instruments, personal utilities, experiments and ambient desk displays.

Make an app on your computer, with or without a coding agent. Preview it in a virtual LAB, install it on the physical device, then play with it or leave it on your desk doing something delightful.

## Initial hardware direction

- ESP32-S3 host as the original baseline; ESP32-P4 with a separate wireless processor (e.g. ESP32-C6) is the leading camera-capable host candidate.
- Independently programmable RP2350B user processor with its own memory and flash.
- Approximately 2.73-inch square 320 × 320 color IPS display.
- Sixteen tactile buttons with app-specific mappings.
- Proposed dual capacitive touch rails, seven segments on each side of the display (14 independent touch zones).
- Factory-installed, service-replaceable internal microSD (32 GB working target) plus a separate externally accessible microSD expansion/import slot; dedicated firmware flash remains separate.
- Rear-facing programmable color camera: Seeed IMX219 (8 MP MIPI CSI-2) is the lead candidate, with ST VD66GY global shutter (1.5 MP) as a specialized alternative.
- Twelve individually addressable rear-facing RGB LEDs and raised feet for an ambient pool of light.
- Rechargeable battery, USB-C, candidate audio, sensors and expansion.
- Raw PCB and enclosed editions.

The host manages the device and its peripherals. The user processor is a playground that developers can program through an SDK, native code or replacement firmware. Independent recovery is a key design goal.

## Documentation

| Document | Purpose |
| --- | --- |
| [Product brief](docs/product-brief.md) | Vision, use cases, product principles and scope |
| [Hardware architecture](docs/hardware-architecture.md) | Dual processors, peripherals, communications, power and recovery |
| [Preliminary BOM](docs/bom.md) | Candidate components, rough unit costs and sourcing assumptions |
| [Developer ecosystem](docs/developer-ecosystem.md) | SDK, virtual device, native development and agent integrations |
| [Starter applications](docs/starter-apps.md) | Candidate built-in apps and what they teach |
| [Prototype roadmap](docs/prototype-roadmap.md) | Learning sequence, benchmarks and decision gates |

## Project status

Concept and feasibility stage. The current hardware configuration is a working hypothesis, not a finalized design. The original preliminary cost model was $46.40 for a raw-board device at 1,000 units, including assembly, display and battery. The dual-card storage, touch rails, rear camera and possible host/wireless changes are not yet fully priced; see the updated BOM. These are not supplier quotations.

First milestone: connect development boards, a representative display, buttons and RGB LEDs. Demonstrate a color instrument, responsive 2D graphics, interprocessor communication and recovery from crashed user firmware. Measure performance and power before committing to custom PCBA.

No production firmware, schematics, PCB layout or validated component BOM yet. Licensing is undecided.
