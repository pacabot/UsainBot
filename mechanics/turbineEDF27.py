# -*- coding: utf-8 -*-
"""
Module 3D parametrique : turbine EDF 27 mm (appui aerodynamique UsainBot).

Modele d'encombrement / integration, pas un modele aerodynamique : les
diametres, la longueur hors-tout et le nombre de pales sont a la cote ; le
profil des pales et des aubes est representatif, pas releve sur la piece.

Cotes de reference (AEO-RC / AEORC POWER-X 27 mm, moteur M1204, 7 pales) :
  - diametre interieur de veine ......... 27,4 mm
  - diametre exterieur du fut ........... 29,7 mm
  - diametre exterieur de la levre ...... 36,7 mm
  - longueur hors-tout .................. 25,8 mm
  - masse ............................... 8 a 11 g selon version
Sources : turbines-rc.com (fiche AEO RC POWER-X 27 mm) et probots.co.in
(fiche AF27102A). A RECALER AU PIED A COULISSE sur la piece recue : les
declinaisons du meme fut varient de quelques dixiemes.

Repere : axe de rotation = Z. z = 0 au plan d'ejection (face arriere),
z = LONGUEUR_HT au plan d'aspiration (levre). L'air entre en z = +L et
sort en z = 0. Origine XY sur l'axe.

Regeneration :
  /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd turbineEDF27.py
Produit turbineEDF27.fcstd, turbineEDF27.step et turbineEDF27.stl a cote.
"""

import os
import math

import FreeCAD as App
import Part
import Mesh
import Import

from FreeCAD import Vector

# --------------------------------------------------------------------------
# Parametres : tout se regle ici, puis on relance le script.
# --------------------------------------------------------------------------

DIA_VEINE        = 27.4   # diametre interieur du fut (passage d'air)
DIA_FUT          = 29.7   # diametre exterieur du fut
DIA_LEVRE        = 36.7   # diametre exterieur de la levre d'entree
LONGUEUR_HT      = 25.8   # longueur hors-tout, levre comprise
HAUTEUR_LEVRE    = 3.0    # hauteur du bourrelet exterieur de la levre
RAYON_BELL       = 3.5    # rayon du conge d'entree (bell mouth)
JEU_BOUT_PALE    = 0.30   # jeu radial entre bout de pale et veine

NB_PALES         = 7      # rotor
DIA_MOYEU_ROTOR  = 11.2
PALE_CORDE_PIED  = 7.0
PALE_CORDE_BOUT  = 6.0
PALE_EPAIS_PIED  = 1.00
PALE_EPAIS_BOUT  = 0.60
PALE_CALAGE_PIED = 45.0   # angle par rapport au plan de rotation, degres
PALE_CALAGE_BOUT = 25.0
PALE_Z_CENTRE    = 18.0   # position axiale du milieu de corde au pied
PALE_FLECHE      = 0.15   # recul axial par mm de rayon

NB_AUBES         = 5      # redresseur / support moteur
DIA_MOYEU_ARR    = 13.0
AUBE_CORDE       = 7.0
AUBE_EPAIS       = 1.20
AUBE_CALAGE      = 65.0
AUBE_Z_CENTRE    = 7.0
MOYEU_ARR_HAUT   = 12.5   # sommet du moyeu arriere

SPINNER_HAUT     = LONGUEUR_HT - 1.2  # base de la pointe spherique (rayon 1,2)
SPINNER_BASE     = 21.0   # base du cone d entree

DIA_FAISCEAU     = 3.0    # encombrement des trois fils moteur
LONG_FAISCEAU    = 15.0
Z_FAISCEAU       = 2.5

JEU_ENVELOPPE    = 0.75   # marge radiale du volume d'interdiction
JEU_DECOUPE      = 0.50   # marge sur les outils de decoupe

ICI = os.path.dirname(os.path.abspath(__file__))
NOM = "turbineEDF27"

R_VEINE  = DIA_VEINE / 2.0
R_FUT    = DIA_FUT / 2.0
R_LEVRE  = DIA_LEVRE / 2.0
R_BOUT   = R_VEINE - JEU_BOUT_PALE
R_MOYEU  = DIA_MOYEU_ROTOR / 2.0
R_MOY_AR = DIA_MOYEU_ARR / 2.0
AXE_Z    = Vector(0, 0, 1)
ORIG     = Vector(0, 0, 0)


# --------------------------------------------------------------------------
# Outils de construction
# --------------------------------------------------------------------------

def profil_section(rayon, corde, epaisseur, cambrure, calage_deg, z_centre,
                   n_points=16):
    """Contour ferme d'un profil cambre, dans le plan x = rayon.

    Le profil est place tangentiellement (corde inclinee de `calage_deg` par
    rapport au plan de rotation XY) et centre sur z_centre.
    """
    beta = math.radians(calage_deg)
    dir_corde = Vector(0.0, math.cos(beta), math.sin(beta))
    dir_normale = Vector(0.0, -math.sin(beta), math.cos(beta))
    centre = Vector(rayon, 0.0, z_centre)

    def point(u, signe):
        x = (u - 0.5) * corde
        y_camb = cambrure * 4.0 * u * (1.0 - u) * corde
        y_epais = 0.5 * epaisseur * math.sin(math.pi * u) ** 0.9
        return centre + dir_corde * x + dir_normale * (y_camb + signe * y_epais)

    pts = [point(i / float(n_points), +1.0) for i in range(n_points + 1)]
    pts += [point(i / float(n_points), -1.0) for i in range(n_points - 1, 0, -1)]
    pts.append(pts[0])
    return Part.makePolygon(pts)


def interp(a, b, t):
    return a + (b - a) * t


def construire_pale():
    """Une pale de rotor, deja recoupee au diametre de veine."""
    rayons = [R_MOYEU - 0.2, 8.2, 11.0, 14.6]
    r0, r1 = rayons[0], rayons[-1]
    sections = []
    for r in rayons:
        t = (r - r0) / (r1 - r0)
        sections.append(profil_section(
            rayon=r,
            corde=interp(PALE_CORDE_PIED, PALE_CORDE_BOUT, t),
            epaisseur=interp(PALE_EPAIS_PIED, PALE_EPAIS_BOUT, t),
            cambrure=0.06,
            calage_deg=interp(PALE_CALAGE_PIED, PALE_CALAGE_BOUT, t),
            z_centre=PALE_Z_CENTRE - PALE_FLECHE * (r - r0),
        ))
    brut = Part.makeLoft(sections, True, True)
    limite = Part.makeCylinder(R_BOUT, LONGUEUR_HT + 10.0, Vector(0, 0, -5.0), AXE_Z)
    return brut.common(limite)


def construire_aube():
    """Une aube de redresseur, recoupee au diametre de veine."""
    sections = [
        profil_section(R_MOY_AR - 0.4, AUBE_CORDE, AUBE_EPAIS, 0.03,
                       AUBE_CALAGE, AUBE_Z_CENTRE),
        profil_section(15.0, AUBE_CORDE, AUBE_EPAIS * 0.85, 0.03,
                       AUBE_CALAGE, AUBE_Z_CENTRE),
    ]
    brut = Part.makeLoft(sections, True, True)
    limite = Part.makeCylinder(R_VEINE, LONGUEUR_HT + 10.0, Vector(0, 0, -5.0), AXE_Z)
    return brut.common(limite)


def construire_fut():
    """Fut de la turbine : revolution du profil meridien."""
    L = LONGUEUR_HT
    R = RAYON_BELL
    p1 = Vector(R_VEINE, 0, 0)
    p2 = Vector(R_VEINE, 0, L - R)
    p3 = Vector(R_VEINE + R, 0, L)
    centre_arc = Vector(R_VEINE + R, 0, L - R)
    milieu_arc = centre_arc + Vector(-R * math.cos(math.pi / 4), 0,
                                     R * math.sin(math.pi / 4))
    p4 = Vector(R_LEVRE, 0, L)
    p5 = Vector(R_LEVRE, 0, L - HAUTEUR_LEVRE)
    p6 = Vector(R_FUT, 0, L - HAUTEUR_LEVRE - 1.2)
    p7 = Vector(R_FUT, 0, 0)

    aretes = [
        Part.makeLine(p1, p2),
        Part.Arc(p2, milieu_arc, p3).toShape(),
        Part.makeLine(p3, p4),
        Part.makeLine(p4, p5),
        Part.makeLine(p5, p6),
        Part.makeLine(p6, p7),
        Part.makeLine(p7, p1),
    ]
    face = Part.Face(Part.Wire(aretes))
    return face.revolve(ORIG, AXE_Z, 360.0)


def construire_stator():
    """Fut + aubes + moyeu arriere, en un seul solide."""
    solide = construire_fut()
    moyeu = Part.makeCylinder(R_MOY_AR, MOYEU_ARR_HAUT, ORIG, AXE_Z)
    conge = Part.makeCone(R_MOY_AR, R_MOYEU * 0.95, 1.5,
                          Vector(0, 0, MOYEU_ARR_HAUT), AXE_Z)
    solide = solide.fuse(moyeu).fuse(conge)

    aube = construire_aube()
    for i in range(NB_AUBES):
        copie = aube.copy()
        copie.rotate(ORIG, AXE_Z, 360.0 * i / NB_AUBES)
        solide = solide.fuse(copie)
    return solide.removeSplitter()


def construire_rotor():
    """Moyeu rotor + cone d'entree + pales."""
    moyeu = Part.makeCylinder(R_MOYEU, SPINNER_BASE - (MOYEU_ARR_HAUT + 1.7),
                              Vector(0, 0, MOYEU_ARR_HAUT + 1.7), AXE_Z)
    cone = Part.makeCone(R_MOYEU, 1.2, SPINNER_HAUT - SPINNER_BASE,
                         Vector(0, 0, SPINNER_BASE), AXE_Z)
    pointe = Part.makeSphere(1.2, Vector(0, 0, SPINNER_HAUT))
    solide = moyeu.fuse(cone).fuse(pointe)

    pale = construire_pale()
    for i in range(NB_PALES):
        copie = pale.copy()
        copie.rotate(ORIG, AXE_Z, 360.0 * i / NB_PALES)
        solide = solide.fuse(copie)
    return solide.removeSplitter()


def construire_faisceau():
    """Sortie des trois fils moteur, radiale, cote ejection."""
    depart = Vector(R_FUT - 2.0, 0, Z_FAISCEAU)
    return Part.makeCylinder(DIA_FAISCEAU / 2.0, LONG_FAISCEAU, depart,
                             Vector(1, 0, 0))


def construire_enveloppe():
    """Volume d'interdiction pour les controles d'interference."""
    corps = Part.makeCylinder(R_LEVRE + JEU_ENVELOPPE,
                              LONGUEUR_HT + 2 * JEU_ENVELOPPE,
                              Vector(0, 0, -JEU_ENVELOPPE), AXE_Z)
    couloir = Part.makeCylinder(DIA_FAISCEAU / 2.0 + 1.5, 26.0,
                                Vector(R_FUT - 2.0, 0, Z_FAISCEAU),
                                Vector(1, 0, 0))
    return corps.fuse(couloir).removeSplitter()


def construire_decoupes():
    """Deux outils booleens de decoupe pour la carte ou le chassis."""
    air = Part.makeCylinder(R_VEINE + JEU_DECOUPE, 12.0,
                            Vector(0, 0, -6.0), AXE_Z)
    traversante = Part.makeCylinder(R_FUT + JEU_DECOUPE, 12.0,
                                    Vector(0, 0, -6.0), AXE_Z)
    return air, traversante


# --------------------------------------------------------------------------
# Assemblage du document
# --------------------------------------------------------------------------

def ajouter(doc, nom, label, forme):
    obj = doc.addObject("Part::Feature", nom)
    obj.Label = label
    obj.Shape = forme
    return obj


def main():
    doc = App.newDocument(NOM)
    doc.Comment = (
        "Turbine EDF 27 mm - modele d'encombrement parametrique. "
        "Genere par turbineEDF27.py. Cotes AEO-RC POWER-X 27 mm : "
        "veine 27,4 / fut 29,7 / levre 36,7 / longueur 25,8 mm, 7 pales. "
        "Verifier au pied a coulisse sur la piece recue."
    )

    stator = ajouter(doc, "Stator", "Turbine EDF27 - fut et redresseur",
                     construire_stator())
    rotor = ajouter(doc, "Rotor", "Turbine EDF27 - rotor 7 pales",
                    construire_rotor())
    fils = ajouter(doc, "Faisceau", "Turbine EDF27 - sortie 3 fils",
                   construire_faisceau())
    ajouter(doc, "Enveloppe", "Turbine EDF27 - enveloppe d'interdiction",
            construire_enveloppe())
    air, traversante = construire_decoupes()
    ajouter(doc, "DecoupeAir", "Outil - decoupe passage d'air (turbine posee)",
            air)
    ajouter(doc, "DecoupeTraversante",
            "Outil - decoupe fut traversant (turbine encastree)", traversante)

    doc.recompute()

    piece = [stator, rotor, fils]
    doc.saveAs(os.path.join(ICI, NOM + ".fcstd"))
    Import.export(piece, os.path.join(ICI, NOM + ".step"))
    Mesh.export(piece, os.path.join(ICI, NOM + ".stl"))

    bb = stator.Shape.BoundBox.united(rotor.Shape.BoundBox)
    print("--- turbine EDF 27 mm ---")
    print("encombrement  X %.2f  Y %.2f  Z %.2f mm"
          % (bb.XLength, bb.YLength, bb.ZLength))
    print("z de %.2f a %.2f mm" % (bb.ZMin, bb.ZMax))
    print("volume stator %.0f mm3, rotor %.0f mm3"
          % (stator.Shape.Volume, rotor.Shape.Volume))
    print("solides valides : stator=%s rotor=%s"
          % (stator.Shape.isValid(), rotor.Shape.isValid()))
    print("fichiers ecrits dans %s" % ICI)


main()
