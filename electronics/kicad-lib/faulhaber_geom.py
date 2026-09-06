#!/usr/bin/env python3
"""Cotes de la motorisation Faulhaber — source unique.

Importe par les trois generateurs :
    gen_faulhaber_3d.py         modeles STEP places dans le repere de l'empreinte
    gen_faulhaber_footprint.py  l'empreinte et celle des entretoises
    check_faulhaber_assembly.py controle des interferences et des jeux
L'equerre-berceau, elle, ne se genere plus : c'est un corps PartDesign,
../../mechanics/Motor_bracket_1524.FCStd, a tenir a la main en phase avec ces
cotes (voir README.md).

Repere de l'empreinte, identique a celui du GM12-N20 :
    X  transversal            Y  axe moteur, arbre vers -Y
    Z  vertical, 0 = dessus de la carte
    origine = centre de l'equerre, qui est symetrique en X et en Y

Les cotes du moteur et du reducteur sont RELEVEES SUR LES STEP OFFICIELS
Faulhaber (3d/vendor/), pas saisies depuis les plans : voir 3d/vendor/README.md.
"""

# ---------------------------------------------------------------- moteur 1524T006SR
MOT_D        = 15.00   # corps, releve : r = 7.5
MOT_L        = 24.80   # corps nu, releve : Z -1.0 .. 23.8
MOT_FACE_Z   = 23.80   # face avant du moteur dans son propre STEP
ASSY_OFFSET  = 40.90   # L1 : decalage a appliquer au STEP moteur pour l'assembler

# ---------------------------------------------------------------- codeur IE2-1024
ENC_L        = 1.40    # rallonge annoncee ; L1(1524...SR) = 26.2 = 24.8 + 1.4
ENC_D        = 15.00
# nappe PVC 6 conducteurs, connecteur EN 60603-13 / DIN 41651 au pas 2,54 (2x3) :
# 1 Moteur-  2 Moteur+  3 GND  4 UDD  5 Voie B  6 Voie A
ENC_RIBBON_W = 8.00
ENC_RIBBON_T = 0.60

# ---------------------------------------------------------------- reducteur 15/10 3,33:1
# Version a PALIERS FRITTES (pas la K a roulements) : la portee de centrage ne
# fait que 0,5 mm de saillie, l'arbre Ø3 commence 0,2 mm plus loin, et surtout la
# charge radiale admissible tombe a 4 N a 6,5 mm de la face — voir README.
GEAR_STEP    = "15-10_1stage.stp"
GEAR_L       = 17.10   # une etage, releve : Z -17.1 .. 0
GEAR_D       = 15.00
GEAR_BOSS_D  = 7.00    # portee de centrage, releve : r = 3.5
GEAR_BOSS_H  = 0.50    # saillie ; 1,00 sur la version K
GEAR_M2_PCD  = 11.00   # 2 trous M2 a (0, +/-5.5) — foret de taraudage releve 1.6
GEAR_UNC_PCD = 10.92   # 2 trous 2-56 UNC a (+/-5.46, 0) — foret releve 1.8
GEAR_THREAD_DEPTH = 3.00
GEAR_RADIAL_MAX = 4.00 # N, a 6,5 mm de la face d'appui (30 N sur la version K)
GEAR_RADIAL_REF = 6.50
SHAFT_D      = 3.00
SHAFT_TIP    = 14.20   # depuis la face de sortie
SHAFT_START  = 2.20    # debut du Ø3 ; avant : epaulements Ø4,5 puis Ø3,4
SHOULDER_D   = 4.50

# ---------------------------------------------------------------- roue JSumo JS4311
WHEEL_D      = 43.00
WHEEL_W      = 11.00
TIRE_W       = 8.00
TIRE_ID      = 35.00   # reconstruit : ajuste pour retrouver les 17,7 g annonces
WHEEL_BORE   = 3.00
WHEEL_GAP    = 0.50    # jeu entre la platine et la face interne de la roue

# ---------------------------------------------------------------- geometrie du robot
PCB_T        = 1.60
CLEARANCE    = 5.00    # garde au sol visee (ITR8307 : 2 a 4 mm utiles)

# ---------------------------------------------------------------- equerre-berceau
# Piece usinee dans un bloc d'alu. Aucun conge : ce qui lui donne sa ligne, ce
# sont des plans — les flancs obliques, la face de bridage ronde, le fond ajoure.
BR_W         = 22.00   # largeur hors-tout, au droit des vis
BR_L         = 32.00   # longueur hors-tout, symetrique en Y autour de l'origine
BR_BORE_D    = 15.10   # berceau : 0,05 mm de jeu au rayon
BR_FLANGE_T  = 2.50    # platine avant — PLAFONNEE par la roue, voir README

# Le berceau ne prend le moteur que sur le TIERS de son diametre : 5,00 mm de
# profondeur au lieu des 7,55 d'un demi-rond. Le moteur y repose, il n'y est pas
# enferme — c'est la platine qui le tient. Les joues descendent d'autant, la piece
# avec elles.
CRADLE_DEPTH = MOT_D / 3

# La face de bridage epouse le reducteur : un disque, pas une plaque. Ø17 et non
# Ø15 pour garder 1 mm de matiere autour des fraisures, qui debordent a 7,5 mm.
FLANGE_R     = 8.50

# Flancs obliques : la piece n'est a sa pleine largeur qu'au droit des vis, et se
# pince a chaque bout. L'angle n'est PAS un reglage libre : il est celui qui amene
# le flanc exactement sur le diametre du disque de bridage. Un flanc plus doux
# laissait une banquette decouverte de chaque cote du disque ; un flanc plus raide
# mordrait dedans.
TAPER_LEN    = 5.00    # longueur sur laquelle le flanc se pince, a chaque bout

BR_X_THREAD  = 9.00    # ecart a l'axe
BR_Y_HOLE    = 9.00    # ecart au centre, en Y
BR_TAP_D     = 1.60    # avant-trou M2, traversant
BR_ENGAGE_LO = 4.00    # engagement max par le dessous
BR_ENGAGE_HI = 3.00    # engagement max par le dessus
PCB_DRILL    = 2.20    # M2 avec jeu, percage de la carte et des entretoises
CS_D         = 4.00    # fraisure 90 deg des vis de la platine
BR_RELIEF_X  = 5.00    # fenetre d'allegement sous le berceau
BR_RELIEF_Y  = 6.00

# --- entretoises : des chutes de la carte mere, empilees sous l'equerre
SHIM_T       = PCB_T   # une entretoise = une epaisseur de carte
SHIM_N       = 3       # 3 x 1,6 = 4,80 mm : voir le calcul de BR_FLOOR

# Le fond du berceau est le plus mince possible : c'est l'empilage d'entretoises
# qui fait la hauteur. BR_FLOOR est ce qui reste une fois la garde au sol visee
# atteinte — et non l'inverse. Les taraudages ne le traversent pas, ils sont dans
# les joues.
BR_FLOOR = (WHEEL_D / 2 - PCB_T - CLEARANCE) - SHIM_N * SHIM_T - BR_BORE_D / 2
assert BR_FLOOR >= 2.00, f"fond de berceau trop mince ({BR_FLOOR:.2f}) : baisser SHIM_N"

AXIS_Z       = SHIM_N * SHIM_T + BR_FLOOR + BR_BORE_D / 2   # 14,90
BR_Z0        = SHIM_N * SHIM_T                              # dessous de l'equerre
BR_WALL_TOP  = AXIS_Z - BR_BORE_D / 2 + CRADLE_DEPTH        # haut des joues
BR_TOP       = AXIS_Z + FLANGE_R                            # haut du disque

# Ce que le berceau laisse de matiere en haut de joue, et ce qu'il faut pour y
# loger un M2 sans percer ni le berceau ni le flanc.
import math as _m
_bore_at_top = _m.sqrt((BR_BORE_D / 2) ** 2 - (AXIS_Z - BR_WALL_TOP) ** 2)
assert BR_X_THREAD - BR_TAP_D / 2 - _bore_at_top >= 1.0, "taraudage trop pres du berceau"
assert BR_W / 2 - BR_X_THREAD - BR_TAP_D / 2 >= 1.0, "taraudage trop pres du flanc"
assert FLANGE_R >= GEAR_M2_PCD / 2 + CS_D / 2 + 0.8, "disque trop petit pour les fraisures"
BR_W_END = FLANGE_R                          # le flanc meurt sur le disque
TAPER_ANGLE = _m.degrees(_m.atan2(BR_W / 2 - FLANGE_R, TAPER_LEN))
assert 5.0 < TAPER_ANGLE < 60.0, f"pincement des flancs aberrant ({TAPER_ANGLE:.1f} deg)"
CRADLE_WRAP = 2 * _m.degrees(_m.acos((AXIS_Z - BR_WALL_TOP) / (BR_BORE_D / 2)))

# ---------------------------------------------------------------- positions deduites
Y_FLANGE     = -BR_L / 2                 # -16.00, face avant de la platine
Y_FACE       = Y_FLANGE + BR_FLANGE_T    # -13.50, face de sortie du reducteur
Y_BACK       = BR_L / 2                  # +16.00, arriere de l'equerre
Y_GEAR_BACK  = Y_FACE + GEAR_L           #  +3.60
Y_MOT_BACK   = Y_FACE + ASSY_OFFSET + 1.0  # +28.40
Y_ENC_BACK   = Y_MOT_BACK + ENC_L        # +29.80
Y_SHAFT_TIP  = Y_FACE - SHAFT_TIP        # -27.70
Y_WHEEL_IN   = Y_FLANGE - WHEEL_GAP      # -16.50
Y_WHEEL_OUT  = Y_WHEEL_IN - WHEEL_W      # -27.50

# Porte-a-faux de la roue depuis la face du reducteur, ce qui decide de la charge
# radiale admissible sur les paliers frittes.
WHEEL_OVERHANG = BR_FLANGE_T + WHEEL_GAP + WHEEL_W / 2      # 8.50
RADIAL_ALLOWED = GEAR_RADIAL_MAX * GEAR_RADIAL_REF / WHEEL_OVERHANG

if __name__ == "__main__":
    print(f"entretoises              {SHIM_N} x {SHIM_T:.2f} = {BR_Z0:.2f} mm")
    print(f"fond du berceau          {BR_FLOOR:6.2f} mm")
    print(f"hauteur d'axe            {AXIS_Z:6.2f} mm / dessus de carte, "
          f"{AXIS_Z + PCB_T:.2f} / dessous")
    print(f"garde au sol             {WHEEL_D/2 - AXIS_Z - PCB_T:6.2f} mm")
    print(f"equerre                  Y {Y_FLANGE:7.2f} .. {Y_BACK:7.2f}  "
          f"Z {BR_Z0:5.2f} .. {BR_TOP:5.2f}")
    print(f"reducteur                Y {Y_FACE:7.2f} .. {Y_GEAR_BACK:7.2f}")
    print(f"moteur                   Y {Y_GEAR_BACK:7.2f} .. {Y_MOT_BACK:7.2f}")
    print(f"codeur                   Y {Y_MOT_BACK:7.2f} .. {Y_ENC_BACK:7.2f}")
    print(f"  depassement arriere    {Y_ENC_BACK - Y_BACK:6.2f} mm")
    print(f"roue                     Y {Y_WHEEL_OUT:7.2f} .. {Y_WHEEL_IN:7.2f}")
    print(f"bout d'arbre             Y {Y_SHAFT_TIP:7.2f}  (roue a {Y_WHEEL_OUT:.2f})")
    print(f"\nporte-a-faux de la roue  {WHEEL_OVERHANG:6.2f} mm depuis la face")
    print(f"charge radiale admise    {RADIAL_ALLOWED:6.2f} N  "
          f"({GEAR_RADIAL_MAX:.0f} N a {GEAR_RADIAL_REF:.1f} mm, paliers frittes)")
