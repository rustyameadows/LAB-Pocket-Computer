# Product brief

Status: working concept, November 2026.

## What it is

LAB Pocket Computer is a pocket-sized, programmable creative computer. It combines the tactile immediacy of a Teenage Engineering Pocket Operator, the approachability of a Game Boy, the flexibility of a programmable calculator and the openness of a microcontroller development board.

It is not primarily a gaming console, music instrument, development board or desktop display. It should be excellent at several of these things because each is just an application running on the same little object.

## Why a separate device?

A phone already has more compute and a better display. LAB earns its existence through tactile controls, a consistent physical layout, instant access to small programs, a deliberately bounded canvas, a hackable hardware platform and an ambient presence on a desk. It should invite making, not demand attention.

## Three complementary modes

- Play: full-color 2D games, visual instruments, sound toys, utilities and unusual interactive experiments.
- Make: write or generate a small program on a computer, preview it on a virtual device, install it and iterate on hardware.
- Ambient: leave it on a desk displaying time, weather, scores, sensor readings, a personal dashboard or artwork. Apps can also animate a pool of light underneath the device.

## Physical direction

- Pocketable fixed hardware, with a raw PCB edition and an enclosed edition.
- Square color display, initially targeting approximately 2.7 inches and 320 × 320 pixels.
- Sixteen tactile buttons in a calculator-like grid. Map controls per app; explore layouts that also feel excellent for games.
- Two proposed seven-segment capacitive touch rails, one on either side of the display. Apps can treat each rail as seven discrete inputs or a slider/gesture surface; the physical button grid remains independent.
- Factory-installed internal microSD for apps, assets, recordings and user data, with 32 GB as a working target. A separate externally accessible microSD slot is for removable media, imports and expansion. The internal card should be service-replaceable, with secure retention in a portable device.
- Rear-mounted color camera as an app-accessible creative input, with live view, image capture, programmable filters and optical experiments. Seeed IMX219 is the lead candidate; STMicroelectronics VD66GY global shutter is a potential alternative or specialized upgrade. The front display acts as a viewfinder when an app requests it.
- Twelve individually addressable rear-facing RGB LEDs. Feet or standoffs create a gap and a soft wash of light on the desk.
- Generous rechargeable battery, USB-C charging, Wi-Fi and Bluetooth. Prefer a slim, service-replaceable ~5,000 mAh flat pouch pack (potentially up to 6,000 mAh if the layout permits). Explore an alternate body using two replaceable 21700 cells, potentially arranged across the upper rear so the battery housing creates an intentional desk angle and doubles as the raised feet. The Pocket Operator's embrace of its battery geometry is a design reference, not a requirement to expose live cells. Neither battery form factor is locked.
- Audio as a creative medium: four sensitive digital MEMS microphones with independent channels and directional-listening potential, stereo playback from two thin speakers (four as an alternate layout), and a required 3.5 mm CTIA TRRS headset jack with stereo headphone output and mono external microphone input. Core motion and optical sensing: Bosch BMI270 six-axis IMU and a rear-facing Vishay VEML3328 colorscope with controlled white illumination for sampling physical colors. Optional top/front ambient-light sensing; no dedicated environmental sensors in the base device. Exposed expansion pins remain a candidate.
- A smaller companion device could eventually serve as a dedicated home for a finished app. It is outside the initial scope.

## Product principles

1. Fixed controls, flexible meanings. An app defines what the physical buttons do.
2. Games are first-class, not the entire product. Prioritize responsive input, stable animation and a comfortable grip.
3. A useful object even when idle. Ambient mode is a product feature, not a screensaver.
4. Every built-in app can teach a developer how to make another one.
5. Make things with AI, rather than making the handheld itself an AI assistant.
6. Real ownership: support a high-level SDK and a path to unrestricted user firmware, with a recoverable host.
7. Keep the hardware identity coherent. Resist feature creep that turns it into a generic smartphone or dev board.

## Initial success criteria

- The same hardware feels natural as a game, color instrument and glanceable desk display.
- A novice can create and deploy an app with an agent; an experienced developer can replace user firmware.
- User program failure is recoverable without rebuilding or reflashing the host.
- Target 60 FPS for representative 2D games, about 10 hours of interactive battery life and two weeks of standby. These are stretch design targets, not validated specifications.
- The product can be assembled through conventional PCB manufacturing and PCBA services.

## Open product questions

Final layout and dimensions; flat versus cylindrical battery packaging, weight and desk angle; touch rail geometry and feel; internal card capacity and access; D-pad/shoulder controls versus grid-only; display technology and brightness; camera location, optics and capture modes; microphone placement and acoustic geometry, two versus four speakers, optional dedicated or switchable line-level input and exact audio electronics; colorscope optical geometry/calibration and whether a separate ambient-light sensor is useful; distribution and app library; eventual price; enclosure materials and mini-device scope.
