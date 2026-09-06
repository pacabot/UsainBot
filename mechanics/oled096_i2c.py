# -*- coding: utf-8 -*-
"""
Module 3D parametrique : ecran OLED 0,96" SSD1306 I2C 4 broches (generique).

Modele d'encombrement / integration construit en PartDesign : un corps par
composant (carte, verre, zone active, connecteur, broches, nappe), chacun
bati sur des esquisses editables dans l'interface.

Cotes de reference :
  - carte 27,0 x 24,7 mm, relevee au pied a coulisse sur l'exemplaire
    UsainBot (09/2026), variante raccourcie du module generique bleu.
  - ecran 0,96 pouce : zone active 21,74 x 10,86 mm (128 x 64, diagonale
    24,4 mm), donnee constructeur. Le verre modelise est la fenetre
    visible : zone active + bordure, PAS la dalle nue complete
    (26,70 x 19,26) dont le bas passe derriere la carte sur cette
    variante ; il reste ainsi degage des percages du bas.
A RECALER AU PIED A COULISSE sur la piece : DIA_TROU (2,0 / 2,2 / 3,0
selon les lots), MARGE_TROU_X/Y (donc les entraxes), VERRE_L/H et
Y_VERRE_HAUT si le centrage de la fenetre dans le chassis est critique.

Execution (voie recommandee - FreeCAD complet mais sans fenetre, pour que
les couleurs, transparences et visibilites soient posees nativement) :
    QT_QPA_PLATFORM=offscreen /Applications/FreeCAD.app/Contents/MacOS/FreeCAD \
        oled096_i2c.py
Le script peut aussi etre execute comme macro dans l'interface (le
document reste alors ouvert), ou via freecadcmd (mais ce mode n'a pas de
ViewObject : le .fcstd sort avec une apparence approximative).

Sorties (dans ce dossier) : .fcstd (couleurs, verre transparent, esquisses
et origines masquees), .stl, et .step avec une couleur par solide
(injectees en post-traitement : l'export STEP de FreeCAD les perd meme
avec l'interface offscreen).

Repere : origine au centre de la carte dans le plan de sa FACE ARRIERE
(plan d'appui sur entretoises), X le long du bord broches, +Y vers les
broches, +Z vers l'ecran.
"""

import math
import os
import re
import sys
import zipfile

import FreeCAD as App
import Part
import Import
import Mesh
from FreeCAD import Vector

# --------------------------------------------------------------------------
# Parametres (mm)
# --------------------------------------------------------------------------

LARGEUR        = 27.0    # MESURE - le long du bord broches
HAUTEUR        = 24.7    # MESURE - bord broches -> bord nappe
EP_PCB         = 1.2
CONGE_COIN     = 0.5

DIA_TROU       = 2.2     # A VERIFIER : 2,0 / 2,2 / 3,0 selon les lots
MARGE_TROU_X   = 2.0     # centre de trou -> bord lateral  -> entraxe X 23,0
MARGE_TROU_Y   = 2.0     # centre de trou -> bords haut/bas -> entraxe Y 20,7

NB_BROCHES     = 4       # GND VCC SCL SDA
PAS_BROCHES    = 2.54
Y_BROCHES      = 1.5     # axe de la rangee sous le bord haut
COTE_BROCHE    = 0.64
DEPASS_AVANT   = 0.8     # bout soude cote ecran
DEPASS_ARRIERE = 6.0     # queue de broche derriere le plastique
EP_PLASTIQUE   = 2.5     # corps isolant du connecteur, cote arriere
LARG_PLASTIQUE = 2.54

ZA_L           = 21.74   # zone active 128 x 64 (0,96 pouce de diagonale)
ZA_H           = 10.86
VERRE_L        = 25.0    # fenetre visible : zone active + bordure de verre
VERRE_H        = 14.0    # (degagee des percages du bas) - A RECALER
VERRE_EP       = 1.26
Y_VERRE_HAUT   = 4.3     # bord haut du verre sous le bord haut de la carte

NAPPE_L        = 13.0
NAPPE_EP       = 0.35
NAPPE_RETOUR   = 3.0     # remontee de la nappe sur la face arriere

ICI = os.path.dirname(os.path.abspath(__file__))
NOM = "OLED_0.96_SSD1306_I2C_128x64"

# Couleurs par solide (RGB 0..1), reprises de la photo du module
COULEURS = {
    "PCB":        (0.10, 0.22, 0.55),   # bleu carte
    "Verre":      (0.09, 0.09, 0.10),   # fenetre d'ecran
    "ZoneActive": (0.02, 0.02, 0.03),   # zone utile 128x64
    "Plastique":  (0.12, 0.12, 0.12),   # corps du connecteur
    "Broche1":    (0.83, 0.68, 0.21),   # or
    "Broche2":    (0.83, 0.68, 0.21),
    "Broche3":    (0.83, 0.68, 0.21),
    "Broche4":    (0.83, 0.68, 0.21),
    "Nappe":      (0.30, 0.23, 0.16),   # kapton sombre
}

# Transparence par solide (0 = opaque, 1 = invisible)
TRANSPARENCES = {
    "Verre": 0.35,
}

DEMI_L = LARGEUR / 2.0
DEMI_H = HAUTEUR / 2.0
Y_HAUT = DEMI_H            # bord broches
Y_BAS = -DEMI_H            # bord nappe


# --------------------------------------------------------------------------
# Aides esquisses (geometrie sans contraintes : le pilotage reste ici)
# --------------------------------------------------------------------------

def esquisse(corps, nom, z=0.0, rotation=None):
    sk = corps.newObject("Sketcher::SketchObject", nom)
    rot = rotation if rotation is not None else App.Rotation()
    sk.Placement = App.Placement(Vector(0, 0, z), rot)
    return sk


def ajouter_polygone(sk, points):
    """Contour ferme de segments dans le plan de l'esquisse."""
    n = len(points)
    for i in range(n):
        a, b = points[i], points[(i + 1) % n]
        sk.addGeometry(Part.LineSegment(Vector(a[0], a[1], 0),
                                        Vector(b[0], b[1], 0)), False)


def ajouter_rectangle_arrondi(sk, largeur, hauteur, r):
    l2, h2 = largeur / 2.0, hauteur / 2.0
    axe = Vector(0, 0, 1)
    sk.addGeometry(Part.LineSegment(Vector(l2, -h2 + r, 0),
                                    Vector(l2, h2 - r, 0)), False)
    sk.addGeometry(Part.ArcOfCircle(
        Part.Circle(Vector(l2 - r, h2 - r, 0), axe, r), 0, math.pi / 2), False)
    sk.addGeometry(Part.LineSegment(Vector(l2 - r, h2, 0),
                                    Vector(-l2 + r, h2, 0)), False)
    sk.addGeometry(Part.ArcOfCircle(
        Part.Circle(Vector(-l2 + r, h2 - r, 0), axe, r),
        math.pi / 2, math.pi), False)
    sk.addGeometry(Part.LineSegment(Vector(-l2, h2 - r, 0),
                                    Vector(-l2, -h2 + r, 0)), False)
    sk.addGeometry(Part.ArcOfCircle(
        Part.Circle(Vector(-l2 + r, -h2 + r, 0), axe, r),
        math.pi, 3 * math.pi / 2), False)
    sk.addGeometry(Part.LineSegment(Vector(-l2 + r, -h2, 0),
                                    Vector(l2 - r, -h2, 0)), False)
    sk.addGeometry(Part.ArcOfCircle(
        Part.Circle(Vector(l2 - r, -h2 + r, 0), axe, r),
        3 * math.pi / 2, 2 * math.pi), False)


def ajouter_rectangle(sk, largeur, hauteur, cx=0.0, cy=0.0):
    l2, h2 = largeur / 2.0, hauteur / 2.0
    ajouter_polygone(sk, [(cx - l2, cy - h2), (cx + l2, cy - h2),
                          (cx + l2, cy + h2), (cx - l2, cy + h2)])


def protrusion(corps, nom, sk, longueur, inversee=False,
               longueur2=None, milieu=False):
    pad = corps.newObject("PartDesign::Pad", nom)
    pad.Profile = sk
    pad.Length = longueur
    if longueur2 is not None:
        pad.Type = "TwoLengths"
        pad.Length2 = longueur2
    pad.Reversed = inversee
    pad.Midplane = milieu
    return pad


def centres_trous():
    for sx in (-1, 1):
        for sy in (-1, 1):
            yield (sx * (DEMI_L - MARGE_TROU_X), sy * (DEMI_H - MARGE_TROU_Y))


# --------------------------------------------------------------------------
# Corps PartDesign
# --------------------------------------------------------------------------

def corps_pcb(doc):
    """Carte : protrusion du contour arrondi puis cavite des 4 trous."""
    corps = doc.addObject("PartDesign::Body", "PCB")
    sk = esquisse(corps, "SkContour")
    ajouter_rectangle_arrondi(sk, LARGEUR, HAUTEUR, CONGE_COIN)
    protrusion(corps, "PadCarte", sk, EP_PCB)
    sk_trous = esquisse(corps, "SkTrous", z=EP_PCB)
    for cx, cy in centres_trous():
        sk_trous.addGeometry(Part.Circle(Vector(cx, cy, 0),
                                         Vector(0, 0, 1), DIA_TROU / 2.0),
                             False)
    poche = corps.newObject("PartDesign::Pocket", "PocheTrous")
    poche.Profile = sk_trous
    poche.Type = "ThroughAll"
    return corps


def corps_verre(doc):
    corps = doc.addObject("PartDesign::Body", "Verre")
    sk = esquisse(corps, "SkVerre", z=EP_PCB)
    cy = Y_HAUT - Y_VERRE_HAUT - VERRE_H / 2.0
    ajouter_rectangle(sk, VERRE_L, VERRE_H, 0.0, cy)
    protrusion(corps, "PadVerre", sk, VERRE_EP)
    return corps


def corps_zone_active(doc):
    """Zone utile 128x64, pelliculaire, centree dans la fenetre."""
    corps = doc.addObject("PartDesign::Body", "ZoneActive")
    sk = esquisse(corps, "SkZoneActive", z=EP_PCB + VERRE_EP)
    cy = Y_HAUT - Y_VERRE_HAUT - VERRE_H / 2.0
    ajouter_rectangle(sk, ZA_L, ZA_H, 0.0, cy)
    protrusion(corps, "PadZoneActive", sk, 0.05)
    return corps


def corps_plastique(doc):
    corps = doc.addObject("PartDesign::Body", "Plastique")
    sk = esquisse(corps, "SkPlastique")
    ajouter_rectangle(sk, NB_BROCHES * PAS_BROCHES, LARG_PLASTIQUE,
                      0.0, Y_HAUT - Y_BROCHES)
    protrusion(corps, "PadPlastique", sk, EP_PLASTIQUE, inversee=True)
    return corps


def corps_broche(doc, i):
    corps = doc.addObject("PartDesign::Body", "Broche%d" % (i + 1))
    sk = esquisse(corps, "SkBroche%d" % (i + 1))
    x = (i - (NB_BROCHES - 1) / 2.0) * PAS_BROCHES
    ajouter_rectangle(sk, COTE_BROCHE, COTE_BROCHE, x, Y_HAUT - Y_BROCHES)
    protrusion(corps, "PadBroche%d" % (i + 1), sk,
               EP_PCB + DEPASS_AVANT,
               longueur2=EP_PLASTIQUE + DEPASS_ARRIERE)
    return corps


def corps_nappe(doc):
    """Nappe pliee sur le bord bas : profil en C dans le plan YZ,
    protrusion symetrique en X."""
    corps = doc.addObject("PartDesign::Body", "Nappe")
    # plan YZ, normale +X : le u local vaut -z monde, le v local vaut y monde
    sk = esquisse(corps, "SkNappe",
                  rotation=App.Rotation(Vector(0, 1, 0), 90))
    y_bas_verre = Y_HAUT - Y_VERRE_HAUT - VERRE_H
    pts_yz = [
        (y_bas_verre, EP_PCB),                       # depart sous le verre
        (y_bas_verre, EP_PCB + NAPPE_EP),
        (Y_BAS - NAPPE_EP, EP_PCB + NAPPE_EP),       # plat avant
        (Y_BAS - NAPPE_EP, -NAPPE_EP),               # pli sur le chant
        (Y_BAS + NAPPE_RETOUR, -NAPPE_EP),           # retour arriere
        (Y_BAS + NAPPE_RETOUR, 0.0),
        (Y_BAS, 0.0),
        (Y_BAS, EP_PCB),
    ]
    ajouter_polygone(sk, [(-z, y) for (y, z) in pts_yz])
    protrusion(corps, "PadNappe", sk, NAPPE_L, milieu=True)
    return corps


def outil_percage(doc):
    """4 cylindres pour percer la carte porteuse (booleen de coupe)."""
    outils = []
    for cx, cy in centres_trous():
        outils.append(Part.makeCylinder(DIA_TROU / 2.0, 24.0,
                                        Vector(cx, cy, -12.0),
                                        Vector(0, 0, 1)))
    obj = doc.addObject("Part::Feature", "OutilPercage")
    obj.Label = "Outil - percage 4 trous carte porteuse"
    obj.Shape = Part.makeCompound(outils)
    return obj


# --------------------------------------------------------------------------
# Couleurs STEP : injection post-export
# --------------------------------------------------------------------------
# freecadcmd exporte un STEP sans presentation (les couleurs viennent des
# ViewObject, absents sans interface). On rattache donc a la main une
# couleur par solide : PRODUCT -> ... -> representation -> MANIFOLD_SOLID_BREP,
# puis chaine STYLED_ITEM standard (meme schema que KiCad StepUp / OCC).

def injecter_couleurs_step(chemin, couleurs):
    with open(chemin, "r") as f:
        texte = f.read()
    corps = re.split(r"\bDATA;\s*", texte, maxsplit=1)[1]
    entites = {}
    for m in re.finditer(r"#(\d+)\s*=\s*(.*?);", corps, re.S):
        entites[int(m.group(1))] = " ".join(m.group(2).split())

    def refs(eid):
        return [int(x) for x in re.findall(r"#(\d+)", entites[eid])]

    def chercher(type_):
        for eid, e in entites.items():
            if e.startswith(type_):
                yield eid

    prochain = max(entites) + 1
    lignes, id_couleur = [], {}

    def nouvelle(defn):
        nonlocal prochain
        lignes.append("#%d = %s;" % (prochain, defn))
        prochain += 1
        return prochain - 1

    nb_styles = 0
    for pid in chercher("PRODUCT("):
        label = re.match(r"PRODUCT\('([^']*)'", entites[pid]).group(1)
        if label not in couleurs:
            continue
        # PRODUCT -> PRODUCT_DEFINITION_FORMATION -> PRODUCT_DEFINITION
        #  -> PRODUCT_DEFINITION_SHAPE -> SHAPE_DEFINITION_REPRESENTATION
        pdf = [e for e in chercher("PRODUCT_DEFINITION_FORMATION") if pid in refs(e)]
        pd = [e for e in chercher("PRODUCT_DEFINITION(") if pdf and pdf[0] in refs(e)]
        pds = [e for e in chercher("PRODUCT_DEFINITION_SHAPE") if pd and pd[0] in refs(e)]
        sdr = [e for e in chercher("SHAPE_DEFINITION_REPRESENTATION") if pds and pds[0] in refs(e)]
        if not sdr:
            continue
        rep = [r for r in refs(sdr[0]) if "REPRESENTATION" in entites[r]
               and not entites[r].startswith("SHAPE_DEFINITION")][0]
        solides = [r for r in refs(rep)
                   if entites[r].startswith("MANIFOLD_SOLID_BREP")]
        contexte = [r for r in refs(rep)
                    if "GEOMETRIC_REPRESENTATION_CONTEXT" in entites[r]][-1]
        rgb = couleurs[label]
        transp = TRANSPARENCES.get(label, 0.0)
        if rgb not in id_couleur:
            id_couleur[rgb] = nouvelle(
                "COLOUR_RGB('',%.6f,%.6f,%.6f)" % rgb)
        styles = []
        for sol in solides:
            fasc = nouvelle("FILL_AREA_STYLE_COLOUR('',#%d)" % id_couleur[rgb])
            fas = nouvelle("FILL_AREA_STYLE('',(#%d))" % fasc)
            ssfa = nouvelle("SURFACE_STYLE_FILL_AREA(#%d)" % fas)
            elements = "#%d" % ssfa
            if transp > 0.0:
                sst = nouvelle("SURFACE_STYLE_TRANSPARENT(%.4f)" % transp)
                rend = nouvelle(
                    "SURFACE_STYLE_RENDERING_WITH_PROPERTIES(.NORMAL_SHADING."
                    ",#%d,(#%d))" % (id_couleur[rgb], sst))
                elements += ",#%d" % rend
            sss = nouvelle("SURFACE_SIDE_STYLE('',(%s))" % elements)
            ssu = nouvelle("SURFACE_STYLE_USAGE(.BOTH.,#%d)" % sss)
            psa = nouvelle("PRESENTATION_STYLE_ASSIGNMENT((#%d))" % ssu)
            styles.append(nouvelle("STYLED_ITEM('color',(#%d),#%d)" % (psa, sol)))
            nb_styles += 1
        nouvelle("MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION"
                 "('',(%s),#%d)" % (",".join("#%d" % s for s in styles), contexte))

    texte = texte.replace("ENDSEC;\nEND-ISO-10303-21;",
                          "\n".join(lignes) + "\nENDSEC;\nEND-ISO-10303-21;")
    with open(chemin, "w") as f:
        f.write(texte)
    return nb_styles


# --------------------------------------------------------------------------
# Apparence du document (couleurs, transparences, visibilites)
# --------------------------------------------------------------------------

def lister_apparences(piece, outil):
    """(objet, rgb ou None, transparence 0..1, visible) pour tout l'arbre."""
    entrees = []
    for corps in piece:
        rgb = COULEURS[corps.Label]
        transp = TRANSPARENCES.get(corps.Label, 0.0)
        entrees.append((corps, rgb, transp, True))
        for elem in corps.Group:
            if elem.TypeId in ("PartDesign::Pad", "PartDesign::Pocket"):
                entrees.append((elem, rgb, transp, elem == corps.Tip))
            elif elem.TypeId == "Sketcher::SketchObject":
                entrees.append((elem, None, 0.0, False))
            elif elem.TypeId == "App::Origin":
                entrees.append((elem, None, 0.0, False))
                for axe in elem.OriginFeatures:
                    entrees.append((axe, None, 0.0, False))
    entrees.append((outil, None, 0.0, False))
    return entrees


def appliquer_apparence_gui(entrees):
    """Voie native (interface presente, meme offscreen) : ViewObject."""
    for obj, rgb, transp, visible in entrees:
        vo = obj.ViewObject
        vo.Visibility = visible
        if rgb is not None:
            try:
                vo.ShapeColor = rgb
                vo.Transparency = int(round(transp * 100))
            except AttributeError:
                pass  # certains conteneurs n'ont pas ces proprietes


def injecter_apparence_fcstd(chemin, entrees):
    """Repli sans interface : GuiDocument.xml minimal ecrit dans l'archive.

    Les visibilites (esquisses et origines masquees, seule la protrusion
    de tete visible) sont restaurees fidelement ; les couleurs passent par
    la propriete de compatibilite ShapeColor, moins fiable que la voie
    native - preferer l'execution offscreen documentee en tete de fichier.
    """
    blocs = []
    for obj, rgb, transp, visible in entrees:
        props = ('                <Property name="Visibility" type="App::PropertyBool" status="1">\n'
                 '                    <Bool value="%s"/>\n'
                 '                </Property>\n' % ("true" if visible else "false"))
        n = 1
        if rgb is not None:
            paquet = ((int(round(rgb[0] * 255)) << 24) |
                      (int(round(rgb[1] * 255)) << 16) |
                      (int(round(rgb[2] * 255)) << 8) | 0xFF)
            props += ('                <Property name="ShapeColor" type="App::PropertyColor" status="1">\n'
                      '                    <PropertyColor value="%d"/>\n'
                      '                </Property>\n'
                      '                <Property name="Transparency" type="App::PropertyPercent" status="1">\n'
                      '                    <Integer value="%d"/>\n'
                      '                </Property>\n'
                      % (paquet, int(round(transp * 100))))
            n = 3
        blocs.append(
            '        <ViewProvider name="%s" expanded="0">\n'
            '            <Properties Count="%d" TransientCount="0">\n%s'
            '            </Properties>\n'
            '        </ViewProvider>' % (obj.Name, n, props))
    xml = ("<?xml version='1.0' encoding='utf-8'?>\n"
           '<Document SchemaVersion="1" HasExpansion="1">\n'
           '    <ViewProviderData Count="%d">\n%s\n'
           '    </ViewProviderData>\n'
           '</Document>\n' % (len(blocs), "\n".join(blocs)))
    with zipfile.ZipFile(chemin, "a", zipfile.ZIP_DEFLATED) as z:
        z.writestr("GuiDocument.xml", xml)
    return len(blocs)


# --------------------------------------------------------------------------
# Assemblage du document
# --------------------------------------------------------------------------

def main():
    doc = App.newDocument(NOM)
    doc.Comment = (
        "Ecran OLED 0,96 SSD1306 I2C 4 broches - modele d'encombrement "
        "parametrique PartDesign. Genere par oled096_i2c.py. Carte "
        "27,0 x 24,7 mesuree sur l'exemplaire UsainBot ; fenetre d'ecran "
        "0,96 pouce (21,74 x 10,86 + bordure). Percages et entraxes "
        "A VERIFIER au pied a coulisse."
    )

    piece = [corps_pcb(doc), corps_verre(doc), corps_zone_active(doc),
             corps_plastique(doc), corps_nappe(doc)]
    piece += [corps_broche(doc, i) for i in range(NB_BROCHES)]
    outil = outil_percage(doc)

    doc.recompute()
    erreurs = [o.Name for o in doc.Objects
               if "Error" in getattr(o, "State", []) or
                  "Invalid" in getattr(o, "State", [])]
    if erreurs:
        raise RuntimeError("recompute en erreur : %s" % ", ".join(erreurs))

    entrees = lister_apparences(piece, outil)
    if App.GuiUp:
        appliquer_apparence_gui(entrees)

    chemin_fcstd = os.path.join(ICI, NOM + ".fcstd")
    doc.saveAs(chemin_fcstd)
    chemin_step = os.path.join(ICI, NOM + ".step")
    Import.export(piece, chemin_step)
    Mesh.export(piece, os.path.join(ICI, NOM + ".stl"))
    nb = injecter_couleurs_step(chemin_step, COULEURS)

    if App.GuiUp:
        nb_vues = len(entrees)
        mode_vues = "natives (ViewObject)"
    else:
        nb_vues = injecter_apparence_fcstd(chemin_fcstd, entrees)
        mode_vues = "injectees (repli sans interface)"

    bb = piece[0].Shape.BoundBox
    for p in piece[1:]:
        bb = bb.united(p.Shape.BoundBox)
    y_bas_verre = Y_HAUT - Y_VERRE_HAUT - VERRE_H
    y_haut_trou_bas = -(DEMI_H - MARGE_TROU_Y) + DIA_TROU / 2.0
    print("--- OLED 0,96 SSD1306 I2C (PartDesign) ---")
    print("carte %.2f x %.2f x %.2f mm" % (LARGEUR, HAUTEUR, EP_PCB))
    print("encombrement  X %.2f  Y %.2f  Z %.2f mm (z %.2f a %.2f)"
          % (bb.XLength, bb.YLength, bb.ZLength, bb.ZMin, bb.ZMax))
    print("trous dia %.1f, entraxes X %.1f  Y %.1f mm"
          % (DIA_TROU, LARGEUR - 2 * MARGE_TROU_X, HAUTEUR - 2 * MARGE_TROU_Y))
    print("garde verre / trous du bas : %.2f mm (positif = degage)"
          % (y_bas_verre - y_haut_trou_bas))
    print("solides valides : %s" % all(p.Shape.isValid() for p in piece))
    print("couleurs STEP injectees : %d solide(s), transparence verre %.0f %%"
          % (nb, TRANSPARENCES.get("Verre", 0.0) * 100))
    print("apparences FCStd %s : %d vue(s)" % (mode_vues, nb_vues))
    print("fichiers ecrits dans %s" % ICI)


main()

# Lance via l'application complete en mode offscreen : sortir une fois
# les fichiers ecrits (sinon FreeCAD reste en attente d'evenements).
if App.GuiUp and os.environ.get("QT_QPA_PLATFORM") == "offscreen":
    sys.stdout.flush()
    os._exit(0)
