# -*- coding: utf-8 -*-
"""Optimisation automatique du placement du schema.

Boucle en point fixe : generation -> mesure des recouvrements (avec les
rectangles calibres de metrics.json) -> calcul de deplacements -> ecriture de
placement.json -> regeneration, jusqu'a zero recouvrement. Les deplacements
portent sur les composants a deux ou trois pattes, les notes, et la longueur
des troncons d'etiquette ; les circuits integres, connecteurs et fils restent
ou le concepteur les a mis.

    python3 optimize.py            # optimise, regenere dans electronics/, ERC
    python3 optimize.py --dry      # optimise dans /tmp sans toucher electronics/
"""
import json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ELEC = os.path.abspath(os.path.join(HERE, '..'))
PLACEMENT = os.path.join(HERE, 'placement.json')

FRAME = (14.0, 14.0, 406.0, 283.0)          # zone utile d'une feuille A3
TITLE = (292.0, 246.0)                      # coin du cartouche
GRID = 1.27
MAX_SHIFT = 16.0                            # au-dela, c'est au concepteur de jouer
MAX_STUB = 12.7


def run_design(dest, report):
    r = subprocess.run([sys.executable, os.path.join(HERE, 'design.py'),
                        dest, '--report', report],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f'design.py a echoue :\n{r.stdout}\n{r.stderr}')
    return json.load(open(report, encoding='utf-8'))


def snap_up(v):
    import math
    return math.copysign(math.ceil(abs(v) / GRID) * GRID, v)


def legal(rect):
    x0, y0, x1, y1 = rect
    if x0 < FRAME[0] or y0 < FRAME[1] or x1 > FRAME[2] or y1 > FRAME[3]:
        return False
    return not (x1 > TITLE[0] and y1 > TITLE[1])


def nudge_for(a, b):
    """Deplacement minimal de la boite a pour quitter la boite b."""
    ox = min(a[2], b[2]) - max(a[0], b[0]) + 0.7
    oy = min(a[3], b[3]) - max(a[1], b[1]) + 0.7
    ca, cb = ((a[0] + a[2]) / 2, (a[1] + a[3]) / 2), ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    dx = snap_up(ox if ca[0] >= cb[0] else -ox)
    dy = snap_up(oy if ca[1] >= cb[1] else -oy)
    moves = [(0, dy), (dx, 0)] if oy <= ox else [(dx, 0), (0, dy)]
    moves += [(0, -dy), (-dx, 0)]           # sens oppose en dernier recours
    return moves


def classify(rep):
    """Separe recouvrements durs, frolements d etiquettes toleres, defauts geometriques."""
    todo, grazes = [], 0
    for sh in rep['sheets']:
        for i, j in sh['pairs']:
            A, B = sh['boxes'][i], sh['boxes'][j]
            both_lbl = (A['desc'].startswith('etiquette')
                        and B['desc'].startswith('etiquette'))
            if both_lbl:
                ra, rb = A['rect'], B['rect']
                ma, mb = A.get('meta') or {}, B.get('meta') or {}
                depth = min(min(ra[2], rb[2]) - max(ra[0], rb[0]),
                            min(ra[3], rb[3]) - max(ra[1], rb[1]))
                # seule une vraie colonne de broches - meme sens, ancres au pas
                # de 2,54 mm et plus - a le droit d emboiter ses cadres. Deux
                # etiquettes face a face, elles, se recouvrent pour de vrai.
                stacked = ('a' in ma and 'a' in mb
                           and ma.get('d') == mb.get('d')
                           and abs(ma['a'][0] - mb['a'][0]) < 3.0
                           and abs(ma['a'][1] - mb['a'][1]) >= 2.29)
                if stacked and depth <= 1.45:
                    grazes += 1
                    continue
            todo.append((sh, A, B))
    geom = [g for sh in rep['sheets'] for g in sh['geom']]
    return todo, grazes, geom


def main():
    dry = '--dry' in sys.argv
    work = tempfile.mkdtemp(prefix='opt_')
    report = os.path.join(work, 'rep.json')
    adj = json.load(open(PLACEMENT, encoding='utf-8')) if os.path.exists(PLACEMENT) else {}
    stuck, last = set(), None
    banned = {}                              # cle -> positions interdites
    prev_adj, prev_moved = dict(adj), set()
    todo, grazes, geom = [], 0, []

    for it in range(1, 41):
        rep = run_design(work, report)
        todo, grazes, geom = classify(rep)
        if geom and prev_moved:
            # la derniere passe a cree un defaut electrique : on la retire
            print(f'passe {it:2d} : {len(geom)} defauts geometriques, '
                  f'annulation de {len(prev_moved)} deplacements')
            for k in prev_moved:
                v = adj.get(k)
                banned.setdefault(k, set()).add(tuple(v) if isinstance(v, list) else v)
            adj = dict(prev_adj)
            prev_moved = set()
            json.dump(adj, open(PLACEMENT, 'w', encoding='utf-8'),
                      indent=1, sort_keys=True)
            continue
        n = len(todo)
        print(f'passe {it:2d} : {n} recouvrements ({grazes} frolements toleres)')
        if n == 0 or (last is not None and n >= last + 8):
            break
        last = n
        prev_adj, prev_moved = dict(adj), set()

        moved = set()
        for sh, A, B in todo:
            cand = [x for x in (A, B) if x['movable'] is True and x['key']
                    and x['key'] not in stuck]
            cand.sort(key=lambda x: (0 if x['desc'] == 'note' else 1,
                                     (x['rect'][2] - x['rect'][0]) *
                                     (x['rect'][3] - x['rect'][1])))
            hit = False
            for m in cand:
                if m['key'] in moved:
                    hit = True
                    break
                other = B if m is A else A
                cur = adj.get(m['key'], [0, 0])
                for dx, dy in nudge_for(m['rect'], other['rect']):
                    nx, ny = cur[0] + dx, cur[1] + dy
                    moved_rect = [m['rect'][0] + dx, m['rect'][1] + dy,
                                  m['rect'][2] + dx, m['rect'][3] + dy]
                    if (nx, ny) in banned.get(m['key'], ()):
                        continue
                    if abs(nx) + abs(ny) <= MAX_SHIFT and legal(moved_rect):
                        adj[m['key']] = [round(nx, 2), round(ny, 2)]
                        moved.add(m['key'])
                        prev_moved.add(m['key'])
                        hit = True
                        break
                else:
                    stuck.add(m['key'])
                    continue
                break
            if hit:
                continue
            # rallonger un troncon - jamais entre deux etiquettes : elles ne
            # feraient que glisser l une sur l autre
            both_lbl = (A['desc'].startswith('etiquette')
                        and B['desc'].startswith('etiquette'))
            stubs = [] if both_lbl else [
                x for x in (A, B) if x['movable'] == 'stub' and x['key']
                and x['key'] not in stuck and x['key'] not in moved]
            if stubs:
                m = stubs[0]
                cur = adj.get(m['key'], 0)
                if round(cur + 2.54, 2) in banned.get(m['key'], ()):
                    stuck.add(m['key'])
                elif cur + 2.54 <= MAX_STUB:
                    adj[m['key']] = round(cur + 2.54, 2)
                    moved.add(m['key'])
                    prev_moved.add(m['key'])
                else:
                    stuck.add(m['key'])
            else:
                print(f"   irresoluble : {A['desc']} / {B['desc']} "
                      f"vers ({A['rect'][0]:.0f}, {A['rect'][1]:.0f}) sur {sh['file']}")
        json.dump(adj, open(PLACEMENT, 'w', encoding='utf-8'), indent=1, sort_keys=True)

    for g in geom:
        print('GEOMETRIE :', g)
    print(f'{len(adj)} ajustements dans placement.json, {len(todo)} recouvrements '
          f'durs restants, {grazes} frolements toleres')

    if not dry and not todo and not geom:
        subprocess.run([sys.executable, os.path.join(HERE, 'design.py')], check=True)
        r = subprocess.run(['kicad-cli', 'sch', 'erc', '--severity-all',
                            '-o', os.path.join(work, 'erc.rpt'),
                            os.path.join(ELEC, 'UsainBot.kicad_sch')],
                           capture_output=True, text=True)
        for line in open(os.path.join(work, 'erc.rpt'), encoding='utf-8-sig'):
            if 'ERC messages' in line:
                print('ERC :', line.strip())
    shutil.rmtree(work)


if __name__ == '__main__':
    main()
