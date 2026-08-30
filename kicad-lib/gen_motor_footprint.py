#!/usr/bin/env python3
"""Genere l'empreinte mecanique du GM12-N20 + support N20/N30.

Origine de l'empreinte = milieu des deux trous de fixation.
Axe moteur suivant Y ; arbre de sortie vers -Y.

Toutes les cotes sont modifiables ci-dessous. Apres une mesure au pied a
coulisse sur la piece reelle, corriger PITCH puis relancer :
    python3 gen_motor_footprint.py
"""
# ---- support : cotes datasheet Handson GA12-N20-Bracket, validees au pied a coulisse
PITCH      = 18.00     # entraxe des trous (datasheet Handson, confirme au pied a coulisse)
HOLE_D     = 2.20      # percage carte : M2 avec jeu (le modele donne 2.00 nominal)
BR_W       = 25.00     # largeur hors-tout du support (datasheet Handson)
BR_D       = 11.50     # profondeur du support (suivant l'axe moteur)
BR_FRONT   = 7.25      # axe des trous -> face avant (cote arbre) : 11.5 - 8.5/2
SHAFT_OFF  = 6.00      # face avant du support -> face de sortie d'axe (mesure)
# ---- moteur (plan cote Waveshare GM12-N20)
MOT_W      = 12.00     # largeur du corps
GEARBOX_L  = 9.03      # longueur du reducteur
BODY_L     = 22.07     # corps 10x12 restant + bloc encodeur (releve sur le STEP)
SHAFT_D    = 3.00
SHAFT_L    = 9.20      # releve sur le STEP Waveshare
CLEAR      = 0.25      # marge de courtyard

y_front = -BR_FRONT                    # face avant du support (cote arbre)
y_face  = y_front - SHAFT_OFF          # face de sortie d'axe du motoreducteur
y_gear  = y_face + GEARBOX_L           # fin du reducteur
y_back  = y_gear + BODY_L              # arriere du moteur + encodeur
y_shaft = y_face - SHAFT_L
br_back = y_front + BR_D

def line(x1,y1,x2,y2,layer,w):
    return (f'\t(fp_line (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f})\n'
            f'\t\t(stroke (width {w}) (type solid)) (layer "{layer}"))\n')
def rect(x1,y1,x2,y2,layer,w):
    return (f'\t(fp_rect (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f})\n'
            f'\t\t(stroke (width {w}) (type solid)) (fill no) (layer "{layer}"))\n')

s  = '(footprint "Motor_GM12-N20_Bracket"\n\t(version 20260206)\n\t(generator "pacabot-gen")\n'
s += '\t(generator_version "10.0")\n\t(layer "F.Cu")\n'
s += (f'\t(descr "GM12-N20 gearmotor on N20/N30 bracket, mechanical only. '
      f'2x M2 NPTH, {PITCH} mm pitch. Origin at hole midpoint, shaft toward -Y, '
      f'output face {SHAFT_OFF} mm ahead of bracket.")\n')
s += '\t(tags "motor n20 gm12 gearmotor bracket mechanical")\n'
s += '\t(attr through_hole exclude_from_pos_files exclude_from_bom allow_missing_courtyard)\n'
s += (f'\t(property "Reference" "M**" (at 0 {y_shaft-2:.3f} 0) (layer "F.SilkS")\n'
      '\t\t(effects (font (size 1 1) (thickness 0.15))))\n')
s += (f'\t(property "Value" "GM12-N20" (at 0 {y_back+2:.3f} 0) (layer "F.Fab")\n'
      '\t\t(effects (font (size 1 1) (thickness 0.15))))\n')
# trous de fixation M2
for i,x in enumerate((-PITCH/2, PITCH/2), 1):
    s += (f'\t(pad "" np_thru_hole circle (at {x:.3f} 0) (size {HOLE_D} {HOLE_D})\n'
          f'\t\t(drill {HOLE_D}) (layers "F&B.Cu" "*.Mask"))\n')
# F.Fab : support + moteur + arbre
s += rect(-BR_W/2, y_front, BR_W/2, br_back, "F.Fab", 0.1)
s += rect(-MOT_W/2, y_face, MOT_W/2, y_back, "F.Fab", 0.1)
s += line(-MOT_W/2, y_gear, MOT_W/2, y_gear, "F.Fab", 0.1)
s += rect(-SHAFT_D/2, y_shaft, SHAFT_D/2, y_face, "F.Fab", 0.1)
# F.SilkS : contour du support seul
s += rect(-BR_W/2, y_front, BR_W/2, br_back, "F.SilkS", 0.12)
# F.CrtYd : enveloppe totale
x_c = max(BR_W, MOT_W)/2 + CLEAR
s += rect(-x_c, y_shaft-CLEAR, x_c, y_back+CLEAR, "F.CrtYd", 0.05)
MODELS = ("GM12-N20_bracket",          # support ABS blanc
          "GM12-N20_motor_gearbox",    # reducteur + arbre, laiton
          "GM12-N20_motor_can",        # carter moteur, nickel
          "GM12-N20_motor_encoder",    # bloc encodeur, sombre
          "Pololu_wheel_40x7_hub",     # moyeu roue, blanc
          "Pololu_wheel_40x7_tire")    # gomme, noir
for mdl in MODELS:
    s += f'\t(model "${{KIPRJMOD}}/../kicad-lib/3d/{mdl}.step"\n'
    s += '\t\t(offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))\n'
s += ')\n'

open("Pacabot.pretty/Motor_GM12-N20_Bracket.kicad_mod","w").write(s)
print("ecrit : Pacabot.pretty/Motor_GM12-N20_Bracket.kicad_mod")
print(f"  entraxe {PITCH} mm, percages {HOLE_D} mm")
print(f"  emprise Y : {y_shaft:.2f} .. {y_back:.2f} mm  (total {y_back-y_shaft:.2f} mm)")
print(f"  emprise X : +/-{x_c:.2f} mm")
