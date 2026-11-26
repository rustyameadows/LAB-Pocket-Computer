# Starter applications

A small, designed collection of default apps should establish the product's personality. Each app is useful or playful in its own right and demonstrates one or more SDK capabilities. Treat this as a candidate slate rather than a fixed launch requirement.

| App | Experience | Demonstrates |
| --- | --- | --- |
| Clock | Beautiful, customizable glanceable time display; optional sunset/night glow | Time, typography, ambient lifecycle, LEDs |
| Weather | Current conditions and simple forecast | Wi-Fi, caching, periodic updates, offline states |
| Sensor studio | Live acceleration, rotation, light, and optional external sensor data | Sensors, charts, BLE, data logging |
| Color synth / colorscope | Use the grid to mix palettes and the rear illuminated color sensor to sample physical colors; save palettes and synchronize screen and rear glow | Color sensing, calibration, input mapping, graphics, persistence, lighting |
| Visual toy | Generative patterns, pixel animations and interactive loops | Animation, sprites, performance |
| Camera studio | Rear-camera live view, snapshots, pixel-art filters, stop-motion and optical experiments | Camera preview, image processing, controls, storage |
| Voice recorder | Record, play, name and export a short clip | Microphone, audio, filesystem |
| Music toy/player | Tiny sequencer or local-file player; light reacts to playback | Audio timing, storage, lighting |
| Arcade game | Original falling-block or similar responsive 2D game | Input latency, steady frame rate, collision and audio |
| Pocket creature | Small original virtual pet with persistent state | Time, saves, animation, low-power behavior |
| Live dashboard | User-defined data source, status, score or project progress | Networking, refresh policy, ambient display |

## Design constraints

Apps should feel intentionally designed for this fixed physical device, not like miniaturized phone apps. Establish a clear control mapping, readable visual hierarchy, fast start, useful offline states where appropriate, and an obvious way back to the launcher. Rear lighting should have a purpose and respect a global off/brightness setting. Avoid dependency on a microphone, speaker or specific sensor until that hardware is confirmed.

## Launch priority

Start with the color synth, clock and an arcade game. Together these prove interactive graphics, the tactile input model, low-distraction ambient mode and the SDK. Add weather, sensors, camera and audio once the corresponding hardware and APIs are stable.

Provide example source, a short explanation of what each project teaches and instructions for building, previewing and installing. Prefer small, forkable projects over one giant monolithic demo.
