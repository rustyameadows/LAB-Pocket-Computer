# Developer ecosystem

The differentiator is not simply that LAB runs apps. It should be unusually easy to make a physical computing experience, including with coding agents.

## Development paths

1. SDK apps: a small, approachable runtime with portable hardware APIs. Explore interpreted and compiled workflows rather than choosing the language prematurely.
2. Native apps: compiled C/C++ or Rust for the RP2350B with direct access to documented hardware and host services.
3. Bare-metal user firmware: replace RP2350B firmware entirely; optionally use host services via the published protocol. Host recovery remains independent.

The SDK should make the simple path delightful without blocking the advanced path. Separate host firmware releases from user app releases. Document which host services are available during bare-metal use.

## Proposed capability surface

- Graphics: text, shapes, sprites, tiles, palettes, images, animation and framebuffer operations.
- Input: button press/release, held state, chords and repeat timing; two seven-segment capacitive rails with individual touch states, slider position and gesture events. Keep mappings app-defined.
- Audio: tone/music synthesis, playback, recording where supported.
- Light: 12 individually addressable LEDs with safe brightness limits and animation.
- Sensors: motion, environmental data, ambient light and expansion peripherals.
- Camera: host-managed rear-camera live preview, frame and pixel access, still capture, supported controls, storage and optional host-side image processing. Negotiate available formats/resolutions/rates and explicit capture permissions; do not require full-resolution transfer to the RP2350B.
- Data: scoped persistent internal storage, separately mounted removable microSD media, card presence/mount events, safe removal and import/export, time, network requests and BLE with permission boundaries.
- Lifecycle: launch, suspend, resume, exit, background/ambient behavior, reset and error reporting.

Consider app manifests containing identity, version, supported hardware/runtime, permissions, assets, controls, entrypoint and ambient support. Define package validation, atomic installs and rollback. Do not hard-code a manifest format before prototyping.

## Playground and tooling

A browser-based virtual LAB should reproduce the display, button grid, dual seven-segment touch rails and rear lighting. Simulate sensor values, time, connectivity, app lifecycle, separate storage volumes and card insertion/removal; support simulated camera input from test images/video or an explicitly permitted webcam. Include a file editor or import, preview, input automation, console and install/export workflow. A local CLI can build and deploy without the web service.

Provide agent-ready documentation and examples, a Codex plugin or skill, and MCP tools where useful. A coding agent should be able to discover the SDK, generate an app, build it, run it in the emulator, capture a screenshot, press buttons, inspect logs, test behavior and deploy to the device with user approval. Firmware replacement is a separate explicit action.

Keep AI off the device as a product default. The creation environment can use whatever coding agent the developer prefers.

## Emulation and verification

The virtual device must reflect real API semantics, not just render a mock interface. Start with host-protocol/API simulation; instruction-level RP2350 emulation is an open decision. Hardware-in-the-loop tests cover timing, memory, power and radio behavior that a simulator cannot establish.

Create a small compatibility suite: drawing, controls, multi-button input, touch segment/slider gestures, animation, audio, LED timing, sensor injection, camera frames and capture behavior, internal/external storage behavior and recovery. Enable repeatable screenshot and behavioral checks for agents.

## Community and openness

A future app library can showcase installable apps, example source and forks. Make built-ins available as teaching projects where licensing permits. Support sideloading without a mandatory cloud account. Open decisions include SDK/firmware licensing, distribution policy, signing, permissions, trust indicators and community moderation. Networked apps should not silently expose secrets or local devices; define capability boundaries and user approval flows.

## First vertical slice

A color instrument that maps buttons to hue/saturation/brightness, renders a full-screen color, lights the underside, saves a palette and runs equivalently in the emulator and on hardware. Then use the same toolchain for a small game and a networked ambient clock. This exercises the platform before building an app store.
