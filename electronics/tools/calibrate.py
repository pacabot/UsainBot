# -*- coding: utf-8 -*-
"""Calibre les metriques de texte contre le rendu reel de KiCad.

Chaque chaine du schema (etiquettes, valeurs, notes) est posee seule sur des
feuilles de calibration, rendue par kicad-cli en SVG, rasterisee, et son encre
mesuree au pixel. Le resultat va dans metrics.json : le verificateur de
recouvrements travaille alors sur les rectangles que KiCad dessine vraiment,
pas sur une estimation de largeur de fonte.
"""
import json, os, shutil, subprocess, sys, tempfile

from PIL import Image

import kigen
from kigen import Sheet, SymLib, q

HERE = os.path.dirname(os.path.abspath(__file__))
PXMM = 8                      # pixels par millimetre au rendu
ROWS_Y = (22, 272, 6)         # premiere ligne, derniere, pas
FID = ((11.43, 11.43), (405.13, 285.75))    # croix de reperage, hors fenetres


def build_pages(samples):
    """Repartit (kind, texte) sur des feuilles A3 ; renvoie [(fichier, slots)]."""
    pages, slots, y, x = [], [], ROWS_Y[0], 24.0
    row_h = ROWS_Y[2]

    def close_page():
        nonlocal slots, y, x
        if slots:
            pages.append(slots)
        slots, y, x = [], ROWS_Y[0], 24.0

    for kind, text in samples:
        est = len(text) * 1.1 + 10
        if x + est > 396:
            x, y = 24.0, y + row_h
            if y > ROWS_Y[1]:
                close_page()
        slots.append((kind, text, x, y))
        x += est + 14
        if x > 300:                       # une chaine longue occupe sa ligne
            x, y = 24.0, y + row_h
            if y > ROWS_Y[1]:
                close_page()
    close_page()
    return pages


def write_page(slots, path, lib):
    sh = Sheet(lib, 'calib', os.path.basename(path), paper='A3')
    for fx, fy in FID:
        sh.wire((fx - 2.54, fy), (fx + 2.54, fy), 'fid')
        sh.wire((fx, fy - 2.54), (fx, fy + 2.54), 'fid')
    for kind, text, x, y in slots:
        if kind == 'glabel':
            sh.glabel_at(text, (x, y), (1, 0))
        elif kind == 'label':
            sh.label_at(text, (x, y), (1, 0))
        else:
            sh.note(text, x, y, 1.27, bold=(kind == 'textb'))
    open(path, 'w', encoding='utf-8').write(
        sh.render([['sheet_instances', ['path', q('/'), ['page', q('1')]]]]))


def ink_bbox(img, x0, y0, x1, y1):
    """Bbox de l encre (alpha > 0) dans une fenetre, en pixels absolus."""
    region = img.crop((int(x0), int(y0), int(x1), int(y1)))
    bbox = region.getchannel('A').getbbox()
    if bbox is None:
        return None
    return (bbox[0] + int(x0), bbox[1] + int(y0),
            bbox[2] + int(x0), bbox[3] + int(y0))


def measure_page(png, slots, metrics):
    img = Image.open(png).convert('RGBA')
    # reperage : deux croix aux coordonnees connues -> echelle et decalage reels
    maps = []
    for fx, fy in FID:
        w = 4 * PXMM
        bb = ink_bbox(img, fx * PXMM - w, fy * PXMM - w, fx * PXMM + w, fy * PXMM + w)
        if bb is None:
            raise SystemExit(f'{png} : croix de reperage introuvable en ({fx}, {fy})')
        maps.append(((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2))
    (p1x, p1y), (p2x, p2y) = maps
    sx = (p2x - p1x) / (FID[1][0] - FID[0][0])
    sy = (p2y - p1y) / (FID[1][1] - FID[0][1])
    ox = p1x - FID[0][0] * sx
    oy = p1y - FID[0][1] * sy

    for kind, text, x, y in slots:
        ax, ay = x * sx + ox, y * sy + oy
        wpx = (len(text) * 1.1 + 12) * sx
        bb = ink_bbox(img, ax - 9 * sx, ay - 2.8 * sy, ax + wpx, ay + 2.8 * sy)
        if bb is None:
            print(f'  !! rien mesure pour {kind} {text!r}')
            continue
        metrics.setdefault(kind, {})[text] = [
            round((bb[0] - ax) / sx, 3), round((bb[1] - ay) / sy, 3),
            round((bb[2] - ax) / sx, 3), round((bb[3] - ay) / sy, 3)]


def main():
    rep_path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/usainbot_rep.json'
    if not os.path.exists(rep_path):
        subprocess.run([sys.executable, os.path.join(HERE, 'design.py'),
                        tempfile.mkdtemp(), '--report', rep_path], check=True)
    rep = json.load(open(rep_path, encoding='utf-8'))
    st = rep['strings']
    samples = []
    for kind, keys in (('glabel', ('glabel',)), ('label', ('label',)),
                       ('text', ('text', 'field')), ('textb', ('textb',))):
        seen = set()
        for kk in keys:
            for t in st.get(kk, ()):
                for line in t.split('\n'):
                    if line and line not in seen:
                        seen.add(line)
                        samples.append((kind, line))
    samples.append(('text', 'Xp'))            # references du pas de ligne
    print(f'{len(samples)} chaines a calibrer')

    work = tempfile.mkdtemp(prefix='calib_')
    metrics = {}
    for i, slots in enumerate(build_pages(samples)):
        sch = os.path.join(work, f'calib{i:02d}.kicad_sch')
        write_page(slots, sch, LIB)
        svgdir = os.path.join(work, f'svg{i:02d}')
        subprocess.run(['kicad-cli', 'sch', 'export', 'svg', '--no-background-color',
                        '--exclude-drawing-sheet', '-o', svgdir, sch],
                       check=True, capture_output=True)
        svg = [f for f in os.listdir(svgdir) if f.endswith('.svg')][0]
        png = os.path.join(work, f'p{i:02d}.png')
        subprocess.run(['rsvg-convert', '-w', str(420 * PXMM),
                        os.path.join(svgdir, svg), '-o', png], check=True)
        measure_page(png, slots, metrics)
        print(f'  page {i + 1} mesuree ({len(slots)} chaines)')

    # pas de ligne des notes multi-lignes, mesure et non suppose
    one = metrics['text']['Xp']
    two_probe = os.path.join(work, 'two.kicad_sch')
    write_page([('text2', 'Xp\nXp', 60, 60)], two_probe, LIB)
    svgdir = os.path.join(work, 'svg_two')
    subprocess.run(['kicad-cli', 'sch', 'export', 'svg', '--no-background-color',
                    '--exclude-drawing-sheet', '-o', svgdir, two_probe], check=True, capture_output=True)
    svg = [f for f in os.listdir(svgdir) if f.endswith('.svg')][0]
    png = os.path.join(work, 'two.png')
    subprocess.run(['rsvg-convert', '-w', str(420 * PXMM),
                    os.path.join(svgdir, svg), '-o', png], check=True)
    img = Image.open(png).convert('RGBA')
    bb = ink_bbox(img, (60 - 9) * PXMM, (60 - 9) * PXMM,
                  (60 + 20) * PXMM, (60 + 9) * PXMM)
    Y0, Y1 = bb[1] / PXMM - 60, bb[3] / PXMM - 60
    pitch = (Y1 - one[3]) if abs(Y1 - one[3]) > abs(Y0 - one[1]) else (Y0 - one[1])
    metrics['_'] = {'pitch': round(pitch, 3)}
    print(f'pas de ligne mesure : {pitch:.3f} mm '
          f'({"vers le bas" if pitch > 0 else "vers le haut"})')

    out = os.path.join(HERE, 'metrics.json')
    json.dump(metrics, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
    n = sum(len(v) for k, v in metrics.items() if k != '_')
    print(f'{out} : {n} mesures')
    shutil.rmtree(work)


LIB = SymLib()
if __name__ == '__main__':
    main()
