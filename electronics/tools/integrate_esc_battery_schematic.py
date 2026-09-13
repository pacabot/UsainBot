#!/usr/bin/env python3
"""Targeted integration into the current user schematics; no full regeneration."""
import ast
import copy
import sys
from pathlib import Path
import sexp
import kigen
from integration_blocks import ensure_symbols, build_esc, build_battery

ROOT = Path(__file__).resolve().parents[1]

def ref(node):
    return next((sexp.unq(p[2]) for p in sexp.find_all(node, 'property')
                 if sexp.unq(p[1]) == 'Reference'), '')

def geometric_points(node):
    at = sexp.find(node, 'at')
    if at:
        return [(float(at[1]), float(at[2]))]
    if node[0] in ('wire', 'polyline', 'bus'):
        pts = sexp.find(node, 'pts')
        return [(float(p[1]), float(p[2])) for p in sexp.find_all(pts, 'xy')]
    if node[0] == 'rectangle':
        return [(float(p[1]), float(p[2])) for p in
                (sexp.find(node, 'start'), sexp.find(node, 'end'))]
    return []

def merge(root, block):
    lib = sexp.find(root, 'lib_symbols')
    existing = {sexp.unq(s[1]) for s in sexp.find_all(lib, 'symbol')}
    for name, sym in block.libsyms.items():
        if name not in existing:
            lib.append(sym)
    root.extend(block.items)
    # All user component UUIDs survive; generated wires and supplies receive a
    # disjoint counter range. Check UUID uniqueness within this sheet.
    ids = [sexp.unq(sexp.find(n, 'uuid')[1]) for n in root
           if isinstance(n, list) and sexp.find(n, 'uuid')]
    assert len(ids) == len(set(ids)), 'Duplicate schematic object UUID'

def main():
    footprint = sys.argv[1]
    ensure_symbols(ROOT / 'kicad-lib/Pacabot.kicad_sym')
    source = ROOT / 'tools/design.py'
    tree = ast.parse(source.read_text())
    tree.body = [n for n in tree.body if not
                 (isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                  and isinstance(n.value.func, ast.Name) and n.value.func.id == 'main')]
    api = {'__file__': str(source)}
    argv = sys.argv[:]
    sys.argv = [str(source)]
    exec(compile(tree, str(source), 'exec'), api)
    sys.argv = argv
    kigen.ADJUST.clear()
    kigen.PWRN = 9500
    lib = kigen.SymLib([str(ROOT / 'kicad-lib')])

    path = ROOT / '07-comms.kicad_sch'
    root = sexp.parse(path.read_text())[0]
    assert any(ref(n) == 'J702' for n in root if isinstance(n, list)), 'Already integrated?'
    preserved = []
    removed = []
    for n in root:
        if not isinstance(n, list):
            preserved.append(n); continue
        points = geometric_points(n)
        if points and min(y for _, y in points) >= 166:
            removed.append(ref(n) or n[0])
        else:
            preserved.append(n)
    root = preserved
    block = kigen.Sheet(lib, 'Communications', path.name)
    block._n = 12000
    build_esc(block, api)
    merge(root, block)
    tb = sexp.find(root, 'title_block')
    for n in sexp.find_all(tb, 'comment'):
        if n[1] == '2':
            n[2] = kigen.q('EMAX Bullet 12A sans BEC; montage 3 pins prototype; phases moteur hors PCB')
    path.write_text(sexp.dump(root) + '\n')
    print('Replaced isolated turbine block:', ', '.join(r for r in removed if r.startswith(('J', 'R', 'C'))))

    path = ROOT / '01-power.kicad_sch'
    root = sexp.parse(path.read_text())[0]
    assert any(ref(n) == 'J104' for n in root if isinstance(n, list)), 'Already integrated?'
    preserved = []
    for n in root:
        if not isinstance(n, list):
            preserved.append(n); continue
        points = geometric_points(n)
        drop = bool(points) and all(215 <= x <= 291 and 30 <= y <= 60 for x, y in points)
        if not drop:
            if n[0] == 'text' and 'Pack : XT30' in sexp.unq(n[1]):
                old = sexp.unq(n[1])
                old = old.replace('Pack : XT30 vertical pour le courant, JST-XH pour la nappe\\n'
                                  'd equilibrage qui apporte le point milieu au BQ25887. Coupure par\\n',
                                  'Pack commun : J102 Mega-Fit 3 contacts GND / MID / VPACK.\\n'
                                  'MID alimente la mesure / equilibrage du BQ25887. Coupure par\\n')
                n[1] = kigen.q(old.replace('\\n', '\n'))
            preserved.append(n)
    root = preserved
    block = kigen.Sheet(lib, 'Alimentation', path.name)
    block._n = 14000
    build_battery(block, api, footprint)
    merge(root, block)
    path.write_text(sexp.dump(root) + '\n')
    print('Replaced J102 + J104 with one 3-contact pack connector J102.')

    # Keep the maintained generator consistent without regenerating existing
    # sheets. The integration script itself applies only the two isolated blocks.
    text = source.read_text()
    a = text.index("    j2 = sh.place('Connector_Generic:Conn_01x02', 'J102'")
    b = text.index("    vert(sh, 'Device:Fuse', 'F101'", a)
    text = text[:a] + ('    from integration_blocks import build_battery\n'
                      f'    build_battery(sh, globals(), {footprint!r})\n\n') + text[b:]
    a = text.index('    # ---------------------------------------------------------- turbine')
    b = text.index('    return sh', a)
    text = text[:a] + ('    # Vertical Bullet module; external phases are separate from main PCB pads.\n'
                      '    from integration_blocks import build_esc\n'
                      '    build_esc(sh, globals())\n') + text[b:]
    text = text.replace("'Pack : XT30 vertical pour le courant, JST-XH pour la nappe\\n'\n"
                        "            'd equilibrage qui apporte le point milieu au BQ25887. Coupure par\\n'",
                        "'Pack commun : Mega-Fit 3 contacts GND / MID / VPACK.\\n'\n"
                        "            'MID apporte le point milieu au BQ25887. Coupure par\\n'")
    source.write_text(text)

if __name__ == '__main__':
    main()
