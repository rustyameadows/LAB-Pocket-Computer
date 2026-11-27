# Rev 3 pixel selection

LED1–LED12 use the Worldsemi WS2812B-V6 in the 5.0 × 5.0 mm PLCC-4 package, JLCPCB/LCSC C52917433. The footprint follows the Worldsemi V6 recommended land pattern. Verify the chamfer against pin 3 (VSS) at assembly. Pin 1 is VDD, pin 2 is data out and pin 4 is data in.

The 20 keypad pixels use SK6805-EC10-000 so each still fits between the switch terminals. The 5 V boost supplies both chains, with the 3.3 V data translated by U8. Limit simultaneous full-white brightness in firmware to the measured system power budget. Verify the farthest pixel rail under a step to white on a nearly discharged pack.

[Worldsemi V6 datasheet](datasheets/WS2812B-V6-EN-r1.pdf) · [JLCPCB part listing](https://jlcpcb.com/partdetail/C52917433) · [Keypad pixel datasheet](datasheets/SK6805-EC10-000.pdf)
