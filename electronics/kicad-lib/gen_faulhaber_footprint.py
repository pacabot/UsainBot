#!/usr/bin/env python3
"""Genere les deux empreintes de la motorisation Faulhaber.

    python3 gen_faulhaber_footprint.py

    Motor_Faulhaber_1524_15-10   le motoreducteur sur son equerre-berceau
    Motor_bracket_1524_shim      l'entretoise, a poser dans une chute de la carte

Toutes les cotes viennent de faulhaber_geom.py. Meme convention que le
GM12-N20 : axe moteur suivant Y, arbre vers -Y, Z=0 au dessus de la carte.
L'origine est le centre de l'equerre, qui est symetrique en X et en Y.

Aucune connexion electrique : le moteur ET le codeur passent par la nappe six
conducteurs du codeur, connecteur EN 60603-13 / DIN 41651 au pas 2,54 (2x3) —
1 Moteur-, 2 Moteur+, 3 GND, 4 UDD, 5 Voie B, 6 Voie A. C'est une embase a part
dans le schema, pas un pad de cette empreinte.
"""
import math
import faulhaber_geom as G

NAME = "Motor_Faulhaber_1524_15-10"
SHIM = "Motor_bracket_1524_shim"
CLEAR = 0.25

# Le bas de la roue passe sous la carte : le contour doit etre degage sur cette
# demi-largeur, la ou le disque descend sous Z=0.
X_CUT = math.sqrt((G.WHEEL_D / 2) ** 2 - G.AXIS_Z ** 2)

MODELS = ("Motor_bracket_1524",           # equerre aluminium
          "Faulhaber_15-10_gearhead",     # reducteur, inox
          "Faulhaber_1524_motor",         # moteur, acier nickele
          "Faulhaber_IE2-1024_encoder",   # codeur, sombre
          "JSumo_JS4311_hub",             # moyeu alu
          "JSumo_JS4311_tire")            # gomme silicone


def line(x1, y1, x2, y2, layer, w):
    return (f'\t(fp_line (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f})\n'
            f'\t\t(stroke (width {w}) (type solid)) (layer "{layer}"))\n')


def rect(x1, y1, x2, y2, layer, w, style="solid"):
    return (f'\t(fp_rect (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f})\n'
            f'\t\t(stroke (width {w}) (type {style})) (fill no) (layer "{layer}"))\n')


def circle(x, y, r, layer, w):
    return (f'\t(fp_circle (center {x:.3f} {y:.3f}) (end {x + r:.3f} {y:.3f})\n'
            f'\t\t(stroke (width {w}) (type solid)) (fill no) (layer "{layer}"))\n')


def outline(layer, w):
    """Le contour de l'equerre : plein largeur au droit des vis, pince aux bouts."""
    h, v, e, t = G.BR_W / 2, G.BR_L / 2, G.BR_W_END, G.TAPER_LEN
    pts = [(e, -v), (h, -v + t), (h, v - t), (e, v),
           (-e, v), (-h, v - t), (-h, -v + t), (-e, -v)]
    xy = " ".join(f"(xy {x:.3f} {y:.3f})" for x, y in pts)
    return (f'\t(fp_poly (pts {xy})\n'
            f'\t\t(stroke (width {w}) (type solid)) (fill no) (layer "{layer}"))\n')


def npth(x, y, d):
    return (f'\t(pad "" np_thru_hole circle (at {x:.3f} {y:.3f}) (size {d} {d})\n'
            f'\t\t(drill {d}) (layers "F&B.Cu" "*.Mask"))\n')


def head(name, descr, tags, ref_y, val_y, value):
    s = f'(footprint "{name}"\n\t(version 20260206)\n\t(generator "pacabot-gen")\n'
    s += '\t(generator_version "10.0")\n\t(layer "F.Cu")\n'
    s += f'\t(descr "{descr}")\n\t(tags "{tags}")\n'
    s += ('\t(attr through_hole exclude_from_pos_files exclude_from_bom '
          'allow_missing_courtyard)\n')
    s += (f'\t(property "Reference" "{"M**" if value else "REF**"}" '
          f'(at 0 {ref_y:.3f} 0) (layer "F.SilkS")\n'
          '\t\t(effects (font (size 1 1) (thickness 0.15))))\n')
    s += (f'\t(property "Value" "{value or name}" (at 0 {val_y:.3f} 0) (layer "F.Fab")\n'
          '\t\t(effects (font (size 1 1) (thickness 0.15))))\n')
    return s


# ===================================================== le motoreducteur
y_back = G.Y_ENC_BACK
s = head(NAME,
         f"Faulhaber 1524T006SR + IE2-1024 + planetary gearhead 15/10 3.33:1 on "
         f"machined aluminium cradle, mechanical only. 4x M2 NPTH, "
         f"{2 * G.BR_X_THREAD:.1f} x {2 * G.BR_Y_HOLE:.1f} mm. Axis {G.AXIS_Z:.2f} mm "
         f"above board top, set by {G.SHIM_N} x {G.SHIM_T:.1f} mm PCB shims. "
         f"JSumo JS4311 wheel 43x11.",
         "motor faulhaber 1524 gearmotor encoder cradle mechanical",
         y_back + 2, y_back + 4, "1524T006SR")

# --- quatre trous de fixation, sous les joues de l'equerre. Les taraudages sont
# traversants : ces memes quatre positions recoivent la platine de renfort par le
# dessus, ce qui rend l'equerre symetrique en Y.
for sx in (-1, 1):
    for sy in (-1, 1):
        s += npth(sx * G.BR_X_THREAD, sy * G.BR_Y_HOLE, G.PCB_DRILL)

# --- F.Fab : equerre, corps, reducteur, codeur, arbre
s += outline("F.Fab", 0.1)
s += circle(0, G.Y_FLANGE + G.BR_FLANGE_T / 2, G.FLANGE_R, "F.Fab", 0.1)  # disque
s += line(-G.BR_W / 2, G.Y_FACE, G.BR_W / 2, G.Y_FACE, "F.Fab", 0.1)   # dos du disque
s += rect(-G.MOT_D / 2, G.Y_FACE, G.MOT_D / 2, y_back, "F.Fab", 0.1)   # corps Ø15
s += line(-G.MOT_D / 2, G.Y_GEAR_BACK, G.MOT_D / 2, G.Y_GEAR_BACK, "F.Fab", 0.1)
s += line(-G.MOT_D / 2, G.Y_MOT_BACK, G.MOT_D / 2, G.Y_MOT_BACK, "F.Fab", 0.1)
s += rect(-G.SHAFT_D / 2, G.Y_SHAFT_TIP, G.SHAFT_D / 2, G.Y_FACE, "F.Fab", 0.1)
# les quatre taraudages, vus du dessus : ils recoivent la platine de renfort
for sx in (-1, 1):
    for sy in (-1, 1):
        s += circle(sx * G.BR_X_THREAD, sy * G.BR_Y_HOLE, 1.0, "F.Fab", 0.1)

# --- F.SilkS : l'equerre seule, c'est elle qu'on pose
s += outline("F.SilkS", 0.12)

# --- Dwgs.User : la roue, et ce qu'il faut degager du contour de carte
s += rect(-G.WHEEL_D / 2, G.Y_WHEEL_OUT, G.WHEEL_D / 2, G.Y_WHEEL_IN,
          "Dwgs.User", 0.05, "dash")
s += rect(-X_CUT, G.Y_WHEEL_OUT, X_CUT, G.Y_WHEEL_IN, "Dwgs.User", 0.15)
s += (f'\t(fp_text user "decoupe roue" '
      f'(at 0 {(G.Y_WHEEL_IN + G.Y_WHEEL_OUT) / 2:.3f} 0)\n'
      '\t\t(layer "Dwgs.User") (effects (font (size 0.8 0.8) (thickness 0.12))))\n')

# --- F.CrtYd : ce qui touche la carte ; la roue est hors carte
x_c = G.BR_W / 2 + CLEAR
s += rect(-x_c, G.Y_FLANGE - CLEAR, x_c, y_back + CLEAR, "F.CrtYd", 0.05)

for mdl in MODELS:
    s += f'\t(model "${{KIPRJMOD}}/kicad-lib/3d/{mdl}.step"\n'
    s += '\t\t(offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))\n'
s += ')\n'
open(f"Pacabot.pretty/{NAME}.kicad_mod", "w").write(s)

# ===================================================== l'entretoise
# Une chute de la carte mere, au format de l'equerre. Le contour part sur
# Edge.Cuts : pose dans une zone perdue du panneau, elle se decoupe avec la
# carte. Prevoir des pontets ou demander l'usinage a onglets au fabricant, sinon
# la piece tombe pendant le routage.
v = G.BR_L / 2
s = head(SHIM,
         f"PCB shim for the Faulhaber motor cradle. Stack {G.SHIM_N} of them "
         f"({G.SHIM_N} x {G.SHIM_T:.1f} = {G.BR_Z0:.2f} mm) to set the axle height. "
         f"Outline on Edge.Cuts: place in an unused area of the panel.",
         "shim spacer motor cradle faulhaber edge-cuts",
         -v - 2, v + 2, None)
for sx in (-1, 1):
    for sy in (-1, 1):
        s += npth(sx * G.BR_X_THREAD, sy * G.BR_Y_HOLE, G.PCB_DRILL)
s += outline("Edge.Cuts", 0.1)
s += outline("F.Fab", 0.1)
# le berceau ne porte que sur ses joues : evider le milieu allege le panneau et
# evite que l'entretoise ne touche le fond du berceau
s += rect(-G.BR_BORE_D / 2 + 1.0, -v + 4.0, G.BR_BORE_D / 2 - 1.0, v - 4.0,
          "Edge.Cuts", 0.1)
s += ')\n'
open(f"Pacabot.pretty/{SHIM}.kicad_mod", "w").write(s)

print(f"ecrit : Pacabot.pretty/{NAME}.kicad_mod")
print(f"  4 trous M2 a (+/-{G.BR_X_THREAD}, +/-{G.BR_Y_HOLE}), percage {G.PCB_DRILL} mm")
print(f"  emprise Y : {G.Y_FLANGE:.2f} .. {y_back:.2f}   ({y_back - G.Y_FLANGE:.2f} mm)")
print(f"  emprise X : +/-{x_c:.2f} mm")
print(f"  roue Ø{G.WHEEL_D:.0f} : degager le contour sur +/-{X_CUT:.2f} mm "
      f"entre Y {G.Y_WHEEL_OUT:.2f} et {G.Y_WHEEL_IN:.2f}")
print(f"  taraudages traversants : les memes quatre positions servent a la "
      f"platine de renfort")
print(f"ecrit : Pacabot.pretty/{SHIM}.kicad_mod")
print(f"  {G.BR_W:.0f} x {G.BR_L:.0f} mm, a tirer en {G.SHIM_N} exemplaires par moteur")
print(f"  hauteur d'axe {G.AXIS_Z:.2f} mm, garde au sol "
      f"{G.WHEEL_D / 2 - G.AXIS_Z - G.PCB_T:.2f} mm")
