#!/usr/bin/env python3
"""Ajoute les entites de couleur AP214 a un fichier STEP qui n'en a pas.

KiCad 10 n'utilise plus que du STEP : la couleur doit etre portee par le
fichier lui-meme (COLOUR_RGB + STYLED_ITEM), comme dans les modeles livres
avec KiCad. FreeCAD en mode console ne sait pas les ecrire (pas de ViewObject),
d'ou ce post-traitement.

    python3 colorize_step.py            # recolorise tout le dossier 3d/
"""
import re, sys, os

PALETTE = {
    "GM12-N20_bracket":        (0.93, 0.93, 0.91),  # ABS blanc
    "GM12-N20_motor_encoder":  (0.16, 0.18, 0.20),  # bloc encodeur sombre
    "GM12-N20_motor_can":      (0.66, 0.68, 0.70),  # carter nickele
    "GM12-N20_motor_gearbox":  (0.72, 0.60, 0.35),  # reducteur laiton
    "Pololu_wheel_40x7_hub":   (0.95, 0.95, 0.95),  # moyeu plastique blanc
    "Pololu_wheel_40x7_tire":  (0.11, 0.11, 0.12),  # gomme silicone noire
}
ITEMS = r'(?:MANIFOLD_SOLID_BREP|SHELL_BASED_SURFACE_MODEL|BREP_WITH_VOIDS|FACETED_BREP)'
REPRS = (r'(?:ADVANCED_BREP_SHAPE_REPRESENTATION|MANIFOLD_SURFACE_SHAPE_REPRESENTATION'
         r'|GEOMETRICALLY_BOUNDED_SURFACE_SHAPE_REPRESENTATION|SHAPE_REPRESENTATION)')

def colorize(path, rgb):
    txt = open(path, encoding='latin-1').read()
    if 'COLOUR_RGB' in txt:
        return "deja colore"
    nxt = max(int(x) for x in re.findall(r'#(\d+)\s*=', txt)) + 1
    m = re.search(r'#(\d+)\s*=\s*' + REPRS + r'\s*\((.*?)\)\s*;', txt, re.S)
    if not m:
        return "ERREUR: pas de shape representation"
    ctx = re.findall(r'#(\d+)', m.group(2))[-1]
    items = re.findall(r'#(\d+)\s*=\s*' + ITEMS + r'\s*\(', txt)
    if not items:
        return "ERREUR: aucun item stylable"
    r, g, b = rgb
    L = []
    c0 = nxt
    L.append("#%d = COLOUR_RGB('',%.9f,%.9f,%.9f);" % (c0, r, g, b))
    L.append("#%d = FILL_AREA_STYLE_COLOUR('',#%d);" % (c0+1, c0))
    L.append("#%d = FILL_AREA_STYLE('',(#%d));" % (c0+2, c0+1))
    L.append("#%d = SURFACE_STYLE_FILL_AREA(#%d);" % (c0+3, c0+2))
    L.append("#%d = SURFACE_SIDE_STYLE('',(#%d));" % (c0+4, c0+3))
    L.append("#%d = SURFACE_STYLE_USAGE(.BOTH.,#%d);" % (c0+5, c0+4))
    L.append("#%d = PRESENTATION_STYLE_ASSIGNMENT((#%d));" % (c0+6, c0+5))
    sid, styled = c0+7, []
    for it in items:
        L.append("#%d = STYLED_ITEM('color',(#%d),#%s);" % (sid, c0+6, it))
        styled.append("#%d" % sid); sid += 1
    L.append("#%d = MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',(%s),#%s);"
             % (sid, ",".join(styled), ctx))
    i = txt.rstrip().rfind('ENDSEC;')
    out = txt[:i] + "\n".join(L) + "\n" + txt[i:]
    open(path, 'w', encoding='latin-1').write(out)
    return "%d item(s) colore(s) en (%.2f, %.2f, %.2f)" % (len(items), r, g, b)

if __name__ == "__main__":
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "3d")
    for name, rgb in sorted(PALETTE.items()):
        p = os.path.join(d, name + ".step")
        print("%-28s %s" % (name, colorize(p, rgb) if os.path.exists(p) else "ABSENT"))
