#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere les deux empreintes de la turbine d'appui EDF 27 mm.

La carte porte la turbine par un percage unique de DIA_TROU (34 mm) et trois
vis M2 sur un cercle de BCD. Le meme jeu de percages sert aux DEUX montages,
c'est tout l'interet du 34 : on ne fige pas le sens au routage.

  Turbine_EDF27_dessus   (defaut)  -- turbine POSEE sur la face dessus.
      La levre dia 36,7 s'appuie sur l'anneau de carte qui reste autour du
      trou (1,35 mm de large) ; la turbine tient entierement au-dessus de la
      carte, LONGUEUR_HT au-dessus du cuivre. Les vis se montent PAR LE
      DESSOUS, tetes sous la carte, dans un collier imprime pose sur la levre.

  Turbine_EDF27_dessous            -- turbine ENCASTREE par le dessous.
      Le fut dia 29,7 traverse le trou de 34 ; le conge levre/fut vient
      coincer sur l'arete du percage, ce qui centre la turbine tout seul.
      Il ne reste que la levre sous la carte. Aspiration degagee (le bell
      mouth ne lit plus la carte a bout portant) et Z_HAUT gagne, mais la
      levre descend Z_BAS sous la carte, sous le bord de jupe : a verifier
      contre la garde au sol avant de choisir ce montage.

Les deux empreintes se posent COTE DESSUS (couche F.Cu) : la turbine traverse
le plan de carte dans les deux cas, il ne faut jamais les retourner. Passer
d'un montage a l'autre = changer l'empreinte dans les proprietes, la position
et la rotation ne bougent pas.

Repere de l'empreinte (fichier .kicad_mod, +Y vers le bas de l'ecran) :
  - origine = axe de rotation de la turbine ;
  - X CONFONDU AVEC L'ESSIEU : c'est la direction contrainte, les moteurs
    arrivent a +/-20,2 mm de l'axe une fois la voie a 155 ;
  - la vis isolee regarde -Y, soit le nez du robot (la carte est dessinee
    nez en haut, y 120 au nez) ; les deux autres partent vers la queue.

Cotes de la turbine recopiees de mechanics/turbineEDF27.py, qui reste la
source de verite (fiches AEO-RC POWER-X 27 mm, A RECALER AU PIED A COULISSE).

    python3 gen_turbine_footprint.py
"""
import math
import os

# ---- turbine (mechanics/turbineEDF27.py)
DIA_VEINE   = 27.4    # passage d'air
DIA_FUT     = 29.7    # exterieur du fut
DIA_LEVRE   = 36.7    # exterieur de la levre d'entree
LONGUEUR_HT = 25.80   # hors-tout, levre comprise
HAUT_LEVRE  = 3.00    # hauteur du bourrelet
CONGE_LEVRE = 1.20    # hauteur du conge fut -> levre
RAYON_BELL  = 3.50    # rayon du bell mouth : la portee plate commence a
                      # R_VEINE + RAYON_BELL = 17,20

# ---- percages de la carte
DIA_TROU    = 34.00   # passage d'air / passage de fut
D_VIS       = 2.20    # M2 avec jeu, PCB_DRILL du projet
BCD         = 42.50   # cercle des trois vis
ANGLES      = (-90.0, 30.0, 150.0)   # degres depuis +X ; -90 = vers le nez

# ---- pieces rapportees, indicatif
COLLIER_EP  = 2.50    # paroi du collier imprime autour de la levre
DIA_COLLIER = BCD + 2 * COLLIER_EP

# ---- degagement lateral disponible une fois la voie a 155 (memoire projet :
# arriere du codeur a 20,2 mm de l'axe, 1,8 mm de jeu sur la levre)
X_MOTEUR    = 20.20

W_SILK, W_FAB, W_DWG, W_EDGE, W_CRT = 0.12, 0.10, 0.10, 0.10, 0.05

R_VEINE  = DIA_VEINE / 2.0
R_FUT    = DIA_FUT / 2.0
R_LEVRE  = DIA_LEVRE / 2.0
R_TROU   = DIA_TROU / 2.0
R_VIS    = BCD / 2.0
R_GORGE  = R_VEINE + RAYON_BELL          # ouverture du bell mouth

# Enfoncement en montage encastre : le conge (R_FUT -> R_LEVRE sur CONGE_LEVRE
# de hauteur) coince sur l'arete du percage.
Z_CONGE  = LONGUEUR_HT - HAUT_LEVRE - CONGE_LEVRE
Z_ASSISE = Z_CONGE + CONGE_LEVRE * (R_TROU - R_FUT) / (R_LEVRE - R_FUT)

VIS = [(R_VIS * math.cos(math.radians(a)), R_VIS * math.sin(math.radians(a)))
       for a in ANGLES]


def circle(cx, cy, r, layer, w, style="solid"):
    return (f'\t(fp_circle (center {cx:.3f} {cy:.3f}) (end {cx + r:.3f} {cy:.3f})\n'
            f'\t\t(stroke (width {w}) (type {style})) (fill no) (layer "{layer}"))\n')


def line(x1, y1, x2, y2, layer, w, style="solid"):
    return (f'\t(fp_line (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f})\n'
            f'\t\t(stroke (width {w}) (type {style})) (layer "{layer}"))\n')


def text(t, x, y, layer, size=0.8, rot=0):
    mir = ' (justify mirror)' if layer.startswith("B.") else ''
    return (f'\t(fp_text user "{t}" (at {x:.3f} {y:.3f} {rot}) (layer "{layer}")\n'
            f'\t\t(effects (font (size {size} {size}) (thickness 0.15)){mir}))\n')


def npth(x, y, d):
    return (f'\t(pad "" np_thru_hole circle (at {x:.3f} {y:.3f}) '
            f'(size {d} {d})\n\t\t(drill {d}) (layers "F&B.Cu" "*.Mask"))\n')


def empreinte(encastre):
    """Retourne (nom, contenu) pour l'un des deux montages."""
    nom = "Turbine_EDF27_" + ("dessous" if encastre else "dessus")
    # cote soufflage / cote appui : ou vit la matiere une fois montee
    if encastre:
        z_haut, z_bas = Z_ASSISE, LONGUEUR_HT - Z_ASSISE
        # sous la carte : la levre et le collier ; dessus : le fut qui sort
        f_body, b_body = R_FUT, R_LEVRE
        pose = (f'Turbine ENCASTREE par le dessous : le fut dia {DIA_FUT} traverse '
                f'le percage, le conge de levre coince sur l arete et centre la '
                f'turbine. {z_haut:.2f} mm au-dessus de la carte, {z_bas:.2f} mm '
                f'dessous (verifier la garde au sol : la levre passe sous le bord '
                f'de jupe). Vis M2 par le dessus, collier sous la carte. '
                f'Etancher le jeu de {R_TROU - R_FUT:.2f} mm autour du fut, sinon '
                f'le plenum se court-circuite par le percage.')
        note = (f"encastree : {z_haut:.2f} dessus / {z_bas:.2f} sous la carte")
    else:
        z_haut, z_bas = LONGUEUR_HT, 0.0
        f_body, b_body = R_LEVRE, None
        pose = (f'Turbine POSEE sur la face dessus : la levre dia {DIA_LEVRE} '
                f'porte sur l anneau de carte de '
                f'{(DIA_LEVRE - DIA_TROU) / 2:.2f} mm laisse autour du percage '
                f'(la portee plate de la levre commence a r {R_GORGE:.2f}, le '
                f'percage s arrete a r {R_TROU:.2f} : le bell mouth n est pas '
                f'obstrue). {LONGUEUR_HT} mm au-dessus de la carte, rien dessous. '
                f'Vis M2 par le dessous, collier sur la levre.')
        note = f"posee : {LONGUEUR_HT} mm au-dessus de la carte"

    s = f'(footprint "{nom}"\n\t(version 20260206)\n'
    s += '\t(generator "pacabot-gen")\n\t(generator_version "10.0")\n'
    s += '\t(layer "F.Cu")\n'
    s += (f'\t(descr "Turbine EDF 27 mm AEO-RC POWER-X (veine {DIA_VEINE} / fut '
          f'{DIA_FUT} / levre {DIA_LEVRE}, long. {LONGUEUR_HT}, 8 a 11 g), appui '
          f'aerodynamique. Mecanique seule : les 3 fils vont a l ESC, pas a la '
          f'carte. Percage d air dia {DIA_TROU} sur Edge.Cuts + 3 NPTH M2 dia '
          f'{D_VIS} a {BCD} de BCD. {pose} A POSER X SUR L ESSIEU : la vis isolee '
          f'regarde le nez, les deux autres passent a {abs(VIS[1][0]):.2f} mm de '
          f'l axe, pour {X_MOTEUR} disponibles. NE PAS RETOURNER l empreinte : '
          f'les deux montages se posent cote dessus.")\n')
    s += ('\t(tags "turbine edf 27 ventilateur appui aerodynamique plenum '
          'mecanique edge-cuts")\n')
    s += ('\t(attr through_hole exclude_from_pos_files exclude_from_bom '
          'allow_missing_courtyard)\n')
    s += (f'\t(property "Reference" "M**" (at 0 {-R_VIS - 4.8:.3f} 0) '
          '(layer "F.SilkS")\n\t\t(effects (font (size 1 1) (thickness 0.15))))\n')
    s += (f'\t(property "Value" "{nom}" (at 0 {R_VIS + 4.8:.3f} 0) '
          '(layer "F.Fab")\n\t\t(effects (font (size 1 1) (thickness 0.15))))\n')

    # ---- percages
    for x, y in VIS:
        s += npth(x, y, D_VIS)

    # ---- Edge.Cuts : le passage d'air, unique et commun aux deux montages
    s += circle(0, 0, R_TROU, "Edge.Cuts", W_EDGE)

    # ---- F.Fab : ce que la turbine occupe, vu de dessus
    s += circle(0, 0, R_LEVRE, "F.Fab", W_FAB)            # levre
    s += circle(0, 0, R_FUT, "F.Fab", W_FAB)              # fut
    s += circle(0, 0, R_GORGE, "F.Fab", W_FAB, "dash")    # ouverture bell mouth
    for x, y in VIS:
        s += circle(x, y, D_VIS / 2, "F.Fab", W_FAB)
    s += text(note, 0, R_LEVRE + 2.4, "F.Fab", 0.7)

    # ---- serigraphie. Tout ce qui tombe dans le percage disparait a la
    # fraise : cote dessus on ne trace jamais en deca de R_TROU.
    r_silk = max(f_body, R_TROU) + 0.40
    s += circle(0, 0, r_silk, "F.SilkS", W_SILK)
    for x, y in VIS:
        s += circle(x, y, D_VIS / 2 + 0.7, "F.SilkS", W_SILK)
    if b_body is not None:
        s += circle(0, 0, b_body + 0.40, "B.SilkS", W_SILK)

    # ---- Dwgs.User : le collier imprime (a dessiner), la sortie des 3 fils
    # et la limite laterale que posent les moteurs.
    s += circle(0, 0, R_VIS + COLLIER_EP, "Dwgs.User", W_DWG, "dash")
    s += line(R_FUT, 0, R_FUT + 8.0, 0, "Dwgs.User", W_DWG, "dash")
    s += text("3 fils -> ESC", R_FUT + 4.2, -1.2, "Dwgs.User", 0.7)
    for signe in (-1, 1):
        s += line(signe * X_MOTEUR, -12.0, signe * X_MOTEUR, 12.0,
                  "Dwgs.User", W_DWG, "dash")
    s += text(f"arriere moteur voie 155 : +/-{X_MOTEUR}", -X_MOTEUR - 1.1, 0,
              "Dwgs.User", 0.7, 90)
    s += text(f"collier imprime dia {DIA_COLLIER:.0f} indicatif",
              0, R_VIS + 7.0, "Dwgs.User", 0.7)

    # ---- courtyard : l'encombrement propre de la turbine, cote par cote.
    # Le collier n'y est pas : c'est une piece a dessiner, son diametre
    # indicatif vit sur Dwgs.User.
    s += circle(0, 0, max(f_body, R_TROU) + 0.25, "F.CrtYd", W_CRT)
    if b_body is not None:
        s += circle(0, 0, b_body + 0.25, "B.CrtYd", W_CRT)

    # ---- modele 3D : le STEP est bati aspiration en +Z, il se retourne pour
    # aspirer vers la carte, puis descend a son assise.
    z_offset = Z_ASSISE if encastre else LONGUEUR_HT
    s += (f'\t(model "${{KIPRJMOD}}/kicad-lib/3d/Turbine_EDF27.step"\n'
          f'\t\t(offset (xyz 0 0 {z_offset:.3f})) (scale (xyz 1 1 1)) '
          f'(rotate (xyz 180 0 0)))\n')
    s += ')\n'
    return nom, s


ICI = os.path.dirname(os.path.abspath(__file__))
for encastre in (False, True):
    nom, contenu = empreinte(encastre)
    with open(os.path.join(ICI, "Pacabot.pretty", nom + ".kicad_mod"), "w") as f:
        f.write(contenu)
    print(f"{nom}.kicad_mod ecrit")

print(f"percage d air        dia {DIA_TROU} : gorge du bell mouth a r "
      f"{R_GORGE:.2f}, marge {R_GORGE - R_TROU:.2f} mm")
print(f"                     anneau d appui de la levre "
      f"{(DIA_LEVRE - DIA_TROU) / 2:.2f} mm, jeu au fut {R_TROU - R_FUT:.2f} mm")
print(f"3 vis M2 dia {D_VIS} a {BCD} de BCD, angles {ANGLES}")
for i, (x, y) in enumerate(VIS, 1):
    print(f"  vis {i} : ({x:+.3f}, {y:+.3f})")
print(f"                     matiere trou-vis {R_VIS - D_VIS / 2 - R_LEVRE:.2f} mm, "
      f"debord lateral {abs(VIS[1][0]) + D_VIS / 2:.2f} pour {X_MOTEUR} dispo")
print(f"montage dessus       {LONGUEUR_HT:.2f} mm au-dessus de la carte, "
      f"rien dessous")
print(f"montage dessous      assise du conge a z {Z_ASSISE:.3f} : "
      f"{Z_ASSISE:.2f} dessus / {LONGUEUR_HT - Z_ASSISE:.2f} sous la carte")
