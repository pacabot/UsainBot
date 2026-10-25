#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regles de routage d UsainBot : largeurs, isolations, vias, impedance.

Calcul seul (Python + NumPy/SciPy) :
    python3 routing_rules.py            -> ../routing-rules/rules.json + tables
Calcul puis application au projet (edition texte/JSON, sans pcbnew) :
    python3 routing_rules.py --apply    -> .kicad_pro, .kicad_dru, stackup PCB

Toutes les entrees sont en tete de fichier, avec leur provenance.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

HERE = Path(__file__).resolve().parent
PRJ = HERE.parent
OUT = PRJ / 'routing-rules'

# ------------------------------------------------------------ empilage
# JLCPCB JLC04161H-3313, page https://jlcpcb.com/impedance relue le
# 13/09/2026 : cuivre externe 35 um (1 oz), interne 15,2 um (0,5 oz),
# preimpregne 3313 x1 = 0,0994 mm er 4,1, coeur 1,3 mm cuivre compris er 4,6.
# Retenu plutot que 7628 : 0,1 mm entre F.Cu et le plan de masse In1 tient
# les boucles des ponts et des convertisseurs courtes, et les paires USB a
# des largeurs compatibles avec les pastilles 0,3 mm du connecteur.
CU_OUT = 0.035
CU_IN = 0.0152
PREPREG = 0.0994
ER_PREPREG = 4.1
CORE = 1.3 - 2 * CU_IN
ER_CORE = 4.6
MASK = 0.010
ER_MASK = 3.3
VIA_PLATING = 0.018   # epaisseur minimale de metallisation supposee (a
                      # confirmer : JLCPCB annonce une moyenne, pas un min)
RHO_CU = 1.724e-8     # ohm.m a 20 C
ALPHA_CU = 0.00393

# ------------------------------------------------------------ IPC-2221B
# I = k * dT^0.44 * A^0.725, A en mil^2 ; k = 0,048 externe, 0,024 interne.
# Plus severe que IPC-2152 pour une carte 1,6 mm avec plans : marge implicite.
def area_mil2(i, dt, k):
    return (i / (k * dt ** 0.44)) ** (1 / 0.725)


def width_mm(i, dt, external=True):
    k, t = (0.048, CU_OUT) if external else (0.024, CU_IN)
    a = area_mil2(i, dt, k) * (0.0254 ** 2)      # mm^2
    return a / t


def via_current(drill, dt, plating=VIA_PLATING):
    """Courant d un fut de via, traite comme conducteur interne (prudent)."""
    a_mm2 = math.pi * (drill + plating) * plating
    a_mil2 = a_mm2 / (0.0254 ** 2)
    return 0.024 * dt ** 0.44 * a_mil2 ** 0.725


def r_per_10mm(w, t=CU_OUT, temp=45.0):
    rho = RHO_CU * (1 + ALPHA_CU * (temp - 20))
    return rho * 0.010 / (w * 1e-3 * t * 1e-3)


# ------------------------------------------------------------ courants
# Chaque courant est deduit d un composant du schema ou d une donnee
# utilisateur ; "cont" dimensionne, "pic" est verifie.
CURRENTS = {
    'PACK': dict(cont=15.5, pic=18.5, src=(
        'mr30-review : ESC 12 A cont./15 A pic + 2 x 1 A moteurs + 1,5 A '
        'electronique. J102 -> J103 (ESC) et J102 -> F101.')),
    'VBAT': dict(cont=7.5, pic=12.0, src=(
        'Branche fusible F101 12 A : 2 x ITRIP 3,0 A (DRV8874, VREF 1,34 V, '
        'RIPROPI 1 k) + 1,5 A electronique. Le fusible borne le pic.')),
    'MOTEUR': dict(cont=3.0, pic=6.0, src=(
        'ITRIP = 1,34 V / (450 uA/A x 1 k) = 3,0 A regule par le DRV8874 ; '
        '6 A = seuil de protection OCP du DRV8874. Reel : 1 A.')),
    'CHARGE': dict(cont=3.0, pic=4.0, src=(
        'BQ25887 : IIN = KILIM / 383 R ~ 2,4 A + ondulation ; L101 4 A.')),
    'BUCK': dict(cont=2.0, pic=3.0, src=(
        'TPS62933 : sortie 3,3 V / 2 A retenue au schema, 3 A max, L102 3 A.')),
    '3V3': dict(cont=1.0, pic=2.0, src=(
        'Distribution +3V3 : ~0,5 A estimes (MCU, bancs IR 126 mA pulses, '
        'laser 3 x 12 mA, OLED, BLE), largeur pour 1 A.')),
    'FAIBLE': dict(cont=0.3, pic=0.5, src=(
        'Bancs IR 6 x 21 mA = 126 mA, lasers 12 mA, buzzer, +3V3_BLE, '
        'equilibrage PACK_MID 88 mA, 3V3A.')),
}

# ------------------------------------------------------------ isolations
# IPC-2221B tableau 6-1, 0-15 V (VPACK 8,4 V, VBUS 5 V, tout le reste 3,3 V)
IPC_CLEAR = {'B1 interne': 0.05, 'B2 externe nu': 0.10,
             'B4 externe vernis (masque)': 0.05, 'A6 pattes composant nues': 0.13,
             'A7 pattes composant vernies': 0.13}
FAB_MIN = 0.09        # JLCPCB 4 couches : piste/espace minimum 3,5 mil
DEFAULT_CLEAR = 0.15  # 0,13 IPC A6 arrondi, > minimum fabricant

# ------------------------------------------------------------ impedance
def solve_cs(w, t, h, er_sub, gap=None, mask=MASK, er_mask=ER_MASK,
             dx=0.01, dy=0.005, er_on=True):
    """Solveur de Laplace 2D en differences finies, microruban sur plan.

    Retourne la capacite lineique (F/m) du mode impair si gap est donne
    (conducteurs a +1/-1 V), sinon d un conducteur unique a 1 V.
    """
    span = (2 * w + (gap or 0)) + 30 * h
    top = h + t + mask + 15 * h
    nx, ny = int(span / dx), int(top / dy)
    x = (np.arange(nx) - nx / 2) * dx
    y = np.arange(ny) * dy
    X, Y = np.meshgrid(x, y, indexing='ij')
    eps = np.ones((nx, ny))
    if er_on:
        eps[:, y < h] = er_sub
        # masque : couche conforme d epaisseur mask au-dessus du substrat
        eps[(Y >= h) & (Y < h + mask)] = er_mask
    fixed = np.zeros((nx, ny), bool)
    V = np.zeros((nx, ny))
    fixed[:, 0] = True
    fixed[:, -1] = True
    fixed[0, :] = True
    fixed[-1, :] = True
    ylay = (Y >= h) & (Y < h + t)
    if gap is None:
        c1 = ylay & (np.abs(X) <= w / 2)
        fixed |= c1
        V[c1] = 1.0
    else:
        xc = (w + gap) / 2
        c1 = ylay & (np.abs(X - xc) <= w / 2)
        c2 = ylay & (np.abs(X + xc) <= w / 2)
        fixed |= c1 | c2
        V[c1] = 1.0
        V[c2] = -1.0
        if er_on:
            eps[(Y >= h + t) & (Y < h + t + mask) &
                ((np.abs(X - xc) <= w / 2 + mask) |
                 (np.abs(X + xc) <= w / 2 + mask))] = er_mask
    if er_on and gap is None:
        eps[(Y >= h + t) & (Y < h + t + mask) & (np.abs(X) <= w / 2 + mask)] = er_mask
    idx = -np.ones((nx, ny), int)
    free = ~fixed
    idx[free] = np.arange(free.sum())
    # permittivites aux faces (moyennes)
    ex = 0.5 * (eps[1:, :] + eps[:-1, :])   # face i+1/2
    ey = 0.5 * (eps[:, 1:] + eps[:, :-1])
    rows, cols, vals = [], [], []
    b = np.zeros(free.sum())
    I, J = np.nonzero(free)
    k = idx[I, J]
    diag = np.zeros(len(k))
    for di, dj, coef in ((1, 0, ex[I, J] / dx**2), (-1, 0, ex[I - 1, J] / dx**2),
                         (0, 1, ey[I, J] / dy**2), (0, -1, ey[I, J - 1] / dy**2)):
        ni, nj = I + di, J + dj
        diag += coef
        nb = idx[ni, nj]
        m = nb >= 0
        rows.append(k[m]); cols.append(nb[m]); vals.append(-coef[m])
        b[k[~m]] += coef[~m] * V[ni[~m], nj[~m]]
    rows.append(k); cols.append(k); vals.append(diag)
    A = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
                      shape=(len(k), len(k)))
    V[free] = spla.spsolve(A, b)
    # energie : W = 1/2 eps0 int eps |E|^2 ; W = 1/2 sum Q V
    # un conducteur a 1 V : C = 2 W ; mode impair +/-1 V : C = W
    e0 = 8.854e-12
    Ex = np.diff(V, axis=0) / (dx * 1e-3)
    Ey = np.diff(V, axis=1) / (dy * 1e-3)
    w_e = 0.5 * e0 * (np.sum(ex * Ex**2) + np.sum(ey * Ey**2)) * dx * 1e-3 * dy * 1e-3
    q = 2 * w_e if gap is None else w_e
    return q


def z0(w, t, h, er, gap=None, **grid):
    c = solve_cs(w, t, h, er, gap, **grid)
    c0 = solve_cs(w, t, h, er, gap, er_on=False, **grid)
    v0 = 299792458.0
    z = 1 / (v0 * math.sqrt(c * c0))
    eeff = c / c0
    return (2 * z if gap is not None else z), eeff


def hammerstad(w, h, er):
    u = w / h
    ee = (er + 1) / 2 + (er - 1) / 2 / math.sqrt(1 + 12 / u)
    return 120 * math.pi / (math.sqrt(ee) * (u + 1.393 + 0.667 * math.log(u + 1.444)))


# ------------------------------------------------------------ classes
def classes():
    dT = 20.0   # echauffement admis au courant continu
    wc = {}
    for key, c in CURRENTS.items():
        wc[key] = dict(
            ext_cont=width_mm(c['cont'], dT), ext_pic=width_mm(c['pic'], 45.0),
            ext_2x=width_mm(c['cont'] / 2, dT), int_cont=width_mm(c['cont'], dT, False))
    return dT, wc


def main():
    OUT.mkdir(exist_ok=True)
    dT, wc = classes()
    res = {'stackup': dict(cu_out=CU_OUT, cu_in=CU_IN, prepreg=PREPREG,
                           er_prepreg=ER_PREPREG, core=CORE, er_core=ER_CORE),
           'dT': dT, 'widths': wc, 'currents': CURRENTS, 'ipc_clearance': IPC_CLEAR}
    vias = {}
    for drill, dia in ((0.3, 0.6), (0.4, 0.8)):
        vias[f'{drill}/{dia}'] = dict(i_dT10=via_current(drill, 10), i_dT20=via_current(drill, 20))
    res['vias'] = vias
    # validation du solveur contre Hammerstad (sans masque, sans epaisseur)
    val = {}
    zf, _ = solve_check()
    val['solveur_vs_hammerstad'] = zf
    res['validation'] = val
    # USB 90 ohms differentiel sur F.Cu, reference In1 ; maillage fin
    # (5 um x 2,5 um) : le maillage grossier surestime Zdiff d environ 2 %
    fine = dict(dx=0.005, dy=0.0025)
    usb = []
    for w, s in ((0.17, 0.18), (0.18, 0.18), (0.18, 0.20), (0.19, 0.20), (0.20, 0.20)):
        zd, ee = z0(w, CU_OUT, PREPREG, ER_PREPREG, gap=s, **fine)
        usb.append(dict(w=w, s=s, zdiff=zd, eeff=ee))
    res['usb'] = usb
    se = []
    for w in (0.15, 0.20):
        z, ee = z0(w, CU_OUT, PREPREG, ER_PREPREG, **fine)
        se.append(dict(w=w, z0=z, eeff=ee))
    res['single'] = se
    (OUT / 'rules.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(json.dumps({k: res[k] for k in ('widths', 'vias', 'validation', 'usb', 'single')},
                     indent=1, ensure_ascii=False))


def solve_check():
    w, h = 0.20, PREPREG
    # substrat seul, conducteur quasi plat, pas de masque : cas Hammerstad
    c = solve_cs(w, 0.002, h, ER_PREPREG, mask=0.0)
    c0 = solve_cs(w, 0.002, h, ER_PREPREG, mask=0.0, er_on=False)
    zfd = 1 / (299792458.0 * math.sqrt(c * c0))
    return dict(w=w, h=h, fd=zfd, hammerstad=hammerstad(w, h, ER_PREPREG)), None


if __name__ == '__main__':
    main()
    if '--apply' in sys.argv:
        from apply_routing_rules import apply   # noqa
        apply()
