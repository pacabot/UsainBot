# -*- coding: utf-8 -*-
"""
Support pare-soleil du duo de telemetrie + diodes couchees (PartDesign).

Trois corps PartDesign :
  - `Support_PareSoleil` : la piece a imprimer. Socle visse par le DESSOUS
    de la carte (avant-trou M2 central + 2 pions dont un decale en
    detrompeur), deux futs perces qui guident les diodes couchees et
    prolongent leurs axes en tubes pare-soleil ;
  - `OPV302_TX` : le VCSEL TO-46 couche, pattes cintrees a 90 deg ;
  - `BPV10NF_RX` : la photodiode T-1 3/4 couchee, pattes cintrees.
Les diodes servent de gabarit de cintrage et de modele 3D KiCad : leurs
pattes tombent exactement sur les pads de l'empreinte Telemetry_Duo_Coude
(../electronics/kicad-lib/gen_telemetry_footprint.py).

REPERE = repere 3D de KiCad (X visee, Z dessus de carte, Y vers le HAUT de
l'ecran de l'editeur d'empreinte, soit l'oppose du Y du .kicad_mod).
Contrairement aux generateurs moteurs : AUCUN miroir a l'export, le modele
est construit directement dans la bonne chiralite — le STL imprime et le
STEP KiCad sont la meme piece. TX (OPV302) en Y=+5, RX (BPV10NF) en Y=-5.

Optique (datasheets TT OPV302 Rev C, Vishay BPV10NF Rev 2.3) :
  - VCSEL : divergence 4 deg FWHM -> l'ouverture TX (dia 3,5) ne rase rien,
    elle ne sert que de garde anti-reflets ;
  - BPV10NF : demi-sensibilite +/-20 deg, puce a 4,4 mm sous le sommet.
    Le tube RX (dia 3,5 sur 6,1 mm) ramene le champ vu de la puce a
    ~+/-9,5 deg : c'est LE pare-soleil, il rejette le ciel et les rampes
    de la salle sans perdre le spot du VCSEL au-dela de ~60 mm (parallaxe
    de l'entraxe 10 : atan(10/d) < 9,5 deg des que d > 60 mm) — d'ou des
    axes paralleles, sans pincement.
Alesages cotes pour la resine (SLA) : en FDM, prevoir +0,1 a +0,2 ou
percer/aleser apres impression. A recaler sur les boitiers recus.

Execution (voie recommandee, cf. oled096_i2c.py) :
    QT_QPA_PLATFORM=offscreen /Applications/FreeCAD.app/Contents/MacOS/FreeCAD \
        telemetry_duo.py

Sorties (dans ce dossier) : Telemetry_Duo.fcstd, Telemetry_Support.step/.stl
(la piece a imprimer), Telemetry_Duo_Diodes.step — les deux STEP sont aussi
copies dans ../electronics/kicad-lib/3d/ pour l'empreinte.
"""

import math
import os
import re
import shutil
import sys
import zipfile

import FreeCAD as App
import Part
import Import
import Mesh
from FreeCAD import Vector

# --------------------------------------------------------------------------
# Parametres (mm) — repere 3D KiCad, origine = axe de la vis M2
# --------------------------------------------------------------------------

ENTRAXE      = 10.0
Z_AXE        = 6.0     # hauteur des axes optiques au-dessus du PCB
X_ARRIERE    = -5.0    # face arriere du support (sortie des pattes)
X_AVANT      = 8.0     # face avant du pare-soleil. Raccourci de 2 mm le
                       # 4 septembre : le tube RX passe de 6,1 a 4,1 mm, donc
                       # de +/-9,5 a +/-11,6 deg vus de la puce. On perd un
                       # peu de rejet du ciel, on gagne sur la parallaxe -
                       # le spot du VCSEL est vu des 49 mm au lieu de 61.
DEMI_LARG    = 9.0     # demi-largeur du socle
Z_SOCLE      = 6.0     # le socle monte jusqu'a l'axe, les futs le coiffent
R_FUT        = 4.0     # rayon exterieur des deux futs

TX_Y         = +ENTRAXE / 2   # OPV302 (le .kicad_mod, Y inverse, le met en -5)
RX_Y         = -ENTRAXE / 2   # BPV10NF

# lamage commun d'entree (les collerettes) : OPV302 5,84 max / BPV10NF 5,90 max
D_LAMAGE     = 6.2
P_LAMAGE     = 0.9     # collerettes de 0,7-0,76 -> affleurent en retrait

# TX : OPV302, TO-46 (capot 4,57-4,72, hauteur totale 4,83-5,33 dont dome)
TX_ALESAGE   = 4.9
TX_FOND      = 0.6     # fin de l'alesage capot (dome affleure a +0,47)
TX_OUVERTURE = 3.5     # tube avant, garde anti-reflets (faisceau 4 deg FWHM)
TX_COLLER_D  = 5.4     # collerette du modele de diode
TX_CAP_D     = 4.7
TX_CAP_FIN   = -0.8    # fin du capot cylindrique, puis dome (stylise)
TX_NEZ_D     = 3.4
TX_NEZ_FIN   = 0.45
TO46_R_PATTE = 2.54 / 2         # pattes sur cercle dia 2,54, a 90 deg
TX_DY        = TO46_R_PATTE * math.sin(math.radians(45))  # 0,898
TX_DZ        = TX_DY            # pattes 1 et 2 a +/-45 deg, patte 3 coupee
TX_D_PATTE   = 0.45

# RX : BPV10NF, T-1 3/4 (corps 5,0+/-0,15, collerette 5,75, sommet a 8,6)
RX_ALESAGE   = 5.25
RX_FOND      = 3.9     # fin de l'alesage corps (sommet de lentille a +3,8)
RX_OUVERTURE = 3.5     # LE pare-soleil : dia 3,5 sur les 6,1 mm restants
RX_COLLER_D  = 5.75
RX_CORPS_D   = 5.0
RX_CORPS_FIN = 2.8     # fin du cylindre, puis dome R2,45 (stylise)
RX_NEZ_D     = 4.2
RX_NEZ_FIN   = 3.75
RX_PUCE_X    = 3.8 - 4.4        # puce 4,4 sous le sommet de lentille
RX_DY        = 2.54 / 2         # pattes diametralement opposees
RX_C_PATTE   = 0.63             # patte carree

# collerettes plaquees au fond du lamage : face avant en -4,1
X_COLLERETTE = X_ARRIERE + P_LAMAGE          # -4.1
X_FLASQUE    = X_COLLERETTE - 0.7            # -4.8 : arriere des collerettes

# fixation par le dessous et pattes
D_PILOTE     = 1.7     # avant-trou M2 (engagement 6 mm dans le socle)
P_PILOTE     = 7.0
D_PION       = 1.45    # dans des percages carte de 1,6
L_PION       = 1.5     # carte de 1,6 : ne depasse pas dessous
PION_A       = (-3.5, 0.0)
PION_B       = (3.5, -1.5)      # decale vers RX : detrompeur
X_PADS       = -7.5    # ligne des pads de l'empreinte
Z_BAS_PATTE  = -1.0    # les pattes traversent la carte

ICI = os.path.dirname(os.path.abspath(__file__))
_BILAN = []


def dire(txt):
    """print() est avale par l'application complete en offscreen : le bilan
    part aussi dans Telemetry_Duo.log, a cote des sorties."""
    print(txt)
    _BILAN.append(txt)

DOSSIER_3D = os.path.abspath(os.path.join(
    ICI, "..", "electronics", "kicad-lib", "3d"))
NOM = "Telemetry_Duo"

COULEURS = {
    "Support_PareSoleil": (0.17, 0.17, 0.18),   # impression sombre et mate
    "OPV302_TX":          (0.83, 0.68, 0.21),   # embase TO doree
    "BPV10NF_RX":         (0.10, 0.10, 0.12),   # epoxy noir filtrant
}
# Le support est OPAQUE : c'est un pare-soleil, un modele translucide donne
# une fausse idee de la piece imprimee et laisse croire que la lumiere passe
# par la paroi. Les alesages se lisent en coupe, pas par transparence.
TRANSPARENCES = {}

# --------------------------------------------------------------------------
# Aides esquisses (geometrie sans contraintes : le pilotage reste ici)
# --------------------------------------------------------------------------

# plan YZ, normale +X : u local = Y monde, v local = Z monde
ROT_YZ = App.Rotation(Vector(1, 1, 1), 120)


def esquisse(corps, nom, position=None, rotation=None):
    sk = corps.newObject("Sketcher::SketchObject", nom)
    sk.Placement = App.Placement(position or Vector(0, 0, 0),
                                 rotation or App.Rotation())
    return sk


def esquisse_yz(corps, nom, x):
    return esquisse(corps, nom, Vector(x, 0, 0), ROT_YZ)


def ajouter_cercle(sk, cx, cy, d):
    sk.addGeometry(Part.Circle(Vector(cx, cy, 0), Vector(0, 0, 1), d / 2.0),
                   False)


def ajouter_rectangle(sk, largeur, hauteur, cx=0.0, cy=0.0):
    l2, h2 = largeur / 2.0, hauteur / 2.0
    pts = [(cx - l2, cy - h2), (cx + l2, cy - h2),
           (cx + l2, cy + h2), (cx - l2, cy + h2)]
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]
        sk.addGeometry(Part.LineSegment(Vector(a[0], a[1], 0),
                                        Vector(b[0], b[1], 0)), False)


def protrusion(corps, nom, sk, longueur, inversee=False):
    pad = corps.newObject("PartDesign::Pad", nom)
    pad.Profile = sk
    pad.Length = longueur
    pad.Reversed = inversee
    return pad


def poche(corps, nom, sk, longueur=None, inversee=True):
    """Les esquisses YZ ont leur normale en +X : une poche part par defaut
    en -X (hors matiere), d'ou inversee=True — meme piege que l'equerre."""
    p = corps.newObject("PartDesign::Pocket", nom)
    p.Profile = sk
    if longueur is None:
        p.Type = "ThroughAll"
    else:
        p.Length = longueur
    p.Reversed = inversee
    return p


# --------------------------------------------------------------------------
# Le support pare-soleil
# --------------------------------------------------------------------------

def corps_support(doc):
    corps = doc.addObject("PartDesign::Body", "Support_PareSoleil")

    sk = esquisse(corps, "SkSocle")
    ajouter_rectangle(sk, X_AVANT - X_ARRIERE, 2 * DEMI_LARG,
                      (X_AVANT + X_ARRIERE) / 2.0, 0.0)
    protrusion(corps, "PadSocle", sk, Z_SOCLE)

    sk = esquisse_yz(corps, "SkFuts", X_ARRIERE)
    for y in (TX_Y, RX_Y):
        ajouter_cercle(sk, y, Z_AXE, 2 * R_FUT)
    protrusion(corps, "PadFuts", sk, X_AVANT - X_ARRIERE)

    sk = esquisse(corps, "SkPions")
    for cx, cy in (PION_A, PION_B):
        ajouter_cercle(sk, cx, cy, D_PION)
    protrusion(corps, "PadPions", sk, L_PION, inversee=True)

    sk = esquisse_yz(corps, "SkLamages", X_ARRIERE)
    for y in (TX_Y, RX_Y):
        ajouter_cercle(sk, y, Z_AXE, D_LAMAGE)
    poche(corps, "PocheLamages", sk, P_LAMAGE)

    sk = esquisse_yz(corps, "SkAlesageTX", X_ARRIERE)
    ajouter_cercle(sk, TX_Y, Z_AXE, TX_ALESAGE)
    poche(corps, "PocheAlesageTX", sk, TX_FOND - X_ARRIERE)

    sk = esquisse_yz(corps, "SkAlesageRX", X_ARRIERE)
    ajouter_cercle(sk, RX_Y, Z_AXE, RX_ALESAGE)
    poche(corps, "PocheAlesageRX", sk, RX_FOND - X_ARRIERE)

    sk = esquisse_yz(corps, "SkOuvertures", X_ARRIERE)
    ajouter_cercle(sk, TX_Y, Z_AXE, TX_OUVERTURE)
    ajouter_cercle(sk, RX_Y, Z_AXE, RX_OUVERTURE)
    poche(corps, "PocheOuvertures", sk)

    sk = esquisse(corps, "SkPilote", Vector(0, 0, P_PILOTE))
    ajouter_cercle(sk, 0, 0, D_PILOTE)
    poche(corps, "PochePilote", sk, P_PILOTE, inversee=False)

    return corps


# --------------------------------------------------------------------------
# Les deux diodes couchees, pattes cintrees sur les pads
# --------------------------------------------------------------------------

def pattes(corps, prefixe, positions_y, z_sortie, section, carree):
    """Trait horizontal depuis la collerette puis descente sur le pad.
    Le trait horizontal demarre 0,1 DANS la collerette (fusion garantie) et
    depasse le plan des pads d'un demi-diametre pour souder le coude."""
    sk = esquisse_yz(corps, "Sk%sH" % prefixe, X_FLASQUE + 0.1)
    for y in positions_y:
        if carree:
            ajouter_rectangle(sk, section, section, y, z_sortie)
        else:
            ajouter_cercle(sk, y, z_sortie, section)
    protrusion(corps, "Pad%sH" % prefixe, sk,
               (X_FLASQUE + 0.1) - (X_PADS - section / 2), inversee=True)

    z_haut = z_sortie + section / 2
    sk = esquisse(corps, "Sk%sV" % prefixe, Vector(0, 0, z_haut))
    for y in positions_y:
        if carree:
            ajouter_rectangle(sk, section, section, X_PADS, y)
        else:
            ajouter_cercle(sk, X_PADS, y, section)
    protrusion(corps, "Pad%sV" % prefixe, sk, z_haut - Z_BAS_PATTE,
               inversee=True)


def corps_tx(doc):
    corps = doc.addObject("PartDesign::Body", "OPV302_TX")
    sk = esquisse_yz(corps, "SkTxCollerette", X_FLASQUE)
    ajouter_cercle(sk, TX_Y, Z_AXE, TX_COLLER_D)
    protrusion(corps, "PadTxCollerette", sk, 0.7)
    sk = esquisse_yz(corps, "SkTxCapot", X_COLLERETTE)
    ajouter_cercle(sk, TX_Y, Z_AXE, TX_CAP_D)
    protrusion(corps, "PadTxCapot", sk, TX_CAP_FIN - X_COLLERETTE)
    sk = esquisse_yz(corps, "SkTxNez", TX_CAP_FIN)
    ajouter_cercle(sk, TX_Y, Z_AXE, TX_NEZ_D)
    protrusion(corps, "PadTxNez", sk, TX_NEZ_FIN - TX_CAP_FIN)
    pattes(corps, "TxPattes", (TX_Y - TX_DY, TX_Y + TX_DY),
           Z_AXE + TX_DZ, TX_D_PATTE, carree=False)
    return corps


def corps_rx(doc):
    corps = doc.addObject("PartDesign::Body", "BPV10NF_RX")
    sk = esquisse_yz(corps, "SkRxCollerette", X_FLASQUE)
    ajouter_cercle(sk, RX_Y, Z_AXE, RX_COLLER_D)
    protrusion(corps, "PadRxCollerette", sk, 0.7)
    sk = esquisse_yz(corps, "SkRxCorps", X_COLLERETTE)
    ajouter_cercle(sk, RX_Y, Z_AXE, RX_CORPS_D)
    protrusion(corps, "PadRxCorps", sk, RX_CORPS_FIN - X_COLLERETTE)
    sk = esquisse_yz(corps, "SkRxNez", RX_CORPS_FIN)
    ajouter_cercle(sk, RX_Y, Z_AXE, RX_NEZ_D)
    protrusion(corps, "PadRxNez", sk, RX_NEZ_FIN - RX_CORPS_FIN)
    pattes(corps, "RxPattes", (RX_Y - RX_DY, RX_Y + RX_DY),
           Z_AXE, RX_C_PATTE, carree=True)
    return corps


# --------------------------------------------------------------------------
# Controles : la geometrie qui compte, mesuree sur les solides
# --------------------------------------------------------------------------

def volume_commun(forme, outil):
    """Volume de l'intersection — en valeur absolue : le volume d'un
    common() sort parfois negatif (piege releve sur la turbine)."""
    return abs(forme.common(outil).Volume)


def cylindre_x(x1, x2, y, z, r):
    return Part.makeCylinder(r, x2 - x1, Vector(x1, y, z), Vector(1, 0, 0))


def controler(support, tx, rx):
    err = []

    # 1. les deux voies optiques sont degagees sur toute la longueur
    for nom, y, r, x1 in (("TX", TX_Y, TX_OUVERTURE / 2 - 0.1, TX_FOND),
                          ("RX", RX_Y, RX_OUVERTURE / 2 - 0.1, RX_FOND)):
        v = volume_commun(support.Shape,
                          cylindre_x(x1 + 0.05, X_AVANT - 0.05, y, Z_AXE, r))
        if v > 1e-6:
            err.append("voie %s obstruee (%.3f mm3)" % (nom, v))

    # 2. les diodes inserees ne touchent pas le support
    for nom, diode in (("TX", tx), ("RX", rx)):
        v = volume_commun(support.Shape, diode.Shape)
        if v > 1e-6:
            err.append("interference support/%s : %.3f mm3" % (nom, v))

    # 3. cloison pleine entre les deux voies (aucune diaphonie interne).
    # La sonde SUIT la longueur du support : ecrite en dur (7 mm depuis X=2)
    # elle debordait de la piece des qu'on raccourcissait le pare-soleil, et
    # signalait une cloison ajouree la ou il n'y avait plus que du vide
    # au-dela de la face avant.
    l_cloison = X_AVANT - 2.0
    attendu = l_cloison * 2.0 * 1.5
    boite = Part.makeBox(l_cloison, 2.0, 1.5, Vector(2.0, -1.0, 4.5))
    v = volume_commun(support.Shape, boite)
    if v < attendu - 0.1:
        err.append("cloison TX/RX ajouree (%.1f mm3 sur %.1f)" % (v, attendu))

    # 4. chaque patte descend bien au travers de son pad
    pads = [("TX K", tx, TX_Y + TX_DY), ("TX A", tx, TX_Y - TX_DY),
            ("RX K", rx, RX_Y - RX_DY), ("RX A", rx, RX_Y + RX_DY)]
    for nom, diode, y in pads:
        sonde = Part.makeCylinder(0.5, 0.8, Vector(X_PADS, y, -0.9),
                                  Vector(0, 0, 1))
        if volume_commun(diode.Shape, sonde) < 0.01:
            err.append("patte %s hors pad (%.2f, %.2f)" % (nom, X_PADS, y))

    # 5. rien sous le plan de carte, hors pions et pattes
    if support.Shape.BoundBox.ZMin < -L_PION - 1e-6:
        err.append("le support descend sous les pions : %.2f"
                   % support.Shape.BoundBox.ZMin)
    return err


# --------------------------------------------------------------------------
# Couleurs STEP : injection post-export (meme voie que l'OLED)
# --------------------------------------------------------------------------

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

def lister_apparences(piece):
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
    return entrees


def appliquer_apparence_gui(entrees):
    for obj, rgb, transp, visible in entrees:
        vo = obj.ViewObject
        vo.Visibility = visible
        if rgb is not None:
            try:
                vo.ShapeColor = rgb
                vo.Transparency = int(round(transp * 100))
            except AttributeError:
                pass


def injecter_apparence_fcstd(chemin, entrees):
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
        "Duo de telemetrie couche : support pare-soleil imprime (visse M2 "
        "par le dessous, 2 pions dont un detrompeur) + OPV302 TO-46 et "
        "BPV10NF T-1 3/4 pattes cintrees a 90 deg. Genere par "
        "telemetry_duo.py. Repere 3D KiCad, aucun miroir a l'export. "
        "Alesages cotes SLA, a recaler sur boitiers recus."
    )

    support = corps_support(doc)
    tx = corps_tx(doc)
    rx = corps_rx(doc)
    piece = [support, tx, rx]

    doc.recompute()
    erreurs = [o.Name for o in doc.Objects
               if "Error" in getattr(o, "State", []) or
                  "Invalid" in getattr(o, "State", [])]
    if erreurs:
        raise RuntimeError("recompute en erreur : %s" % ", ".join(erreurs))
    if not all(p.Shape.isValid() for p in piece):
        raise RuntimeError("solide invalide")

    problemes = controler(support, tx, rx)
    if problemes:
        raise RuntimeError("controles : " + " ; ".join(problemes))

    entrees = lister_apparences(piece)
    if App.GuiUp:
        appliquer_apparence_gui(entrees)

    chemin_fcstd = os.path.join(ICI, NOM + ".fcstd")
    doc.saveAs(chemin_fcstd)
    chemin_support = os.path.join(ICI, "Telemetry_Support.step")
    chemin_diodes = os.path.join(ICI, "Telemetry_Duo_Diodes.step")
    Import.export([support], chemin_support)
    Import.export([tx, rx], chemin_diodes)
    Mesh.export([support], os.path.join(ICI, "Telemetry_Support.stl"))
    nb = injecter_couleurs_step(chemin_support, COULEURS)
    nb += injecter_couleurs_step(chemin_diodes, COULEURS)
    for f in (chemin_support, chemin_diodes):
        shutil.copy2(f, DOSSIER_3D)

    if App.GuiUp:
        nb_vues, mode_vues = len(entrees), "natives (ViewObject)"
    else:
        nb_vues = injecter_apparence_fcstd(chemin_fcstd, entrees)
        mode_vues = "injectees (repli sans interface)"

    # pas de capture d'ecran ici : l'offscreen de cette machine n'a pas de
    # contexte OpenGL et saveImage() segfaulte apres coup (constate) —
    # l'apercu se fait depuis le STL (voir docstring) ou dans l'interface.
    demi_tx = math.degrees(math.atan((TX_OUVERTURE / 2) / (X_AVANT - TX_FOND)))
    demi_rx = math.degrees(math.atan((RX_OUVERTURE / 2) / (X_AVANT - RX_PUCE_X)))
    dire("--- Telemetry Duo : support pare-soleil + diodes couchees ---")
    dire("axes optiques a Z=%.1f, entraxe %.1f, visee +X, "
          "face avant du tube en X=%+.1f" % (Z_AXE, ENTRAXE, X_AVANT))
    dire("TX OPV302  : alesage %.2f (capot 4,72 max), pare-soleil "
          "dia %.1f x %.1f -> +/-%.1f deg (faisceau 4 deg FWHM)"
          % (TX_ALESAGE, TX_OUVERTURE, X_AVANT - TX_FOND, demi_tx))
    dire("RX BPV10NF : alesage %.2f (corps 5,15 max), pare-soleil "
          "dia %.1f x %.1f -> +/-%.1f deg vus de la puce (natif +/-20)"
          % (RX_ALESAGE, RX_OUVERTURE, X_AVANT - RX_FOND, demi_rx))
    dire("recouvrement TX/RX complet au-dela de ~%.0f mm (entraxe %.0f)"
          % ((ENTRAXE / math.tan(math.radians(demi_rx))), ENTRAXE))
    dire("vis M2 par le dessous : avant-trou %.1f x %.1f, engagement "
          "%.1f mm (M2x8 avec carte de 1,6)" % (D_PILOTE, P_PILOTE, Z_SOCLE))
    dire("pions %.2f x %.1f en %s et %s (percages carte 1,6)"
          % (D_PION, L_PION, PION_A, PION_B))
    for p in piece:
        bb = p.Shape.BoundBox
        dire("%-18s X %6.2f a %6.2f  Y %6.2f a %6.2f  Z %6.2f a %6.2f"
              % (p.Label, bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
    dire("controles geometriques : tous passes")
    dire("couleurs STEP injectees : %d style(s)" % nb)
    dire("apparences FCStd %s : %d vue(s)" % (mode_vues, nb_vues))
    dire("fichiers ecrits dans %s et %s" % (ICI, DOSSIER_3D))

    with open(os.path.join(ICI, NOM + ".log"), "w") as f:
        f.write("\n".join(_BILAN) + "\n")


# Garde : FreeCAD rejoue le script a l'initialisation de l'interface
# (piege releve sur la turbine) — sentinelle sur le module App.
if not getattr(App, "_telemetry_duo_fait", False):
    App._telemetry_duo_fait = True
    main()

# Lance via l'application complete en mode offscreen : sortir une fois
# les fichiers ecrits (sinon FreeCAD reste en attente d'evenements).
if App.GuiUp and os.environ.get("QT_QPA_PLATFORM") == "offscreen":
    sys.stdout.flush()
    os._exit(0)
