#!/usr/bin/env python3
"""Controle geometrique de l'ensemble moteur / berceau / roue.

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd check_faulhaber_assembly.py

Relit les sept STEP de 3d/ tels que KiCad les chargera et verifie ce qu'aucune
relecture de cotes ne montre : qu'aucune piece n'en traverse une autre, et que
les quatre jeux qui decident du montage sont bien ceux voulus. A relancer apres
toute retouche de faulhaber_geom.py.
"""
import os, sys, itertools
import FreeCAD as App
import Part

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import faulhaber_geom as G

NAMES = ["Motor_bracket_1524", "Faulhaber_15-10_gearhead",
         "Faulhaber_1524_motor", "Faulhaber_IE2-1024_encoder",
         "JSumo_JS4311_hub", "JSumo_JS4311_tire"]

# jeux voulus, en mm : (piece a, piece b, valeur, tolerance)
GAPS = [("Motor_bracket_1524", "JSumo_JS4311_hub", G.WHEEL_GAP, 0.02,
         "platine / face interne de la roue"),
        ("Motor_bracket_1524", "Faulhaber_1524_motor", G.BR_BORE_D / 2 - G.MOT_D / 2,
         0.01, "jeu du berceau sur le corps"),
        ("Motor_bracket_1524", "Faulhaber_15-10_gearhead", 0.00, 0.01,
         "platine / face de sortie (contact)")]

shapes = {}
for n in NAMES:
    s = Part.Shape()
    s.read(os.path.join(HERE, "3d", n + ".step"))
    shapes[n] = s

bad = 0
print("Interferences :")
found = False
for a, b in itertools.combinations(NAMES, 2):
    v = shapes[a].common(shapes[b]).Volume
    if v > 0.01:
        print(f"  {a} / {b} : {v:.2f} mm3")
        found = True
        bad += 1
if not found:
    print("  aucune")

print("\nJeux :")
for a, b, want, tol, label in GAPS:
    d = shapes[a].distToShape(shapes[b])[0]
    ok = abs(d - want) <= tol
    print(f"  {label:<38} {d:5.2f} mm   attendu {want:.2f}   "
          f"{'ok' if ok else '<<< ECART'}")
    if not ok:
        bad += 1

print("\nCharge radiale sur les paliers frittes :")
print(f"  porte-a-faux de la roue              {G.WHEEL_OVERHANG:5.2f} mm depuis la face")
print(f"  admissible a cette distance          {G.RADIAL_ALLOWED:5.2f} N   "
      f"({G.GEAR_RADIAL_MAX:.0f} N a {G.GEAR_RADIAL_REF:.1f} mm)")

print("\nGarde au sol :")
z = min(shapes[n].BoundBox.ZMin for n in ("JSumo_JS4311_tire",))
print(f"  point bas de la gomme                {z:5.2f} mm / dessus de carte")
print(f"  garde sous le dessous de carte       {-z - G.PCB_T:5.2f} mm   "
      f"attendu {G.CLEARANCE:.2f}")
if abs(-z - G.PCB_T - G.CLEARANCE) > 0.02:
    bad += 1

sys.stdout.flush()
if bad:
    raise RuntimeError(f"{bad} anomalie(s) : voir ci-dessus")
print("\nassemblage conforme")
