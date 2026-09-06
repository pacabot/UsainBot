# -*- coding: utf-8 -*-
"""Modeles 3D des boitiers que KiCad 10 ne livre pas.

Plusieurs empreintes des bibliotheques KiCad *declarent* un modele qui
n'existe pas dans `3dmodels/` : l'USB-C HRO, le Micro-MaTch TE, les selfs
Taiyo-Yuden NR, l'interrupteur MSK12C02, les connecteurs AMASS autres que
XT60. En 3D la carte se retrouve alors trouee la ou vivent justement les
pieces les plus hautes, et le controle d'encombrement (turbine, equerres
moteur, pack a l'arriere) ne veut plus rien dire.

Ce script produit des modeles d'ENCOMBREMENT : les cotes hors-tout et les
volumes qui comptent pour les collisions, pas le detail du contact. Ils
suffisent a ce qu'on leur demande - voir si quelque chose se touche - et
ils portent leurs couleurs, injectees apres coup par `step_colors.py`
(FreeCAD en console ne sait pas les ecrire).

Repere = repere 3D de KiCad : X comme dans le .kicad_mod, **Y inverse**
(le Y du fichier d'empreinte descend, celui du modele monte), Z = 0 sur le
dessus de la carte, +Z vers le haut. Les cotes viennent du F.Fab de
l'empreinte correspondante (donc du plan du fabricant) et de la fiche du
composant ; celles qui n'y sont pas sont marquees A RECALER.

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd gen_3d_models.py
"""

import os
import sys

import FreeCAD as App
import Import
import Part
from FreeCAD import Vector

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
from step_colors import injecter_couleurs_step

SORTIE = os.path.join(ICI, '3d')

# ---------------------------------------------------------------- palette
LAITON = (0.83, 0.68, 0.21)
ROUGE_TE = (0.72, 0.10, 0.11)     # PBT rouge du Micro-MaTch (plan TE 215079)
VERT_PCB = (0.06, 0.32, 0.18)
CUIVRE = (0.85, 0.55, 0.30)
ACIER = (0.72, 0.73, 0.75)
NOIR = (0.13, 0.13, 0.14)
BLANC = (0.90, 0.90, 0.88)
JAUNE = (0.95, 0.78, 0.10)
ROUGE = (0.75, 0.12, 0.12)
FERRITE = (0.28, 0.27, 0.26)

_BILAN = []


def dire(msg):
    _BILAN.append(msg)
    print(msg)


def boite(lx, ly, lz, cx=0.0, cy=0.0, z0=0.0):
    """Pave centre en (cx, cy), pose a la cote z0."""
    return Part.makeBox(lx, ly, lz, Vector(cx - lx / 2.0, cy - ly / 2.0, z0))


def cyl(d, h, x=0.0, y=0.0, z0=0.0):
    return Part.makeCylinder(d / 2.0, h, Vector(x, y, z0))


# =========================================================================
#  Les boitiers
# =========================================================================
def xt30u_m():
    """AMASS XT30U-M vertical : embase male du pack, 30 A.

    F.Fab de l'empreinte : x -2,6 a 7,6 / y -2,6 a 2,6, broches en (0,0) et
    (5,0), forets 2,7. Hauteur hors-tout 12 mm relevee sur la fiche TME,
    dont 3,2 mm de fut sous la carte. A RECALER sur la piece.
    """
    corps = boite(10.2, 5.2, 9.0, cx=2.5, z0=0.0)
    for x in (0.0, 5.0):                      # les deux logements de contact
        corps = corps.cut(cyl(4.4, 5.2, x, 0.0, 3.8))
    chanfrein = boite(10.2, 5.2, 1.0, cx=2.5, z0=8.0)
    corps = corps.cut(chanfrein.cut(boite(9.0, 4.0, 1.0, cx=2.5, z0=8.0)))
    broches = [cyl(2.5, 4.6, x, 0.0, -3.2) for x in (0.0, 5.0)]
    return [('Corps', corps, JAUNE), ('Broches', broches[0].fuse(broches[1]), LAITON)]


def micro_match():
    """TE Micro-MaTch 215079-6, femelle sur carte, 6 voies.

    Cotes du plan client TE C-215079 rev Y2 (telecharge le 4 septembre 2026) :
    longueur hors-tout "A" MAX = **9,7** pour 6 positions, largeur **5,2 MAX**,
    hauteur au-dessus de la carte **4,0 ± 0,2** — et le boitier est **ROUGE**
    (G.F. polyester PBT ; contacts bronze phosphoreux etames sur nickel).
    Le premier modele reprenait la boite englobante du F.Fab de KiCad, plus
    large et plus haute d'un bon millimetre, et en noir : rien a voir avec la
    piece. Pas de 1,27 en quinconce, entraxe de rangees 2,54, detrompeur
    dia 1,5 en (1,8 ; -1,4) dans le repere de l'empreinte.
    """
    LONG, LARG, HAUT = 9.70, 5.20, 4.00
    pads = [(0, 0), (2.54, -1.27), (0, -2.54), (2.54, -3.81), (0, -5.08),
            (2.54, -6.35)]                    # deja dans le repere 3D
    cx = (0 + 2.54) / 2.0                     # milieu des deux rangees
    cy = (0 + -6.35) / 2.0                    # milieu des six contacts
    corps = boite(LARG, LONG, HAUT, cx=cx, cy=cy, z0=0.0)
    # fenetre d accouplement : la nappe descend dans cette gorge
    corps = corps.cut(boite(3.00, LONG - 2.4, 1.30, cx=cx, cy=cy, z0=HAUT - 1.3))
    # les six contacts femelles, visibles au fond de la gorge
    lames = None
    for x, y in pads:
        lame = boite(0.60, 1.20, 1.10, cx=x, cy=y, z0=HAUT - 1.25)
        lames = lame if lames is None else lames.fuse(lame)
    # queues a souder : 0,25 x 0,5 au plan, sous la carte
    queues = None
    for x, y in pads:
        q = boite(0.50, 0.25, 4.60, cx=x, cy=y, z0=-3.0)
        queues = q if queues is None else queues.fuse(q)
    queues = queues.fuse(cyl(1.40, 3.00, 1.80, 1.40, -1.7))   # detrompeur
    return [('Corps', corps, ROUGE_TE), ('Contacts', lames, ACIER),
            ('Queues', queues, LAITON)]


def oled_entretoises():
    """Les quatre entretoises M2 x 6 qui portent le module OLED.

    Le module vit 6 mm au-dessus de la carte (le LQFP-100 passe dessous) :
    sans les entretoises, la vue 3D montre un ecran en levitation et on ne
    voit pas ce qui reste habitable en dessous. Percages a (+/-11,5 ; +/-10,35)
    - carte du module 27,0 x 24,7 mesuree, cf. tools/gen_fp.py.
    """
    HX, HY, H = 11.50, 10.35, 6.00
    EP_MODULE = 1.20
    futs, tetes = None, None
    for sx in (-1, 1):
        for sy in (-1, 1):
            f = cyl(4.0, H, sx * HX, sy * HY, 0.0)
            f = f.cut(cyl(1.7, H + 1, sx * HX, sy * HY, -0.5))
            futs = f if futs is None else futs.fuse(f)
            # vis M2 traversant le module par le dessus
            t = cyl(3.8, 1.20, sx * HX, sy * HY, H + EP_MODULE)
            t = t.fuse(cyl(1.9, EP_MODULE + 0.2, sx * HX, sy * HY, H))
            tetes = t if tetes is None else tetes.fuse(t)
    return [('Entretoises', futs, LAITON), ('Vis', tetes, ACIER)]


def esc_multistar_10a():
    """Turnigy MultiStar 10A BLHeli-S Rev16 V3 (Opto), DEBOUT sur sa base.

    Carte 22 x 12 mm, 5,1 g, 10 A continu / 15 A crete, 2-4S, sans BEC
    (HobbyKing). Il est fixe **sur la tranche cote entree de puissance** :
    ses deux fils d alimentation descendent dans les percages de l empreinte
    et le tiennent debout, les trois fils moteur sortent en haut. L emprise
    au sol tombe alors a 12 x 5 mm pour 22 mm de haut - dix fois moins de
    carte qu a plat, et la turbine est a 30 mm.
    """
    LARG, EP, HAUT = 12.0, 5.0, 22.0
    gaine = boite(LARG, EP, HAUT - 2.0, z0=1.0)
    carte = boite(LARG - 0.6, 1.6, HAUT, z0=0.0)
    fils = None
    for x in (-2.54, 2.54):                          # alimentation, vers le bas
        f = cyl(1.8, 4.0, x, 0.0, -1.7)
        fils = f if fils is None else fils.fuse(f)
    moteur = None
    for x in (-3.6, 0.0, 3.6):                       # trois fils moteur, en haut
        m = cyl(1.6, 7.0, x, 0.0, HAUT - 0.5)
        moteur = m if moteur is None else moteur.fuse(m)
    signal = cyl(1.2, 6.0, 4.6, 0.0, 2.0)
    return [('Gaine', gaine, NOIR), ('Carte', carte, VERT_PCB),
            ('Fils_alim', fils, CUIVRE), ('Fils_moteur', moteur, BLANC),
            ('Fil_signal', signal, JAUNE)]


def usb_c_hro():
    """Embase USB-C HRO TYPE-C-31-M-12, 16 broches, bouche vers -Y (3D).

    F.Fab : 8,94 x 7,30 ; hauteur 3,26 mm (fiche HRO). La bouche s'ouvre du
    cote oppose aux pastilles de contact, c'est-a-dire vers le bord de carte.
    """
    blindage = boite(8.94, 7.30, 3.26)
    # la bouche : fente 6,8 x 1,7 creusee sur 4,5 mm depuis la face avant
    bouche = boite(6.80, 4.50, 1.70, cy=-7.30 / 2.0 + 2.25 - 0.001, z0=0.78)
    blindage = blindage.cut(bouche)
    langue = boite(6.30, 4.20, 0.70, cy=-7.30 / 2.0 + 2.10, z0=1.28)
    return [('Blindage', blindage, ACIER), ('Langue', langue, BLANC)]


def self_nr(cote, hauteur, nom):
    """Self blindee Taiyo-Yuden NR : noyau ferrite moule, cote x cote."""
    corps = boite(cote, cote, hauteur)
    corps = corps.makeFillet(0.4, [a for a in corps.Edges
                                   if abs(a.tangentAt(a.FirstParameter).z) > 0.9])
    return [(nom, corps, FERRITE)]


def msk12c02():
    """Interrupteur a glissiere SPDT Shouhan MSK12C02, sortie laterale.

    F.Fab : x -3,35 a 3,35 / y -1,40 a 2,85 (repere empreinte), corps
    1,4 mm. Le bouton depasse de 1,5 mm au-dessus : c'est lui qu'il faut
    laisser accessible au doigt, d'ou sa presence dans le modele.
    """
    cy = -(2.85 - 1.40) / 2.0
    corps = boite(6.70, 4.25, 1.40, cy=cy, z0=0.0)
    bouton = boite(1.60, 1.20, 1.50, cx=-0.75, cy=cy, z0=1.40)
    return [('Corps', corps, BLANC), ('Bouton', bouton, NOIR)]


def skrhabe010():
    """Alps SKRHABE010 : 4 directions + appui, 7,35 x 7,50 x 1,80."""
    capot = boite(7.35, 7.50, 1.20)
    bascule = cyl(4.40, 0.60, 0.0, 0.0, 1.20)
    return [('Capot', capot, ACIER), ('Bascule', bascule, NOIR)]


PIECES = [
    ('AMASS_XT30U-M_1x02_P5.0mm_Vertical', xt30u_m),
    ('TE_Micro-MaTch_215079-6_2x03_P1.27mm_Vertical', micro_match),
    ('USB_C_Receptacle_HRO_TYPE-C-31-M-12', usb_c_hro),
    ('L_Taiyo-Yuden_NR-30xx', lambda: self_nr(3.0, 1.50, 'Self')),
    ('L_Taiyo-Yuden_NR-40xx', lambda: self_nr(4.0, 3.00, 'Self')),
    ('SW_SPDT_Shouhan_MSK12C02', msk12c02),
    ('SKRHABE010', skrhabe010),
    ('OLED_Standoffs_M2x6', oled_entretoises),
    ('ESC_Multistar_10A', esc_multistar_10a),
]


def main():
    os.makedirs(SORTIE, exist_ok=True)
    doc = App.newDocument('boitiers')
    for nom, fabrique in PIECES:
        objets, couleurs = [], {}
        for label, forme, rgb in fabrique():
            if not forme.isValid():
                forme = forme.removeSplitter()
            o = doc.addObject('Part::Feature', label)
            o.Shape = forme
            o.Label = label
            objets.append(o)
            couleurs[label] = rgb
        doc.recompute()
        chemin = os.path.join(SORTIE, nom + '.step')
        Import.export(objets, chemin)
        n = injecter_couleurs_step(chemin, couleurs)
        bb = objets[0].Shape.BoundBox
        for o in objets[1:]:
            bb.add(o.Shape.BoundBox)
        dire('%-46s z %6.2f a %5.2f   %d solide(s), %s couleurs'
             % (nom + '.step', bb.ZMin, bb.ZMax, len(objets), n))
        for o in objets:
            doc.removeObject(o.Name)
    App.closeDocument(doc.Name)
    dire('%d modeles ecrits dans %s' % (len(PIECES), SORTIE))


main()
