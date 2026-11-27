# LAB Pocket Rev 2 v8 · Aligned side ports

Measured from the top edge, the left 3.5 mm headset jack and the right USB-C mouth both sit at **45.300 mm**. The audio footprint moves 3.625 mm toward the top. The locator pins on the audio axis and the midpoint of the symmetric USB locator pair give a longitudinal offset of 0.000 mm in KiCad. The assembled Blender model independently places both mouth centers at 45.300 mm to the nearest 0.001 mm.

Both ports remain in the second edge-LED gap. The nearest LED footprint is 2.325 mm from the audio footprint and 0.600 mm from USB. A 2.30 mm circular opening in the copper of touch electrode E5 clears the 1.50 mm jack locating pin by a nominal 0.40 mm radially. The left display support has matching relief for the inner pin. The electrode retains its 7.6 × 5.0 mm outline. The stock surface-mount bodies set the opening heights along the thickness of the device, approximately 2.55 mm off the rear board face for audio and 1.68 mm nominal for USB-C.

The assembled envelope is 74 × 152 × 14.967 mm. KiCad reports zero schematic-parity findings, 339 unrouted connections and 108 inherited clearance findings. This is a mechanical placement revision. [KiCad check](../check-layout-v8.py) · [Blender check](../check-scene-v8.py) · [Parts list](../parts-v7.csv) · [Manufacturer drawings](../datasheets/index-v5.csv)

[Assembled front and rear](../renders/LAB-Pocket-R2-v8-front-rear-assembled-r1.jpg) · [Screen and battery removed](../renders/LAB-Pocket-R2-v8-front-rear-screen-battery-removed-r1.jpg)
