# Prototype roadmap

This is a proposed learning sequence, not an engineering schedule or launch commitment.

## Phase 0: bench prototype

Use readily available ESP32-S3 and RP2350 development boards. Connect a representative square LCD, tactile buttons, addressable LEDs and power-monitoring equipment. Verify exact candidate parts and availability separately.

- Bring up display scanout, input and host lighting; evaluate two seven-segment capacitive rails and their coexistence with other peripherals.
- Test host access to internal and removable microSD volumes, simultaneous transfers, safe removal, missing/corrupt media recovery and power-loss behavior.
- Establish a two-way processor protocol and boot/recovery path.
- Run the color synth and a representative 2D game.
- Test both host-side drawing commands and bitmap transfers.
- Measure FPS, frame pacing, end-to-end input latency, interprocessor throughput, memory headroom and performance while Wi-Fi/audio are active.
- Crash/hang the user program intentionally and prove that the host can return to the launcher and reinstall known-good firmware.

## Phase 1: software vertical slice

Develop the minimum launcher, SDK, app package/install path, virtual device and CLI/agent workflow. Build the color synth, ambient clock and small game with the same API. Test app portability between virtual and real devices. Specify permissions, update rollback and recovery.

## Phase 2: form and power

Prototype several 16-button grid layouts and a physical mock-up at the selected display size. Compare game ergonomics, two-thumb use, desk readability, key spacing and switch feel; prototype seven-segment rails along both display edges, including accidental grip touches and exposed/covered electrode options. Verify internal card retention/service access and external card access. Evaluate feet/standoff height and rear LED diffusion. Test display alternatives if the 320 × 320 panel does not meet brightness, viewing or performance needs.

Profile interactive, ambient, Wi-Fi and standby power on real hardware. Validate the battery protection and charging design with appropriate engineering review. Decide whether a more capable host or alternative display is warranted.

## Phase 3: custom PCBA

Create schematics, pin allocation, PCB layout, mechanical model, exact BOM and test plan. Review RF, power, ESD, battery safety and programming interfaces. Request quotes and order a small run (around 10 boards). Attach separately sourced displays and batteries if necessary, and use 3D-printed enclosures for early prototypes.

Validate assembly, factory programming, test coverage, thermals, battery runtime, wireless, audio and recovery. Only then refine the design for pilot manufacturing and certification.

## Decision gates

- S3 versus P4: representative 60 FPS graphics with acceptable latency, memory headroom and power, not theoretical CPU speed.
- Display: availability, price, scanout interface, image quality, responsiveness and power.
- Control layout: enjoyable gaming without sacrificing the general-purpose grid; reliable independent touch segments and slider gestures.
- Storage: dependable factory-installed internal card and externally removable expansion, recovery independent of card health, pin/interface feasibility and verified bulk supply.
- Dual processor: meaningful user freedom, robust recovery and acceptable overhead.
- Battery: realistic workload measurements against the initial ten-hour active / two-week standby goals.
- Manufacturing: verified parts, repeatable assembly, enclosure fit, testability, quote and compliance plan.

No schematic, firmware, industrial design, validated BOM or supplier quote exists in this repository yet.
