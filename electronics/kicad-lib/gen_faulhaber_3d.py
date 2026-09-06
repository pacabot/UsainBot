#!/usr/bin/env python3
"""Modeles STEP de la motorisation Faulhaber, places dans le repere de l'empreinte.

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd gen_faulhaber_3d.py

Trois sources differentes, traitees differemment :

  moteur, reducteur  STEP officiels Faulhaber de 3d/vendor/, seulement transposes
                     dans le repere de l'empreinte (rotation + translation). Aucune
                     retouche de forme, sauf la coupe des fils du moteur nu que le
                     codeur remplace par sa nappe.
  codeur             reconstruit : Faulhaber ne publie pas de STEP pour l'IE2.
                     Enveloppe seule (Ø15 x 1,4 mm) et amorce de nappe.
  roue               reconstruite d'apres les cotes publiees par JSumo. JSumo ne
                     publie pas de CAO. Le decoupage interne du moyeu est plausible,
                     pas releve : il est cale pour retrouver les 17,7 g annonces.

Passage du repere Faulhaber (axe suivant Z, arbre vers +Z, face de sortie du
reducteur a Z=0) au repere de l'empreinte : rotation de +90 deg autour de X, puis
translation de (0, Y_FACE, AXIS_Z). Le moteur subit d'abord -ASSY_OFFSET en Z,
qui l'emmanche dans le reducteur. L'ecriture du STEP applique un dernier miroir
en Y : le repere des modeles 3D de KiCad a son Y inverse par rapport a celui de
l'empreinte. Les cotes affichees ci-dessous restent, elles, dans le repere de
l'empreinte, comparables telles quelles a faulhaber_geom.py.
"""
import os, sys, math
import FreeCAD as App
import Part
from FreeCAD import Vector, Rotation, Placement

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import faulhaber_geom as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "3d")
VENDOR = os.path.join(OUT, "vendor")

# rotation qui amene l'axe Z du repere Faulhaber sur -Y de l'empreinte
TO_FOOTPRINT = Rotation(Vector(1, 0, 0), 90)
ORIGIN = Vector(0, G.Y_FACE, G.AXIS_Z)


# repere de l'empreinte -> repere des modeles 3D de KiCad, dont le Y est inverse
MIRROR_Y = App.Matrix()
MIRROR_Y.A22 = -1.0


def export(shape):
    """Retourne la piece dans le repere des modeles 3D de KiCad.

    Le repere des modeles 3D de KiCad a son Y inverse par rapport a celui de
    l'empreinte. Sans ce retournement, une empreinte tournee de +/-90 deg affiche
    ses modeles cote pour cote : arbre et roue partent du mauvais bord de la carte.
    Les modeles N20, qui viennent de Waveshare, respectent deja cette convention.

    transformShape, et ni mirror() ni transformGeometry. mirror(), sur une forme qui
    porte un Placement, travaille dans le repere local puis reapplique le placement :
    elle deplace la piece au lieu de la retourner. transformGeometry, lui, convertit
    cylindres et cercles en NURBS — volume juste, mais boite englobante surestimee,
    et c'est une BoundBox que check_faulhaber_assembly.py lit pour la garde au sol.
    Le placement est fige d'abord, sans quoi le miroir ne porterait que sur la
    geometrie sous-jacente.
    """
    s = shape.copy()
    m = s.Placement.toMatrix()
    s.Placement = App.Placement()
    s.transformShape(m)                        # fige le placement dans la geometrie
    s.transformShape(MIRROR_Y, False, False)   # miroir exact, cylindres conserves
    return s


def place(shape, extra_z=0.0):
    """Repere Faulhaber -> repere empreinte. extra_z decale avant rotation."""
    s = shape.copy()
    if extra_z:
        s.translate(Vector(0, 0, extra_z))
    s.Placement = Placement(ORIGIN, TO_FOOTPRINT).multiply(s.Placement)
    return s


def save(shape, name):
    if not shape.isValid():
        raise RuntimeError(f"{name} : solide invalide, export refuse")
    path = os.path.join(OUT, name + ".step")
    export(shape).exportStep(path)
    bb = shape.BoundBox
    vol = sum(s.Volume for s in shape.Solids) / 1000.0
    print(f"  {name:<32} X {bb.XMin:7.2f}..{bb.XMax:7.2f}  "
          f"Y {bb.YMin:7.2f}..{bb.YMax:7.2f}  Z {bb.ZMin:6.2f}..{bb.ZMax:6.2f}  "
          f"{vol:6.2f} cm3")
    return vol


def read(name):
    s = Part.Shape()
    s.read(os.path.join(VENDOR, name))
    return s


print("Modeles Faulhaber transposes :")

# ---------------------------------------------------------------- reducteur 15/10
# Version a paliers frittes, celle qui est en main. Le STEP de la version K a
# roulements reste dans vendor/ : basculer GEAR_STEP dans faulhaber_geom.py suffit
# a changer de variante, la portee de centrage et le debut de l'arbre suivent.
gear = place(read(G.GEAR_STEP))
save(gear, "Faulhaber_15-10_gearhead")

# ---------------------------------------------------------------- moteur 1524T006SR
# Les quatre fils du moteur nu (Ø0,8 sortant en Z < -1) disparaissent avec le codeur,
# qui apporte sa propre nappe : on tronque le solide a l'arriere du corps.
motor = read("1524T_SR.stp")
body = Part.makeBox(40, 40, 60, Vector(-20, -20, -1.0))
motor = motor.common(body)
motor = place(motor, -G.ASSY_OFFSET)
save(motor, "Faulhaber_1524_motor")

# ---------------------------------------------------------------- codeur IE2-1024
z_enc = -G.ASSY_OFFSET - 1.0                       # arriere du corps moteur
enc = Part.makeCylinder(G.ENC_D / 2, G.ENC_L, Vector(0, 0, z_enc - G.ENC_L))
ribbon = Part.makeBox(G.ENC_RIBBON_W, G.ENC_RIBBON_T, 7.0,
                      Vector(-G.ENC_RIBBON_W / 2, -G.ENC_RIBBON_T / 2,
                             z_enc - G.ENC_L - 7.0))
enc = enc.fuse(ribbon)
enc = place(enc)
save(enc, "Faulhaber_IE2-1024_encoder")

# ---------------------------------------------------------------- roue JSumo JS4311
# Moyeu : jante + voile + bossage, allege par six trous. Les proportions internes
# sont un choix, calé sur la masse annoncee (17,7 g roue complete).
r_out, r_in = G.TIRE_ID / 2, G.TIRE_ID / 2 - 2.0   # jante Ø35, paroi 2 mm
hub = Part.makeCylinder(r_out, G.WHEEL_W, Vector(0, 0, 0))
hub = hub.cut(Part.makeCylinder(r_in, G.WHEEL_W, Vector(0, 0, 0)))
web = Part.makeCylinder(r_in, 3.2, Vector(0, 0, G.WHEEL_W / 2 - 1.60))
boss = Part.makeCylinder(4.5, G.WHEEL_W, Vector(0, 0, 0))
hub = hub.fuse(web).fuse(boss)
for i in range(6):                                  # allegements Ø4,5 sur Ø23
    a = math.radians(60 * i)
    hub = hub.cut(Part.makeCylinder(
        2.25, G.WHEEL_W, Vector(11.5 * math.cos(a), 11.5 * math.sin(a), 0)))
hub = hub.cut(Part.makeCylinder(G.WHEEL_BORE / 2, G.WHEEL_W, Vector(0, 0, 0)))
# vis de pression M4 radiale
hub = hub.cut(Part.makeCylinder(2.0, 6.0, Vector(0, 0, G.WHEEL_W / 2),
                                Vector(0, 1, 0)))

tire = Part.makeCylinder(G.WHEEL_D / 2, G.TIRE_W,
                         Vector(0, 0, (G.WHEEL_W - G.TIRE_W) / 2))
tire = tire.cut(Part.makeCylinder(G.TIRE_ID / 2, G.TIRE_W,
                                  Vector(0, 0, (G.WHEEL_W - G.TIRE_W) / 2)))

# la roue est emmanchee sur l'arbre, face externe a 0,2 mm du bout
z_wheel = G.SHAFT_TIP - 0.2 - G.WHEEL_W
hub = place(hub, z_wheel)
tire = place(tire, z_wheel)
v_hub = save(hub, "JSumo_JS4311_hub")
v_tire = save(tire, "JSumo_JS4311_tire")

m = v_hub * 2.70 + v_tire * 1.15                    # aluminium + silicone
print(f"\n  masse reconstruite de la roue : {m:.1f} g   (JSumo annonce 17,7 g)")
print(f"  ecart {100 * (m - 17.7) / 17.7:+.0f} %"
      "  — ajuster TIRE_ID ou l'evidement du moyeu si besoin")
print("\nPenser a relancer  python3 colorize_step.py")
