# Rev 3 battery and USB power

BT1 is the protected Jauch 246524, 3.7 V nominal, 4.8 Ah minimum and 5 Ah typical. The pouch bonds to the rear face with the two existing 9495LE strips. The manufacturer drawing gives a 59.5 × 78.5 mm maximum outline, 7.3 mm thickness at delivery and 7.9 mm after cycling. The rear component keepout spans board coordinates X 71.25–130.75 mm and Y 92.00–170.50 mm. Leave the outward-facing pouch surface free to expand. [Jauch pack drawing](datasheets/Jauch-246524-pack-drawing.png)

Keep the NTC and the wire splice off the adhesive footprint. The foil pouch needs an even support surface with no components, wire crossings or raised solder joints pressing into it.

## Hand harness

| J6 pin on board | Termination |
|---|---|
| 1 | Protected pack negative, with a separate splice to the NTC return |
| 2 | SEMITEC 103AT-2 sensing lead |
| 3 | Protected pack positive |

Use the JST PHR-3 housing and three SPH-002T-P0.5S terminals. Jauch supplies 24 AWG red and black leads, 70 ± 5 mm long. Crimp the positive lead directly and use an insulated return splice and one 24 AWG pigtail at the negative contact. Fit each terminal to one conductor. Bond the insulated NTC head flat to the pouch face with a strip of 3M 5413 polyimide tape and secure both sensor leads for strain relief. Keep the sensor away from the PCB charger, the PCM and the wire exit. Preserve the sealed pack and factory protection circuit. Check polarity with a meter at the keyed plug before first insertion.

## Charge controls

U11 supplies VSYS from USB or battery and regulates the cell to 4.2 V nominal. The 1.00 kΩ ISET resistor gives 0.890 A nominal and a calculated 0.985 A maximum including 1% resistor tolerance. A Type-C source advertising at least 1.5 A selects 1.5 kΩ ILIM, or 1.073 A nominal and at most 1.159 A. A default-current source selects the 100 mA input setting. The load has priority and charge current falls when available input current is insufficient. Full charging from empty is intended on the high-current Type-C setting. An ordinary 100 mA port can exhaust the safety timer before full charge.

RT1 drives the charger's TS input and two comparator inputs. Either temperature limit pulls Q1's gate low. R35 then pulls CE high to inhibit charging. A missing or shorted sensor also inhibits charge. The 68 kΩ safety timer gives 9.07 h nominal fast-charge time before TI's dynamic timer adjustments. Jauch specifies charge from 10 to 45 °C. Run the tolerance check with `python3 validation/check-charge-window-R3.py`. It uses the manufacturer R/T table, both divider loads, the BQ bias range, comparator thresholds and input leakage. Actual cell-to-sensor thermal lag requires measurement.

The MAX17048 measures the protected pack terminal and reports voltage and estimated state of charge on I²C address 0x36. The PCA9555 reads active-low CHG, PGOOD and gauge alert on P0.5, P0.6 and P0.7. Start with the default ModelGauge profile and compare readings against a measured discharge cycle before relying on the percentage.

## First electrical test

Use a current-limited USB source and a battery simulator capable of sinking charge current. Start with the high-power loads off. Verify USB current selection on both cable orientations, then emulate RT1 with a resistance box and record CE, TS, pack voltage and current through each trip point. Test a disconnected sensor, shorted sensor, detached USB and a full pack. With the actual pack fitted, measure pouch temperature and charger-board temperature during a complete charge at the intended load. Check shutdown under load near 3.0 V and record recovery on USB insertion.

Source documents are in [datasheets](datasheets). The BQ24074 electrical characteristics, TPS3700 thresholds, SEMITEC R/T table and Jauch charge conditions define the electrical test limits.
