# -*- coding: utf-8 -*-
"""Couleurs AP214 injectees dans un STEP apres coup.

FreeCAD en mode console n a pas de `ViewObject` : son export STEP sort sans
la moindre couleur, et KiCad 10 ne lit plus que du STEP. Le detour est donc
toujours le meme : exporter la geometrie, puis coudre a la main les entites
COLOUR_RGB / STYLED_ITEM sur chaque solide, en le reconnaissant par le nom
du PRODUCT (le Label de l objet FreeCAD).

Le meme code vit dans `mechanics/telemetry_duo.py` et `mechanics/oled096_i2c.py`,
qui sont autonomes par construction (on les lance dans FreeCAD, pas dans
l arborescence du projet) ; ici il sert aux boitiers de composants.

    from step_colors import injecter_couleurs_step
    injecter_couleurs_step('3d/AMASS_XT30U-M.step',
                           {'Corps': (0.95, 0.78, 0.10)},
                           {'Corps': 0.0})
"""

import re

TRANSPARENCES = {}


def injecter_couleurs_step(chemin, couleurs, transparences=None):
    TRANSPARENCES = transparences or {}
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
