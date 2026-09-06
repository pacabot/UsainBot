#!/usr/bin/env python3
"""Genere l'empreinte du duo de telemetrie couche : OPV302 + BPV10NF.

Une seule empreinte porte le couple emetteur/recepteur, les deux diodes
COUCHEES a l'horizontale (pattes cintrees a 90 deg) pour viser le mur ou
l'obstacle, plus les percages du support pare-soleil imprime
(`mechanics/telemetry_duo.py`) qui se visse PAR LE DESSOUS de la carte.

Repere de l'empreinte (fichier .kicad_mod, +Y vers le bas de l'ecran) :
  - origine = axe de la vis M2 du support ;
  - VISEE OPTIQUE vers +X (l'azimut se regle par la rotation au placement,
    comme les trois stations deja posees a -15/-45/-75 deg) ;
  - axes optiques a Z_AXE au-dessus du dessus de carte, entraxe 10 mm ;
  - TX (OPV302, TO-46) en Y = -5 ; RX (BPV10NF, T-1 3/4) en Y = +5.

Numerotation des pads, meme convention que Device:LED / Device:D_Photo
(broche 1 = cathode) : 1 = TX K, 2 = TX A, 3 = RX K, 4 = RX A.
La broche 3 (NC) du TO-46 se coupe au ras du boitier avant montage.
Les deux boitiers sont ronds dans des alesages ronds : orienter les pattes
au cintrage pour tomber sur A/K du silk (TO-46 : pattes 1 et 2 a +/-45 deg
du plan horizontal, patte 3 vers le bas).

Le modele 3D (`mechanics/telemetry_duo.py`) est construit directement dans
le repere 3D de KiCad (Y inverse par rapport au fichier d'empreinte) :
contrairement aux generateurs moteurs, AUCUN miroir a l'export.

Cotes boitiers : datasheets TT Electronics OPV302 Rev C et Vishay BPV10NF
Rev 2.3 - a recaler au pied a coulisse sur les pieces recues.
    python3 gen_telemetry_footprint.py
"""
import math

# ---- implantation
ENTRAXE   = 10.00   # entraxe TX/RX (les cercles de l'ancienne Telemetry_Duo)
Z_AXE     = 6.00    # hauteur des axes optiques au-dessus du PCB (info)
X_ARRIERE = -5.00   # face arriere du support (sortie des pattes)
X_AVANT   = 8.00    # face avant du pare-soleil : a placer au bord de carte.
                    # Raccourci de 2 mm le 4 septembre (tube RX 6,1 -> 4,1,
                    # soit +/-11,5 deg vus de la puce au lieu de +/-9,5, mais
                    # recouvrement TX/RX des 49 mm au lieu de 61).
DEMI_LARG = 9.00    # demi-largeur du support
X_PADS    = -7.50   # ligne des 4 pads, derriere la face arriere

# ---- percages du support (visse par le dessous)
D_VIS     = 2.20    # M2 avec jeu, au centre (comme l'ancienne empreinte)
D_PION    = 1.60    # 2 pions anti-rotation du support, pion imprime 1,45
PION_A    = (-3.50, 0.00)   # sur l'axe : anti-rotation
PION_B    = (3.50, 1.50)    # decale vers RX : detrompeur (interdit le 180)

# ---- TX : OPV302, TO-46, pattes sur cercle 2,54 a 90 deg
TY        = -ENTRAXE / 2
TO46_R    = 2.54 / 2                  # rayon du cercle de pattes
TX_DY     = TO46_R * math.sin(math.radians(45))   # 0,898 : pattes a +/-45
TX_PERC   = 0.80    # patte 0,41-0,48
TX_PAD    = 1.50
# ---- RX : BPV10NF, T-1 3/4, pattes au pas 2,54 dans le plan diametral
RY        = ENTRAXE / 2
RX_DY     = 2.54 / 2
RX_PERC   = 1.00    # patte carree 0,63 (diagonale 0,89)
RX_PAD    = 1.70

W_SILK, W_FAB, W_DWG = 0.12, 0.10, 0.10


def line(x1, y1, x2, y2, layer, w, style="solid"):
    return (f'\t(fp_line (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f})\n'
            f'\t\t(stroke (width {w}) (type {style})) (layer "{layer}"))\n')


def rect(x1, y1, x2, y2, layer, w):
    return (f'\t(fp_rect (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f})\n'
            f'\t\t(stroke (width {w}) (type solid)) (fill no) (layer "{layer}"))\n')


def circle(cx, cy, r, layer, w):
    return (f'\t(fp_circle (center {cx:.3f} {cy:.3f}) (end {cx + r:.3f} {cy:.3f})\n'
            f'\t\t(stroke (width {w}) (type solid)) (fill none) (layer "{layer}"))\n')


def text(t, x, y, layer, size=0.8):
    return (f'\t(fp_text user "{t}" (at {x:.3f} {y:.3f}) (layer "{layer}")\n'
            f'\t\t(effects (font (size {size} {size}) (thickness 0.15))))\n')


def pad(num, shape, x, y, size, drill):
    extra = ' (roundrect_rratio 0.25)' if shape == 'roundrect' else ''
    return (f'\t(pad "{num}" thru_hole {shape} (at {x:.3f} {y:.3f}) '
            f'(size {size} {size})\n\t\t(drill {drill}) '
            f'(layers "*.Cu" "*.Mask"){extra})\n')


def npth(x, y, d):
    return (f'\t(pad "" np_thru_hole circle (at {x:.3f} {y:.3f}) '
            f'(size {d} {d})\n\t\t(drill {d}) (layers "F&B.Cu" "*.Mask"))\n')


def poly(pts, layer, w):
    corps = ' '.join(f'(xy {x:.3f} {y:.3f})' for x, y in pts)
    return (f'\t(fp_poly\n\t\t(pts {corps})\n'
            f'\t\t(stroke (width {w}) (type solid)) (fill no) '
            f'(layer "{layer}"))\n')


s = '(footprint "Telemetry_Duo_Coude"\n\t(version 20260206)\n'
s += '\t(generator "pacabot-gen")\n\t(generator_version "10.0")\n\t(layer "F.Cu")\n'
s += ('\t(descr "Station de telemetrie couchee : OPV302 (VCSEL 850 nm, TO-46) '
      f'+ BPV10NF (photodiode T-1 3/4), pattes cintrees a 90 deg, axes optiques '
      f'horizontaux a {Z_AXE} mm au-dessus de la carte, visee +X, entraxe {ENTRAXE} mm. '
      'Pads 1=TX K, 2=TX A, 3=RX K, 4=RX A (convention Device:LED / D_Photo) ; '
      'couper la broche 3 (NC) du TO-46. Percages du support pare-soleil '
      'mechanics/telemetry_duo.py : M2 central (visse par le dessous) + 2 pions '
      f'dia {D_PION} dont un decale (detrompeur). Face avant du pare-soleil a '
      f'X=+{X_AVANT} : a placer au bord de carte ou en surplomb. Courtyard '
      'reduit a la colonne de pads derriere la face arriere du socle.")\n')
s += '\t(tags "telemetry laser vcsel photodiode pare-soleil couche")\n'
s += '\t(attr through_hole exclude_from_pos_files)\n'
s += ('\t(property "Reference" "REF**" (at 0 -10.5 0) (layer "F.SilkS")\n'
      '\t\t(effects (font (size 0.8 0.8) (thickness 0.15))))\n')
s += ('\t(property "Value" "Telemetry_Duo_Coude" (at 0 10.5 0) (layer "F.Fab")\n'
      '\t\t(effects (font (size 0.8 0.8) (thickness 0.15))))\n')

# pads : cathodes en roundrect (reperage), anodes en rond
s += pad(1, 'roundrect', X_PADS, TY - TX_DY, TX_PAD, TX_PERC)   # TX K
s += pad(2, 'circle',    X_PADS, TY + TX_DY, TX_PAD, TX_PERC)   # TX A
s += pad(3, 'roundrect', X_PADS, RY + RX_DY, RX_PAD, RX_PERC)   # RX K
s += pad(4, 'circle',    X_PADS, RY - RX_DY, RX_PAD, RX_PERC)   # RX A
# percages du support
s += npth(0, 0, D_VIS)
s += npth(*PION_A, D_PION)
s += npth(*PION_B, D_PION)

# F.SilkS : contour du support, fleche de visee, reperes
s += rect(X_ARRIERE, -DEMI_LARG - 0.15, X_AVANT, DEMI_LARG + 0.15, "F.SilkS", W_SILK)
s += line(X_AVANT + 0.3, -0.8, X_AVANT + 1.1, 0, "F.SilkS", W_SILK)
s += line(X_AVANT + 1.1, 0, X_AVANT + 0.3, 0.8, "F.SilkS", W_SILK)
s += text("TX", X_PADS, TY - 2.6, "F.SilkS")
s += text("RX", X_PADS, RY + 2.7, "F.SilkS")
s += text("K", X_PADS - 1.6, TY - TX_DY, "F.SilkS", 0.6)
s += text("A", X_PADS - 1.6, TY + TX_DY, "F.SilkS", 0.6)
s += text("K", X_PADS - 1.6, RY + RX_DY, "F.SilkS", 0.6)
s += text("A", X_PADS - 1.6, RY - RX_DY, "F.SilkS", 0.6)

# F.Fab : support, les deux tubes, axes des diodes
s += rect(X_ARRIERE, -DEMI_LARG, X_AVANT, DEMI_LARG, "F.Fab", W_FAB)
for y in (TY, RY):
    s += rect(X_ARRIERE, y - 4.0, X_AVANT, y + 4.0, "F.Fab", W_FAB)
    s += line(X_ARRIERE - 0.5, y, X_AVANT + 0.5, y, "F.Fab", W_FAB)
s += circle(0, TY, 4.72 / 2, "F.Fab", W_FAB)    # capot TO-46 (couche)
s += circle(0, RY, 5.00 / 2, "F.Fab", W_FAB)    # corps T-1 3/4 (couche)

# Dwgs.User : les deux axes optiques, en tirets, vers la cible
for y in (TY, RY):
    s += line(X_AVANT, y, X_AVANT + 20.0, y, "Dwgs.User", W_DWG, "dash")

# Courtyard en deux largeurs. Le rectangle unique d'avant reservait les
# 18,5 mm de large du socle SUR TOUTE la longueur, y compris derriere la face
# arriere ou il n'y a que la rangee de pads : impossible d'approcher quoi que
# ce soit des pattes des diodes sans faire hurler la regle de recouvrement
# des courtyards, alors que rien n'occupe ce volume-la. La partie arriere se
# borne desormais a la colonne de pads.
cy_x1 = X_PADS - max(TX_PAD, RX_PAD) / 2 - 0.25
cy_y_bas = TY - TX_DY - TX_PAD / 2 - 0.25         # pad TX le plus bas
cy_y_haut = RY + RX_DY + RX_PAD / 2 + 0.25        # pad RX le plus haut
x_large = X_ARRIERE - 0.25
s += poly([(cy_x1, cy_y_bas), (x_large, cy_y_bas),
           (x_large, -DEMI_LARG - 0.25), (X_AVANT + 0.25, -DEMI_LARG - 0.25),
           (X_AVANT + 0.25, DEMI_LARG + 0.25), (x_large, DEMI_LARG + 0.25),
           (x_large, cy_y_haut), (cy_x1, cy_y_haut)], "F.CrtYd", 0.05)

# modeles 3D (repere 3D natif : offset et rotation a zero)
for m in ("Telemetry_Support", "Telemetry_Duo_Diodes"):
    s += (f'\t(model "${{KIPRJMOD}}/kicad-lib/3d/{m}.step"\n'
          '\t\t(offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))\n')
s += ')\n'

with open("Pacabot.pretty/Telemetry_Duo_Coude.kicad_mod", "w") as f:
    f.write(s)

print("Telemetry_Duo_Coude.kicad_mod ecrit")
print(f"pads TX (perc. {TX_PERC}) : 1=K y={TY - TX_DY:.3f}  2=A y={TY + TX_DY:.3f}")
print(f"pads RX (perc. {RX_PERC}) : 3=K y={RY + RX_DY:.3f}  4=A y={RY - RX_DY:.3f}")
print(f"NPTH : M2 {D_VIS} en (0,0), pions {D_PION} en {PION_A} et {PION_B}")
print(f"courtyard : socle X {x_large:.2f} a {X_AVANT + 0.25:.2f} sur "
      f"Y +/-{DEMI_LARG + 0.25:.2f} ; arriere X {cy_x1:.2f} a {x_large:.2f} "
      f"sur Y {cy_y_bas:.2f} a {cy_y_haut:.2f}")
