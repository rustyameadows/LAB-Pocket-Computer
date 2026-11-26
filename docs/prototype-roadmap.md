# Prototype roadmap

This is a proposed learning sequence, not an engineering schedule or launch commitment.

## Phase 0: bench prototype

Use readily available ESP32-P4 and RP2350 development boards for the camera-enabled architecture; keep ESP32-S3 as the comparison baseline. Connect a representative square LCD, tactile buttons, addressable LEDs and power-monitoring equipment. Verify exact candidate parts and availability separately.

- Bring up display scanout, input and host lighting; evaluate two seven-segment capacitive rails and their coexistence with other peripherals.
- Prototype four synchronized IM70D122 PDM microphone channels, stereo playback, CTIA TRRS headset detection/muting, external headset microphone recording, and capture to microSD. The microphones are SMD parts; use an appropriate breakout or test PCB before custom PCBA. Verify simultaneous capture and playback, latency, quiet sound pickup and power.
- Prototype BMI270 motion sampling, tilt/gesture input, interrupts and low-power behavior. Prototype VEML3328 rear colorscope with switchable white illumination; compare LED-on/off readings against color references under varied ambient light and distances. Test rear LED interference, optical baffling and desk/hand occlusion; decide whether a separate top/front ambient sensor is warranted.
- Test host access to internal and removable microSD volumes, simultaneous transfers, safe removal, missing/corrupt media recovery and power-loss behavior.
- Bring up the lead Seeed IMX219 rear camera on P4, including connector verification, low-resolution live preview, snapshots, frame access and recording to storage if supported. Benchmark latency, frame rate, memory and power alongside the display and wireless. Evaluate the ST VD66GY global-shutter alternative separately if motion-oriented applications justify it.
- Establish a two-way processor protocol and boot/recovery path.
- Run the color synth and a representative 2D game.
- Test both host-side drawing commands and bitmap transfers.
- Measure FPS, frame pacing, end-to-end input latency, interprocessor throughput, memory headroom and performance while Wi-Fi/audio are active.
- Crash/hang the user program intentionally and prove that the host can return to the launcher and reinstall known-good firmware.

## Phase 1: software vertical slice

Develop the minimum launcher, SDK, app package/install path, virtual device and CLI/agent workflow. Build the color synth, ambient clock and small game with the same API. Test app portability between virtual and real devices. Specify permissions, update rollback and recovery.

## Phase 2: form and power

Prototype several 16-button grid layouts and a physical mock-up at the selected display size. Compare game ergonomics, two-thumb use, desk readability, key spacing and switch feel; prototype seven-segment rails along both display edges, including accidental grip touches and exposed/covered electrode options. Verify internal card retention/service access and external card access. Evaluate feet/standoff height, rear LED diffusion and rear camera aperture/clearance, including unwanted illumination from the LEDs. Test display alternatives if the 320 × 320 panel does not meet brightness, viewing or performance needs.

Before selecting battery or enclosure geometry, make actual-size volumetric 3D prints of two variants. Use inert battery mock-ups (and safe ballast to simulate mass), not live loose cells. Variant A uses the thin 78.5 × 59.5 × 7.8 mm flat-pack reference; variant B uses two approximately 21.4 × 70.8 mm cylindrical cells plus realistic holder, protection and shell allowance. Explore an upper-rear battery spine that acts as a desk stand, compare it with separate feet and other orientations. Assess pocketability, grip, center of gravity, desk angle, screen readability, rear LED wash, camera aperture and battery service access. Do not assume the cylindrical version is too bulky until it has been held and viewed at scale.

Test two versus four thin PUI speakers and several microphone spacings/port positions in enclosure mock-ups. Compare listening sensitivity, directional accuracy, stereo image, resonance, speaker-to-mic echo, TRS headphone compatibility, CTIA headset input/output and power. Include acoustic chambers, sealing and mounting in volumetric prints. Keep the two-speaker baseline unless four justify their space and cost.

Profile interactive, ambient, Wi-Fi, camera, audio and standby power on real hardware. Validate the battery protection and USB-C charging/power-path design with appropriate engineering review. Compare runtime, charge time, mass, temperature and cost for both battery options before locking a topology or ordering a PCB. Decide whether a more capable host or alternative display is warranted.

## Phase 3: custom PCBA

Create schematics, pin allocation, PCB layout, mechanical model, exact BOM and test plan. Review RF, power, ESD, battery safety and programming interfaces. Request quotes and order a small run (around 10 boards). Attach separately sourced displays and batteries if necessary, and use 3D-printed enclosures for early prototypes.

Validate assembly, factory programming, test coverage, thermals, battery runtime, wireless, audio and recovery. Only then refine the design for pilot manufacturing and certification.

## Decision gates

- S3 versus P4: representative 60 FPS graphics, camera interface and capture requirements, acceptable latency, memory headroom and power, not theoretical CPU speed. P4 is the leading MIPI camera path; verify a separate wireless solution before committing.
- Camera: validate IMX219 module wiring, host capture/preview and app API; assess ST global shutter only as a distinct alternative with different integration requirements.
- Display: availability, price, scanout interface, image quality, responsiveness and power.
- Control layout: enjoyable gaming without sacrificing the general-purpose grid; reliable independent touch segments and slider gestures.
- Storage: dependable factory-installed internal card and externally removable expansion, recovery independent of card health, pin/interface feasibility and verified bulk supply.
- Dual processor: meaningful user freedom, robust recovery and acceptable overhead.
- Battery: volumetric/weighted mock-ups of flat pouch versus dual 21700, realistic workload measurements against the initial ten-hour active / two-week standby goals, validated USB-C charging and safe service/replacement.
- Manufacturing: verified parts, repeatable assembly, enclosure fit, testability, quote and compliance plan.

No schematic, firmware, industrial design, validated BOM or supplier quote exists in this repository yet.
