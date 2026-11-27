"""Check the charge-enable window at worst-case IC, resistor and sensor corners."""
from itertools import product
from math import log, exp

# SEMITEC 103AT R/T table, ohms. Use log interpolation between table points.
table = [(0,27280), (10,17960), (20,12090), (25,10000), (30,8313), (40,5827), (50,4160)]
def temperature(ohms):
    for (t0,r0),(t1,r1) in zip(table,table[1:]):
        if r1 <= ohms <= r0:
            return t0 + (t1-t0)*log(r0/ohms)/log(r0/r1)
    raise ValueError(ohms)

results = {"cold": [], "hot": []}
# R30/31 attenuate TS at INA+. R32/33 attenuate the same TS at INB-.
# Include input leakage, both branches loading the BQ current source, 1% divider
# tolerance, and 2% resistance margin for combined NTC R25 and B tolerance.
for factors in product((.99,1.01), repeat=4):
    ah,bh,ac,bc = [r*f for r,f in zip((100e3,1e6,169e3,100e3),factors)]
    for its,ih,ic,therm in product((72e-6,78e-6),(-25e-9,25e-9),(-15e-9,15e-9),(.98,1.02)):
        for name,limits,a,b,ibias in (("hot",(.387,.400),ah,bh,ih),("cold",(.396,.404),ac,bc,ic)):
            for threshold in limits:
                vts=threshold*(1+a/b)+ibias*a
                ir=its-vts/(ah+bh)-ih*bh/(ah+bh)-vts/(ac+bc)-ic*bc/(ac+bc)
                results[name].append(temperature(vts/ir/therm))
for name,ts in results.items():
    print(f"{name} inhibit: {min(ts):.2f} to {max(ts):.2f} C")
assert min(results["cold"]) > 10 and max(results["hot"]) < 45
