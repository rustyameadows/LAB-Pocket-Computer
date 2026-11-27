# Rev 3A fabrication stack

Use JLCPCB JLC08161H-3313, nominal 1.6 mm FR-4, 1 oz external copper, 0.5 oz internal copper and ENIG. The production calculator identifies this construction as 1.57 mm finished with a ±10% tolerance. Keep the board edge and thickness within the assembly drawing. [JLCPCB stack selection](https://jlcpcb.com/pcb-impedance-calculator) · [Manufacturer's eight-layer reference](https://jlcpcb.com/blog/multilayer-pcb-design-guidelines)

| From top to bottom | Thickness in mm | Function or material |
|---|---:|---|
| F.Cu | 0.0350 | Front components and signals |
| Prepreg | 0.0994 | 3313, nominal Dk 4.10 |
| In1.Cu | 0.0152 | Ground fill with local signal and supply routing |
| Core | 0.1000 | FR-4, Dk 4.36 |
| In2.Cu | 0.0152 | Signals, 3.3 V and battery distribution |
| Prepreg | 0.3568 | Three 2116 plies, Dk 4.16 |
| In3.Cu | 0.0152 | Signals and supply distribution |
| Core | 0.3000 | FR-4, Dk 4.41 |
| In4.Cu | 0.0152 | Signals, 3.3 V and battery distribution |
| Prepreg | 0.3568 | Three 2116 plies, Dk 4.16 |
| In5.Cu | 0.0152 | Signals and supply distribution |
| Core | 0.1000 | FR-4, Dk 4.36 |
| In6.Cu | 0.0152 | Ground fill with local signal and supply routing |
| Prepreg | 0.0994 | 3313, nominal Dk 4.10 |
| B.Cu | 0.0350 | Rear components and high-speed pairs |

Mechanically drilled through-vias include 0.15 mm holes in 0.32 mm lands for dense escapes. Select epoxy-filled, copper-capped, planarized via-in-pad processing. The rear pouch requires a smooth, solder-masked bonding surface. Allow for the small-drill fabrication surcharge when pricing. [JLCPCB drilling and copper limits](https://jlcpcb.com/capabilities/pcb-capabilities) · [JLCPCB via covering](https://jlcpcb.com/help/article/pcb-via-covering)

Specify 90 Ω differential for USB High-Speed and 100 Ω differential for camera CSI-2, with coupon measurement and ±10% tolerance. The nominal outer-layer width and edge gap are 0.170/0.150 mm for USB and 0.150/0.190 mm for CSI. The CAD stack includes a 0.015 mm mask approximation. Confirm the etched widths and laminate build with the fabricator before approving production. The footprint launches, filled vias and uncoupled tuning sections need first-article interface testing.

Both reference layers include local routes. The principal paired runs use rear outer-layer microstrip. The camera connector escape also uses In2.Cu and In5.Cu on individual conductors, with approximately 9.3 mm of inner routing on CSI_D1_N. Include these launches in the interface review. [Pin-to-pin verification and first-article tests](../LAB-Pocket-R3A-handoff-r1.md)
