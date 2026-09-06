#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Peuple le PCB depuis la netlist et place les composants selon le §3.

A lancer avec le Python de KiCad :
    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/\
Versions/Current/bin/python3 place_pcb.py

Repere (celui du contour dessine dans UsainBot.kicad_pcb) :
    x = 155        axe longitudinal
    y = 145        essieu (equerres moteur)
    +y             sens de la course - la moustache en arc R 140 est en bas
    cote gauche du robot = x > 155
"""
import math, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ELEC = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import sexp

import pcbnew

CX, AXLE, ARC = 155.0, 145.0, 135.6

BOARD = os.path.join(ELEC, 'UsainBot.kicad_pcb')
NET = '/tmp/usainbot_place.net'
subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '-o', NET,
                os.path.join(ELEC, 'UsainBot.kicad_sch')],
               check=True, capture_output=True)

# ------------------------------------------------------------------ netlist
root = sexp.parse(open(NET, encoding='utf-8').read())[0]
comps = {}
for c in sexp.find_all(sexp.find(root, 'components'), 'comp'):
    ref = sexp.unq(sexp.find(c, 'ref')[1])
    fp = sexp.find(c, 'footprint')
    ts = sexp.find(c, 'tstamps')
    val = sexp.find(c, 'value')
    comps[ref] = {'fp': sexp.unq(fp[1]) if fp else '',
                  'val': sexp.unq(val[1]) if val else '',
                  'path': sexp.unq(ts[1]) if ts else ''}
pads_net = {}
for n in sexp.find_all(sexp.find(root, 'nets'), 'net'):
    name = sexp.unq(sexp.find(n, 'name')[1])
    for x in sexp.find_all(n, 'node'):
        pads_net[(sexp.unq(sexp.find(x, 'ref')[1]),
                  sexp.unq(sexp.find(x, 'pin')[1]))] = name

# ------------------------------------------------------------------ placement
import json
from layout import P

FIT = os.path.join(HERE, 'layout_fit.json')
if os.path.exists(FIT):
    for ref, (fx, fy) in json.load(open(FIT)).items():
        x, y, rot, side = P[ref]
        P[ref] = (fx, fy, rot, side)

# ------------------------------------------------------------------ pose
FPDIR = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'
def libpath(nick):
    if nick == 'Pacabot':
        return os.path.join(ELEC, 'kicad-lib', 'Pacabot.pretty')
    return os.path.join(FPDIR, nick + '.pretty')

# ---------------------------------------------------------------- modeles 3D
# Plusieurs empreintes livrees avec KiCad 10 declarent un STEP qui n est pas
# dans le paquet (USB-C HRO, Micro-MaTch, selfs NR, MSK12C02, AMASS hors
# XT60) ou l appellent par son ancien nom. La bibliotheque installee n est pas
# a nous : la reparation se fait ici, sur la copie posee dans la carte.
# kicad-lib/gen_3d_models.py produit ceux qui manquaient vraiment.
K3D = '${KICAD10_3DMODEL_DIR}'
PRJ3D = '${KIPRJMOD}/kicad-lib/3d'
MODELS = {
    # renommes en amont : le modele existe, sous un autre nom
    'HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm':
        K3D + '/Package_SO.3dshapes/HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm.step',
    # meme boitier, pad thermique de 2,1 au lieu de 2,6 : invisible dehors
    'HVQFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm_ThermalVias':
        K3D + '/Package_DFN_QFN.3dshapes/'
              'HVQFN-24-1EP_4x4mm_P0.5mm_EP2.1x2.1mm.step',
    # jamais livres : modeles d encombrement du projet
    'USB_C_Receptacle_HRO_TYPE-C-31-M-12':
        PRJ3D + '/USB_C_Receptacle_HRO_TYPE-C-31-M-12.step',
    'TE_Micro-MaTch_215079-6_2x03_P1.27mm_Vertical':
        PRJ3D + '/TE_Micro-MaTch_215079-6_2x03_P1.27mm_Vertical.step',
    'AMASS_XT30U-M_1x02_P5.0mm_Vertical':
        PRJ3D + '/AMASS_XT30U-M_1x02_P5.0mm_Vertical.step',
    'L_Taiyo-Yuden_NR-30xx': PRJ3D + '/L_Taiyo-Yuden_NR-30xx.step',
    'L_Taiyo-Yuden_NR-40xx': PRJ3D + '/L_Taiyo-Yuden_NR-40xx.step',
    'SW_SPDT_Shouhan_MSK12C02': PRJ3D + '/SW_SPDT_Shouhan_MSK12C02.step',
}


def fix_models(fp):
    """Remplace la liste des modeles quand l empreinte est dans la table."""
    path = MODELS.get(fp.GetFPIDAsString().split(':', 1)[-1])
    if path is None:
        return
    fp.Models().clear()
    m = pcbnew.FP_3DMODEL()
    m.m_Filename = path
    m.m_Show = True
    fp.Models().push_back(m)


def model_paths(fp):
    return [m.m_Filename for m in fp.Models()]


board = pcbnew.LoadBoard(BOARD)
# --reset repose tout le monde SAUF ce qui a ete verrouille a la main dans
# pcbnew et les pieces mecaniques M* (moteurs). Une empreinte verrouillee est
# une decision prise a l ecran, souvent contre la table : la table doit s y
# plier, pas l inverse. layout.py relit ces positions par lock_import.py.
LOCKED_ON_BOARD = {f.GetReference() for f in board.GetFootprints() if f.IsLocked()}
if '--reset' in sys.argv:
    for f in list(board.GetFootprints()):
        if not f.GetReference().startswith('M') and not f.IsLocked():
            board.Delete(f)
have = {f.GetReference() for f in board.GetFootprints()}
nets = {}
def net(name):
    if name not in nets:
        item = board.FindNet(name)
        if item is None:
            item = pcbnew.NETINFO_ITEM(board, name)
            board.Add(item)
        nets[name] = item
    return nets[name]

def reload_in_place(old, fpid):
    """Recharge la DEFINITION d une empreinte sans toucher a sa POSITION.

    Verrouiller une empreinte fige ou elle est, pas la version du dessin :
    quand la bibliotheque corrige un entraxe (le module OLED est passe de
    27,3 x 27,8 suppose a 27,0 x 24,7 mesure) ou gagne un modele 3D, la carte
    doit suivre, sinon les quatre entretoises ne tombent plus en face. On
    repose donc la nouvelle copie exactement au meme endroit, meme angle,
    meme face, et on lui rend son verrou.
    """
    nick, name = fpid.split(':', 1)
    new_fp = pcbnew.FootprintLoad(libpath(nick), name)
    if new_fp is None:
        return None
    pos, rot = old.GetPosition(), old.GetOrientationDegrees()
    flipped, lock = old.IsFlipped(), old.IsLocked()
    new_fp.SetReference(old.GetReference())
    new_fp.SetValue(old.GetValue())
    new_fp.SetPath(old.GetPath())
    board.Delete(old)
    board.Add(new_fp)
    new_fp.SetPosition(pos)
    if flipped:
        new_fp.Flip(pos, False)
    new_fp.SetOrientationDegrees(rot)
    new_fp.SetLocked(lock)
    return new_fp


kept = {f.GetReference(): f for f in board.GetFootprints()}
parked, placed, recabled, refreshed = [], 0, 0, 0
px = 60.0
for ref, info in sorted(comps.items()):
    if ref in have:
        # position figee, mais ni la netlist ni le dessin de l empreinte ne
        # le sont : les deux sont repris sous elle, sans la deplacer.
        f = kept.get(ref)
        if f is not None:
            new_fp = reload_in_place(f, info['fp']) if info['fp'] else None
            if new_fp is not None:
                f, refreshed = new_fp, refreshed + 1
            for pad in f.Pads():
                nname = pads_net.get((ref, pad.GetNumber()))
                if nname:
                    pad.SetNet(net(nname))
                    recabled += 1
            fix_models(f)
        continue
    if not info['fp']:
        continue
    nick, name = info['fp'].split(':', 1)
    fp = pcbnew.FootprintLoad(libpath(nick), name)
    if fp is None:
        print('EMPREINTE INTROUVABLE', info['fp'], 'pour', ref)
        continue
    fp.SetReference(ref)
    fp.SetValue(info['val'])
    if info['path']:
        fp.SetPath(pcbnew.KIID_PATH(info['path']))
    board.Add(fp)
    if ref in P:
        x, y, rot, side = P[ref]
    else:
        x, y, rot, side = px, 105.0, 0, 'F'
        px += 5
        parked.append(ref)
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    if side == 'B':
        fp.Flip(fp.GetPosition(), False)
    fp.SetOrientationDegrees(rot)
    for pad in fp.Pads():
        nname = pads_net.get((ref, pad.GetNumber()))
        if nname:
            pad.SetNet(net(nname))
    fix_models(fp)
    placed += 1

# L emprise de l ESC n a plus a etre dessinee a la main : l empreinte
# Pacabot:ESC_Multistar_10A porte elle-meme son contour, sa hauteur en
# tirets et son modele 3D. On se contente d effacer les traits User.4
# d autrefois, qui montraient un variateur sangle a plat.
for d in list(board.GetDrawings()):
    if d.GetLayer() != pcbnew.User_4:
        continue
    if 'ESC' in getattr(d, 'GetText', lambda: '')():
        board.Delete(d); continue
    if getattr(d, 'GetShape', lambda: None)() != pcbnew.SHAPE_T_RECT:
        continue                                  # gabarit, plenum, axes : garder
    if pcbnew.ToMM(d.GetBoundingBox().GetBottom()) <= 145.0:
        board.Delete(d)                           # ancienne emprise d ESC

# ------------------------------------------------- pieces purement mecaniques
# Elles n ont pas de symbole, donc pas de ligne de netlist : personne ne les
# posait, et la turbine - la piece la plus encombrante de la carte - manquait
# tout simplement. Comme les deux moteurs, leur reference commence par M :
# --reset les epargne. L empreinte apporte AVEC ELLE le percage d air dia 34
# sur Edge.Cuts et les trois vis M2 qui, jusqu ici, n existaient nulle part -
# rien ne fixait la turbine.
import layout as _lay
MECA = {'M3': ('Pacabot:Turbine_EDF27_dessus',
               _lay.TURBINE_XY[0], _lay.TURBINE_XY[1], 0.0)}
meca_poses = 0
for ref, (fpid, mx, my, mrot) in MECA.items():
    old_fp = board.FindFootprintByReference(ref)
    if old_fp is not None:
        if old_fp.IsLocked():
            continue                              # decision prise a l ecran
        board.Delete(old_fp)
    nick, name = fpid.split(':', 1)
    fp = pcbnew.FootprintLoad(libpath(nick), name)
    if fp is None:
        print('EMPREINTE MECANIQUE INTROUVABLE', fpid)
        continue
    fp.SetReference(ref)
    board.Add(fp)
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(mx), pcbnew.FromMM(my)))
    fp.SetOrientationDegrees(mrot)
    meca_poses += 1
    # Le percage d air trace a la main faisait double emploi avec celui de
    # l empreinte, et 2 mm plus petit : c est l empreinte qui fait foi.
    for d in list(board.GetDrawings()):
        if (d.GetLayer() == pcbnew.Edge_Cuts
                and getattr(d, 'GetShape', lambda: None)() == pcbnew.SHAPE_T_CIRCLE
                and abs(pcbnew.ToMM(d.GetCenter().x) - mx) < 1.0
                and abs(pcbnew.ToMM(d.GetCenter().y) - my) < 1.0):
            board.Delete(d)

pcbnew.SaveBoard(BOARD, board)
print(f'{placed} empreintes posees, {meca_poses} mecaniques, {len(nets)} nets, '
      f'{len(LOCKED_ON_BOARD)} verrouillees respectees (dessin rafraichi sur '
      f'{refreshed}), {recabled} pads recables')

# tailles natives + contour ferme, pour fit_layout.py
sizes = {}
for f in board.GetFootprints():
    rot = f.GetOrientationDegrees()
    f.SetOrientationDegrees(0)
    bb = f.GetBoundingBox(False)
    sizes[f.GetReference()] = (
        round(pcbnew.ToMM(bb.GetWidth()), 2), round(pcbnew.ToMM(bb.GetHeight()), 2),
        round(pcbnew.ToMM(bb.GetCenter().x - f.GetPosition().x), 2),
        round(pcbnew.ToMM(bb.GetCenter().y - f.GetPosition().y), 2))
    f.SetOrientationDegrees(rot)
outline = pcbnew.SHAPE_POLY_SET()
board.GetBoardPolygonOutlines(outline, True)
o = outline.Outline(0)
poly = [(round(pcbnew.ToMM(o.CPoint(i).x), 2), round(pcbnew.ToMM(o.CPoint(i).y), 2))
        for i in range(o.PointCount())]
json.dump({'sizes': sizes, 'poly': poly}, open('/tmp/board_geom.json', 'w'))
if parked:
    print(f'{len(parked)} sans position, parquees en haut :', ' '.join(parked))

# ------------------------------------------------- audit des modeles 3D
D3 = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels'
# Le Tag-Connect n est pas un composant : l empreinte n est qu un motif de
# pastilles et trois trous de guidage pour la sonde a ressorts, qu on ne
# laisse pas branchee. Rien a modeliser, et c est la seule.
SANS_PIECE = {'Tag-Connect_TC2030-IDC-FP_2x03_P1.27mm_Vertical'}
sans, casse = [], []
for f in board.GetFootprints():
    if f.GetFPIDAsString().split(':', 1)[-1] in SANS_PIECE:
        continue
    paths = model_paths(f)
    if not paths:
        sans.append(f'{f.GetReference()} ({f.GetFPIDAsString()})')
        continue
    for path in paths:
        real = path.replace('${KICAD10_3DMODEL_DIR}', D3).replace('${KIPRJMOD}', ELEC)
        if not os.path.exists(real):
            casse.append(f'{f.GetReference()} -> {path}')
if sans:
    print(f'{len(sans)} empreintes SANS modele 3D :', ', '.join(sorted(sans)))
if casse:
    print(f'{len(casse)} modeles 3D INTROUVABLES :', ', '.join(sorted(casse)))
if not sans and not casse:
    print('modeles 3D : toutes les empreintes en ont un, et tous se chargent')
