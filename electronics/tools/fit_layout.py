#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Controle et ajuste la table de placement (layout.py) hors pcbnew.

Donnees : /tmp/board_geom.json (tailles natives + polygone du contour ferme),
regenere par place_pcb.py a chaque pose.

Trois controles :
  - appartenance au polygone (marge 0.3 mm), 8 points par boite ;
  - collisions deux a deux (marge 0.05 mm par piece) ;
  - zones interdites : courtyards des equerres, trou de turbine (r 16 + 0.3).

Les violations sur pieces non figees sont resolues par petites poussees en
spirale (pas 0.5 mm, rayon 8 mm) ; le resultat va dans layout_fit.json que
place_pcb.py applique par-dessus la table.  --dry : controle seul.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from layout import (P, LOCKED, ROUND, PAIR_OK, OVERHANG, TURBINE, MCU,
                    TURBINE_XY, TURBINE_BCD, TURBINE_VIS)

geom = json.load(open('/tmp/board_geom.json'))
SIZES, POLY = geom['sizes'], geom['poly']
# tailles surchargees : la bbox native inclut serigraphie et gabarits Fab
for h in ('H501', 'H521', 'H541'):
    SIZES[h] = (0.5, 0.5, 0, 0)          # sans courtyard : trou seul
SIZES['J601'] = (10.4, 2.6, 0, -10.85)   # OLED : seule l embase compte,
                                         # le module est sur entretoises
                                         # (rangee de broches a 1,5 du bord haut)
# Le LQFP100 a 45 deg etait traite comme un losange en norme L1 : une
# approximation qui, faute de savoir ou est le sommet et ou est la face,
# inventait des collisions (le trou de turbine a 33 mm passait pour une
# penetration de 2 mm). C'est un carre tourne, donc un rectangle oriente
# comme les autres : meme test SAT, exact cette fois.
DIAMOND = {}
# Les trois stations de telemetrie sont de grands rectangles poses en biais
# (15 / 45 / 75 deg). Les traiter par leur boite englobante droite, c'est leur
# preter 27 x 27 mm la ou elles en font 20 x 19 : le controle voyait des
# collisions avec la moitie de l'epaule et refusait toute position tenable.
# Elles sont donc modelisees par leur rectangle REEL, oriente (test SAT).
OBB = {'TM501', 'TM521', 'TM541', 'U201'}
# Les deux ensembles moteur SONT les equerres : ils debordent de la carte par
# construction (roue comprise) et ne peuvent pas se reprocher leur propre
# zone interdite.
KEEPOUT_FREE = {'M1', 'M2'}
MARGIN_EDGE, MARGIN_PAIR = 0.3, 0.05
# Zones interdites : courtyards des deux equerres moteur, puis les quatre
# percages du module OLED - ils sont sous l ecran, la ou le decouplage du MCU
# vient justement se loger, donc ils comptent.
JX, JY = P['J601'][0], P['J601'][1]
OLED_HX, OLED_HY = 27.0 / 2 - 2.0, 24.7 / 2 - 2.0      # cf. tools/gen_fp.py
# Courtyard des deux ensembles moteur, DEDUIT de l empreinte et de la position
# reelle de M1/M2 au lieu d etre recopie a la main : la table portait encore
# (96,2 .. 142,6) alors que l empreinte Motor_Faulhaber_1524_15-10 s arrete a
# 135,05 - 7,5 mm de carte declares interdits pour rien de chaque cote.
MOTOR_CRTYD = (-11.25, -16.25, 11.25, 30.05)      # F.CrtYd du .kicad_mod


def motor_keepout(ref):
    x, y, rot, _ = P[ref]
    r = math.radians(rot % 360)
    c, si = math.cos(r), math.sin(r)
    xs, ys = [], []
    for lx in (MOTOR_CRTYD[0], MOTOR_CRTYD[2]):
        for ly in (MOTOR_CRTYD[1], MOTOR_CRTYD[3]):
            xs.append(x + lx * c + ly * si)
            ys.append(y - lx * si + ly * c)
    return (min(xs), min(ys), max(xs), max(ys))


KEEPOUTS = [motor_keepout(m) for m in ('M1', 'M2') if m in P]
# Les trois vis M2 de la turbine : NPTH dia 2,2 hors du courtyard de la
# levre, donc invisibles pour le test au rayon. Il faut les declarer.
R_VIS_TURBINE = 1.6                        # 1,1 de percage + 0,5 de garde
for _a in TURBINE_VIS:
    _vx = TURBINE_XY[0] + TURBINE_BCD / 2 * math.cos(math.radians(_a))
    _vy = TURBINE_XY[1] + TURBINE_BCD / 2 * math.sin(math.radians(_a))
    KEEPOUTS.append((_vx - R_VIS_TURBINE, _vy - R_VIS_TURBINE,
                     _vx + R_VIS_TURBINE, _vy + R_VIS_TURBINE))
KEEPOUTS += [(JX + sx * OLED_HX - 1.6, JY + sy * OLED_HY - 1.6,
              JX + sx * OLED_HX + 1.6, JY + sy * OLED_HY + 1.6)
             for sx in (-1, 1) for sy in (-1, 1)]
TURBINE = (TURBINE[0], TURBINE[1], TURBINE[2] + 0.05)   # courtyard deja marge

def bbox(ref, x, y, rot, side):
    w, h, cx, cy = SIZES.get(ref, (2.0, 2.0, 0, 0))
    if side == 'B':
        cy = -cy
    r = math.radians(rot % 360)
    c, s = abs(math.cos(r)), abs(math.sin(r))
    ox = cx * math.cos(r) + cy * math.sin(r)
    oy = -cx * math.sin(r) + cy * math.cos(r)
    hw, hh = (w * c + h * s) / 2, (w * s + h * c) / 2
    return (x + ox - hw, y + oy - hh, x + ox + hw, y + oy + hh)

def inside(px, py):
    hit, n = False, len(POLY)
    for i in range(n):
        x1, y1 = POLY[i]
        x2, y2 = POLY[(i + 1) % n]
        if (y1 > py) != (y2 > py) and px < x1 + (py - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit

def off_board(ref, geo):
    if ref in OBB:                        # coins et milieux du rectangle penche
        return not all(inside(px, py) for px, py in obb_pts(geo, MARGIN_EDGE))
    if ref in ROUND:                      # points sur le cercle, pas les coins
        cx, cy, r = geo
        r += MARGIN_EDGE
        pts = [(cx + r * math.cos(a * math.pi / 4),
                cy + r * math.sin(a * math.pi / 4)) for a in range(8)]
        return not all(inside(px, py) for px, py in pts)
    x1, y1, x2, y2 = geo
    x1 -= MARGIN_EDGE; y1 -= MARGIN_EDGE; x2 += MARGIN_EDGE; y2 += MARGIN_EDGE
    xm, ym = (x1 + x2) / 2, (y1 + y2) / 2
    pts = ((x1, y1), (x2, y1), (x1, y2), (x2, y2), (xm, y1), (xm, y2),
           (x1, ym), (x2, ym))
    return not all(inside(px, py) for px, py in pts)

def rects_gap(a, b):
    return max(b[0] - a[2], a[0] - b[2], b[1] - a[3], a[1] - b[3])


def obb_of(ref, x, y, rot, side):
    """('obb', cx, cy, hw, hh, ux, uy) : rectangle oriente, axe u = grand cote."""
    w, h, cx, cy = SIZES.get(ref, (2.0, 2.0, 0, 0))
    if side == 'B':
        cy = -cy
    r = math.radians(rot % 360)
    ox = cx * math.cos(r) + cy * math.sin(r)
    oy = -cx * math.sin(r) + cy * math.cos(r)
    return ('obb', x + ox, y + oy, w / 2.0, h / 2.0,
            math.cos(r), -math.sin(r))


def obb_axes(g):
    ux, uy = g[5], g[6]
    return ((ux, uy, g[3]), (-uy, ux, g[4]))


def obb_pts(g, grow=0.0):
    _, cx, cy, hw, hh, ux, uy = g
    hw += grow; hh += grow
    return [(cx + sx * hw * ux - sy * hh * uy, cy + sx * hw * uy + sy * hh * ux)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1),
                           (0, -1), (0, 1), (-1, 0), (1, 0))]


def _proj(pts, ax, ay):
    v = [px * ax + py * ay for px, py in pts]
    return min(v), max(v)


def obb_gap(a, b):
    """Distance separant deux convexes (negatif = penetration), par SAT.

    `a` est un OBB ; `b` un OBB ou une boite droite (x1, y1, x2, y2).
    """
    pa = obb_pts(a)[:4]
    if isinstance(b, tuple) and b and b[0] == 'obb':
        pb = obb_pts(b)[:4]
        axes = [(x, y) for x, y, _ in obb_axes(a)] + \
               [(x, y) for x, y, _ in obb_axes(b)]
    else:
        pb = [(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])]
        axes = [(x, y) for x, y, _ in obb_axes(a)] + [(1.0, 0.0), (0.0, 1.0)]
    best = -1e9
    for ax, ay in axes:
        a0, a1 = _proj(pa, ax, ay)
        b0, b1 = _proj(pb, ax, ay)
        g = max(b0 - a1, a0 - b1)
        best = max(best, g)
    return best


def obb_circ_gap(a, cx, cy, r):
    pts = obb_pts(a)[:4]
    axes = [(x, y) for x, y, _ in obb_axes(a)]
    best = -1e9
    for ax, ay in axes:
        a0, a1 = _proj(pts, ax, ay)
        c = cx * ax + cy * ay
        best = max(best, max(c - r - a1, a0 - c - r))
    d = math.hypot(cx - a[1], cy - a[2])          # axe centre-centre
    _, cxs, cys, hw, hh, ux, uy = a
    if d > 1e-9:
        ax, ay = (cx - cxs) / d, (cy - cys) / d
        a0, a1 = _proj(pts, ax, ay)
        c = cx * ax + cy * ay
        best = max(best, max(c - r - a1, a0 - c - r))
    return best

def circ_rect_gap(cx, cy, r, b):
    dx = max(b[0] - cx, 0, cx - b[2])
    dy = max(b[1] - cy, 0, cy - b[3])
    return math.hypot(dx, dy) - r

SIDE = {r: v[3] for r, v in P.items()}

def clashes(ref, geo, others):
    """geo: bbox ou (cx, cy, r). Retourne la liste des conflits (meme face)."""
    out = []
    rnd = ref in ROUND
    for o, og in others.items():
        if o == ref or SIDE.get(o) != SIDE.get(ref):
            continue
        if frozenset((o, ref)) in PAIR_OK:
            continue
        ornd = o in ROUND
        if ref in OBB or o in OBB:
            a, other = (geo, og) if ref in OBB else (og, geo)
            if len(other) == 3:                     # cercle
                g = obb_circ_gap(a, *other)
            elif isinstance(other, tuple) and other and other[0] == 'obb':
                g = obb_gap(a, other)
            elif (ref in DIAMOND or o in DIAMOND):
                # losange du LQFP : son cercle inscrit, conservatif
                d = DIAMOND.get(ref) or DIAMOND[o]
                c = ((other[0] + other[2]) / 2, (other[1] + other[3]) / 2)
                g = obb_circ_gap(a, c[0], c[1], d / 1.415)
            else:
                g = obb_gap(a, other)
        elif ref in DIAMOND or o in DIAMOND:
            # losange contre boite : distance L1 du centre a la boite
            if ref in DIAMOND:
                dc, dr, other = geo, DIAMOND[ref], og
            else:
                dc, dr, other = og, DIAMOND[o], geo
            ctr = (dc[0], dc[1]) if len(dc) == 3 else \
                  ((dc[0] + dc[2]) / 2, (dc[1] + dc[3]) / 2)
            if len(other) == 3:          # cercle : conservatif en L1
                g = (abs(other[0] - ctr[0]) + abs(other[1] - ctr[1])
                     - dr - other[2] * 1.415)
            else:
                dx = max(other[0] - ctr[0], 0, ctr[0] - other[2])
                dy = max(other[1] - ctr[1], 0, ctr[1] - other[3])
                g = dx + dy - dr
        elif rnd and ornd:
            g = math.hypot(geo[0] - og[0], geo[1] - og[1]) - geo[2] - og[2]
        elif rnd:
            g = circ_rect_gap(*geo, og)
        elif ornd:
            g = circ_rect_gap(*og, geo)
        else:
            g = rects_gap(geo, og)
        if g < 2 * MARGIN_PAIR:
            out.append((o, round(g, 2)))
    return out

def keepout_bad(ref, geo):
    if ref in KEEPOUT_FREE:
        return None
    rnd = ref in ROUND
    obb = ref in OBB
    dia = DIAMOND.get(ref)
    for k in KEEPOUTS:
        if obb:
            g = obb_gap(geo, k)
        elif rnd:
            g = circ_rect_gap(geo[0], geo[1], geo[2], k)
        elif dia:
            # losange : distance L1 du centre a la boite
            ctr = ((geo[0] + geo[2]) / 2, (geo[1] + geo[3]) / 2)
            g = (max(k[0] - ctr[0], 0, ctr[0] - k[2])
                 + max(k[1] - ctr[1], 0, ctr[1] - k[3]) - dia)
        else:
            g = rects_gap(geo, k)
        if g < 0:
            return f'equerre ({g:.2f})'
    if obb:
        g = obb_circ_gap(geo, *TURBINE)
    elif rnd:
        g = math.hypot(geo[0] - TURBINE[0], geo[1] - TURBINE[1]) - geo[2] - TURBINE[2]
    elif dia:
        ctr = ((geo[0] + geo[2]) / 2, (geo[1] + geo[3]) / 2)
        g = (abs(ctr[0] - TURBINE[0]) + abs(ctr[1] - TURBINE[1])
             - dia - TURBINE[2] * 1.415)
    else:
        g = circ_rect_gap(TURBINE[0], TURBINE[1], TURBINE[2], geo)
    if g < 0:
        return f'turbine ({g:.2f})'
    return None

def geo_of(ref, x, y, rot, side):
    if ref in OBB:
        return obb_of(ref, x, y, rot, side)
    if ref in ROUND:
        w, h, cx, cy = SIZES.get(ref, (0, 0, 0, 0))
        if side == 'B':
            cy = -cy
        r = math.radians(rot % 360)
        ox = cx * math.cos(r) + cy * math.sin(r)
        oy = -cx * math.sin(r) + cy * math.cos(r)
        return (x + ox, y + oy, ROUND[ref])
    return bbox(ref, x, y, rot, side)

def all_geo(table):
    return {r: geo_of(r, *v) for r, v in table.items()}

def violations(table, geos, only=None):
    out = {}
    refs = only if only is not None else table
    for ref in refs:
        x, y, rot, side = table[ref]
        geo = geos[ref]
        probs = []
        if ref not in OVERHANG and off_board(ref, geo):
            probs.append('hors contour')
        k = keepout_bad(ref, geo)
        if k:
            probs.append(k)
        for o, g in clashes(ref, geo, geos):
            probs.append(f'chevauche {o} ({g})')
        if probs:
            out[ref] = probs
    return out

def try_fix(table, geos, ref, step=0.5, reach=16):
    x, y, rot, side = table[ref]
    steps = sorted({(i * step, j * step) for i in range(-reach, reach + 1)
                    for j in range(-reach, reach + 1)},
                   key=lambda d: (d[0] * d[0] + d[1] * d[1]))
    for dx, dy in steps[1:]:
        nx, ny = x + dx, y + dy
        geo = geo_of(ref, nx, ny, rot, side)
        if ref not in OVERHANG and off_board(ref, geo):
            continue
        if keepout_bad(ref, geo):
            continue
        if clashes(ref, geo, {o: g for o, g in geos.items() if o != ref}):
            continue
        table[ref] = (nx, ny, rot, side)
        geos[ref] = geo
        return True
    return False

def main():
    table = dict(P)
    geos = all_geo(table)
    bad = violations(table, geos)
    print(f'controle initial : {len(bad)} pieces en defaut')
    if '--dry' not in sys.argv:
        for _pass in range(6):
            bad = violations(table, geos)
            movable = [r for r in bad if r not in LOCKED]
            if not movable:
                break
            fixed = 0
            for ref in sorted(movable):
                if try_fix(table, geos, ref) or \
                   try_fix(table, geos, ref, step=0.25, reach=12):
                    fixed += 1
            print(f'passe {_pass + 1} : {len(movable)} a corriger, {fixed} deplacees')
            if not fixed:
                break
        bad = violations(table, geos)
        moved = {r: [round(table[r][0], 2), round(table[r][1], 2)]
                 for r in table if table[r][:2] != P[r][:2]}
        json.dump(moved, open(os.path.join(HERE, 'layout_fit.json'), 'w'),
                  indent=0, sort_keys=True)
        print(f'{len(moved)} ajustements -> layout_fit.json')
    if bad:
        print(f'\n{len(bad)} pieces encore en defaut :')
        for ref in sorted(bad):
            tag = ' [FIGEE]' if ref in LOCKED else ''
            print(f'  {ref:6s}{tag} : ' + ' ; '.join(bad[ref][:4]))
    else:
        print('aucun defaut')

if __name__ == '__main__':
    main()
