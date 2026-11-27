# Rev 3 prototype verification

| Check | Result |
|---|---|
| KiCad 10.0.6 ERC, all reported severities | 0 issues across 22 schematic sheets |
| KiCad 10.0.6 DRC, all reported severities | 0 violations, 0 unconnected items, 0 schematic parity issues, 0 item exclusions |
| Board profile | 74.00 × 152.00 mm, 2.00 mm corner radius, 8 copper layers |
| Fabrication exports | 15 plotted layers, one Gerber job manifest, separate plated and non-plated drill files |
| Minimum mechanical via | 0.15 mm drill and 0.32 mm copper land |
| Assembly reference check | Exact BOM/CPL set match across 344 unique placements, 227 top and 117 bottom |
| USB-C pin-to-pin geometric lengths | D+ 90.4585 mm, D− 90.4586 mm to the A contacts and the B contacts |
| Camera pin-to-pin geometric lengths | All six conductors between 39.4110 and 39.4115 mm |
| Jauch charge temperature window, calculated component corners | Cold inhibit 11.64–16.18 °C, hot inhibit 37.05–42.02 °C |

The native reports include the project’s ignored rule categories. The board has no individual DRC exclusions. The length check follows routed tracks and includes travel between foil centerlines in vias. Physical length does not establish propagation skew, impedance or an eye diagram. [Board report](LAB-Pocket-R3-DRC-r1.json) · [Schematic report](LAB-Pocket-R3-ERC-r1.json)

## Reproduce the electrical checks

From the Rev 3 directory, use KiCad 10.0.6 and its system Python bindings.

```sh
kicad-cli sch erc --severity-all --exit-code-violations -o /tmp/LAB-Pocket-R3-ERC.rpt kicad/LAB-Pocket-R3.kicad_sch
kicad-cli pcb drc --severity-all --schematic-parity --exit-code-violations -o /tmp/LAB-Pocket-R3-DRC.rpt kicad/LAB-Pocket-R3.kicad_pcb
/usr/bin/python3 validation/check-interface-lengths-R3.py
python3 validation/check-charge-window-R3.py
```

## First article

1. Check assembly alignment and polarity, resistance to ground and the three J6 contacts. Bring up USB with a current-limited supply and a battery simulator. Verify 3.3 V, processor core rails, camera rails, the LED supply and power sequencing under load.
2. Verify pack temperature inhibits, connector fault behavior, input-current selection and power transitions. Record charger and pouch temperatures while operating the display and radio during a charge. At 5.0 V input, 3.3 V cell voltage and 0.89 A charge current, the linear charging path alone dissipates approximately 1.5 W. Thermal regulation can extend charge time. [Battery procedure](../battery-R3.md) · [BQ24074 datasheet](../datasheets/BQ24074.pdf)
3. Check USB High-Speed enumeration and sustained transfer with the plug in each orientation. Exercise the IMX219 at the intended CSI lane rate and monitor receiver errors. The tightest camera connector breakout includes inner-layer routing and a nearest ground-stitch distance of approximately 4.25 mm at one clock transition. Obtain the impedance coupon results and validate that launch on the prototype. [Stack and trace geometry](../manufacturing/stackup-R3-r1.md)
4. Test both card slots, keypad and pixels, radio, microphones, audio paths, panel timing and backlight. Measure rail ripple and battery current at maximum intended simultaneous brightness and audio load before selecting a firmware brightness ceiling.
