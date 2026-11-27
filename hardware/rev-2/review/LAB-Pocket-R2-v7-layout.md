# LAB Pocket Rev 2 v7 · Side ports

With the keypad facing you, the 3.5 mm CTIA headset jack opens to the left and USB-C opens to the right. Both are between the second and third edge LEDs counting from the top. The port centers are 48.925 mm and 45.3 mm from the top edge respectively. The board measures 74 × 152 mm with 2 mm corner radii. The assembled CAD envelope is 14.967 mm thick.

The Jauch pack rotates 180° in its plane and sits 10.15 mm lower. Its protected end and leads face the top. The battery connector sits 14.81 mm from the center of the USB footprint. The rear PCB reserves the pack’s maximum 59.5 × 78.5 mm footprint for its two adhesive strips. Each modeled lead runs 70 mm to its assigned contact.

The two 18 × 13 mm PUI speakers sit across the top of the rear face. Their spring contacts land on 2.5 mm square pads, spaced 15.5 mm apart per the manufacturer’s mounting drawing. The upper microphone pair moves 0.575 mm toward the top. All four acoustic ports remain exposed. The camera stays centered behind the display, with the color sensor and its illumination beside it. The radio module stays at the top edge for its antenna.

Both Hirose microSD sockets accept cards from the bottom edge in the same orientation. Viewed from the rear, the external slot is on the left and the internal slot is on the right. Relative to the outline, the nominal seated card tip is 0.075 mm inboard and the released tip projects 3.925 mm. The two side plugs and bottom card paths have open approaches in the model.

An additional 35 parts move beneath the screen, bringing the total to 72 electronics and test points plus the display connector. These include both processors, both flash chips, the IMU and charger. The closest IC packages are the flash chips, with a modeled 0.645 mm to the backlight frame. The display rails and flex path have reserved space. One right touch electrode is shortened to 4.4 mm for the USB locator holes.

The KiCad placement check verifies the twenty key networks, the individual key LED data links, the battery keepout and the relocated footprints. KiCad reports zero board-to-schematic parity findings, 339 unrouted connections, 104 processor copper clearance findings and four USB locator clearance findings. Plug fit, battery lead retention, acoustics and operating temperature still need hardware validation. [Board check](../check-layout-v7.py) · [Blender check](../check-scene-v7.py) · [Parts list](../parts-v7.csv) · [Datasheet archive](../datasheets/index-v5.csv)

Both front/rear pairs use the v6 cameras, scale and lighting. [Assembled views](../renders/LAB-Pocket-R2-v7-front-rear-assembled-r1.jpg) · [Screen and battery removed](../renders/LAB-Pocket-R2-v7-front-rear-screen-battery-removed-r1.jpg)
