"""Generateur de schemas KiCad 10 (S-expressions) pour le projet UsainBot."""
import os, glob, math, uuid as _uuid, hashlib, json
import sexp

def _kicad_share():
    for d in (os.environ.get('KICAD_SHARE'),
              '/Applications/KiCad/KiCad.app/Contents/SharedSupport',
              '/usr/share/kicad', '/usr/local/share/kicad'):
        if d and os.path.isdir(os.path.join(d, 'symbols')):
            return d
    raise SystemExit('bibliotheques KiCad introuvables : definir KICAD_SHARE')

SHARE  = _kicad_share()
SYMDIR = os.path.join(SHARE, 'symbols')
FPDIR  = os.path.join(SHARE, 'footprints')
VERSION = '20260306'
GENVER  = '10.0'

# ---------------------------------------------------------------- uuid stable
_seed = {}
def uid(key):
    """UUID deterministe : regenerer le projet ne casse pas les annotations."""
    h = hashlib.md5(key.encode()).hexdigest()
    return f'{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}'

def q(s):
    return ('"' + str(s).replace('\\', '\\\\').replace('"', '\\"')
            .replace('\n', '\\n') + '"')

GRID = 1.27
def snap(v):
    return round(round(float(v) / GRID) * GRID, 4)

def fmt(v):
    if isinstance(v, float):
        s = f'{v:.4f}'.rstrip('0').rstrip('.')
        return s if s not in ('', '-0') else '0'
    return str(v)

# ---------------------------------------------------------------- footprints
_fpidx = None
def fp_ok(name):
    global _fpidx
    if _fpidx is None:
        _fpidx = {}
        for d in glob.glob(FPDIR + '/*.pretty'):
            lib = os.path.basename(d)[:-7]
            for f in glob.glob(d + '/*.kicad_mod'):
                _fpidx.setdefault(lib + ':' + os.path.basename(f)[:-10], True)
    return name in _fpidx

# ---------------------------------------------------------------- librairies
class SymLib:
    def __init__(self, extra_dirs=()):
        self.files = {}
        for d in (SYMDIR,) + tuple(extra_dirs):
            for f in glob.glob(os.path.join(d, '*.kicad_sym')):
                self.files[os.path.basename(f)[:-10]] = f
        self.cache = {}

    def _raw(self, lib):
        if lib not in self.cache:
            root = sexp.parse(open(self.files[lib], encoding='utf-8').read())[0]
            self.cache[lib] = {sexp.unq(s[1]): s for s in sexp.find_all(root, 'symbol')}
        return self.cache[lib]

    def flat(self, lib_id):
        """Renvoie (definition aplatie renommee 'Lib:Nom', liste de pins)."""
        lib, name = lib_id.split(':', 1)
        syms = self._raw(lib)
        if name not in syms:
            raise KeyError(f'symbole absent : {lib_id}')
        child = syms[name]
        chain = [child]
        cur = child
        while True:
            ext = sexp.find(cur, 'extends')
            if not ext:
                break
            cur = syms[sexp.unq(ext[1])]
            chain.append(cur)
        base = chain[-1]                     # graphiques + pins
        base_name = sexp.unq(base[1])

        if len(chain) == 1:
            # symbole racine : KiCad recopie la definition telle quelle, sans
            # rien reordonner. Toute divergence declencherait un avertissement
            # << ne correspond pas a la copie en librairie >>.
            out = json.loads(json.dumps(child))
            out[1] = q(lib_id)
            for sub in sexp.find_all(out, 'symbol'):
                sub[1] = q(sexp.unq(sub[1]).replace(base_name, name, 1))
            return out, self._pins(out, name)

        out = ['symbol', q(lib_id)]
        # options : enfant prioritaire, sinon parent
        for tag in ('power', 'pin_numbers', 'pin_names', 'exclude_from_sim',
                    'in_bom', 'on_board', 'in_pos_files',
                    'duplicate_pin_numbers_are_jumpers'):
            node = None
            for s in chain:
                node = sexp.find(s, tag)
                if node:
                    break
            if node:
                out.append(node)
        # proprietes : fusion enfant -> parent
        props = {}
        for s in reversed(chain):
            for p in sexp.find_all(s, 'property'):
                key = sexp.unq(p[2] if p[1] == 'private' else p[1])
                props[key] = p
        for k in ('Reference', 'Value', 'Footprint', 'Datasheet', 'Description'):
            if k in props:
                out.append(props.pop(k))
        for k in sorted(props):
            out.append(props[k])
        # sous-symboles du parent, renommes
        pins = []
        for sub in sexp.find_all(base, 'symbol'):
            sub = json.loads(json.dumps(sub))          # copie profonde
            sub[1] = q(sexp.unq(sub[1]).replace(base_name, name, 1))
            out.append(sub)
            # numero d'unite = premier chiffre du suffixe _u_c
            try:
                unit = int(sexp.unq(sub[1]).rsplit('_', 2)[-2])
            except Exception:
                unit = 1
            for p in sexp.find_all(sub, 'pin'):
                at = sexp.find(p, 'at')
                pins.append(dict(
                    num=sexp.unq(sexp.find(p, 'number')[1]),
                    name=sexp.unq(sexp.find(p, 'name')[1]),
                    x=float(at[1]), y=float(at[2]), ang=float(at[3]) if len(at) > 3 else 0.0,
                    etype=p[1], unit=unit))
        return out, pins

    def bbox(self, lib_id, unit=1):
        """Emprise graphique du symbole, en coordonnees de librairie."""
        node, pins = self.flat(lib_id)
        xs, ys = [], []

        def walk(n):
            if not isinstance(n, list):
                return
            tag = n[0] if isinstance(n[0], str) else None
            if tag in ('start', 'end', 'xy', 'center', 'mid'):
                try:
                    xs.append(float(n[1])); ys.append(float(n[2]))
                except (ValueError, IndexError):
                    pass
            for c in n:
                if isinstance(c, list):
                    walk(c)

        for sub in sexp.find_all(node, 'symbol'):
            try:
                u = int(sexp.unq(sub[1]).rsplit('_', 2)[-2])
            except Exception:
                u = 1
            if u in (0, unit):
                walk(sub)
        for p in pins:
            if p['unit'] in (0, unit):
                xs.append(p['x']); ys.append(p['y'])
        if not xs:
            return (-1.27, -1.27, 1.27, 1.27)
        return (min(xs), min(ys), max(xs), max(ys))

    @staticmethod
    def _pins(node, name):
        pins = []
        for sub in sexp.find_all(node, 'symbol'):
            try:
                unit = int(sexp.unq(sub[1]).rsplit('_', 2)[-2])
            except Exception:
                unit = 1
            for p in sexp.find_all(sub, 'pin'):
                at = sexp.find(p, 'at')
                pins.append(dict(
                    num=sexp.unq(sexp.find(p, 'number')[1]),
                    name=sexp.unq(sexp.find(p, 'name')[1]),
                    x=float(at[1]), y=float(at[2]),
                    ang=float(at[3]) if len(at) > 3 else 0.0,
                    etype=p[1], unit=unit))
        return pins

    def units(self, lib_id):
        _, pins = self.flat(lib_id)
        return max([p['unit'] for p in pins] + [1])

# ---------------------------------------------------------------- geometrie
class Pin:
    __slots__ = ('x', 'y', 'dx', 'dy', 'num', 'name', 'etype')
    def __init__(self, x, y, dx, dy, num, name, etype):
        self.x, self.y, self.dx, self.dy = x, y, dx, dy
        self.num, self.name, self.etype = num, name, etype
    def out(self, d):
        return (round(self.x + self.dx * d, 4), round(self.y + self.dy * d, 4))

class Part:
    def __init__(self, sheet, ref, lib_id, x, y, unit, pins):
        self.sheet, self.ref, self.lib_id = sheet, ref, lib_id
        self.x, self.y, self.unit = x, y, unit
        self._by_num, self._by_name = {}, {}
        for p in pins:
            if p['unit'] not in (0, unit):
                continue
            # lib : y vers le haut ; schema : y vers le bas
            ax = x + p['x']
            ay = y - p['y']
            a = math.radians(p['ang'])
            dx = round(-math.cos(a), 6)
            dy = round(math.sin(a), 6)
            pin = Pin(round(ax, 4), round(ay, 4), dx, dy, p['num'], p['name'], p['etype'])
            self._by_num[p['num']] = pin
            self._by_name.setdefault(p['name'], pin)

    def pin(self, key):
        key = str(key)
        if key in self._by_num:
            return self._by_num[key]
        if key in self._by_name:
            return self._by_name[key]
        raise KeyError(f'{self.ref} ({self.lib_id}) : pas de broche {key!r} ; '
                       f'numeros={sorted(self._by_num)} noms={sorted(self._by_name)}')

    def pins(self):
        return list(self._by_num.values())

# ---------------------------------------------------------------- feuille
# Sens du troncon -> (rotation, justification) de l etiquette.
# A 180 degres KiCad ecrit le texte a gauche de l ancre avec << justify right >> ;
# mettre << left >> le fait deborder sur le boitier du composant.
# Sur un troncon vertical l'etiquette reste horizontale : ecrite le long du fil,
# elle traverse le composant place au-dessus ou au-dessous.
LBL_DIR = {(1, 0): (0, 'left'), (-1, 0): (180, 'right'),
           (0, -1): (0, 'left'), (0, 1): (0, 'left')}

# Fonte a batons de KiCad : chasse ~0,78 x la taille, hauteur ~1,2.
CHAR_W, LINE_H = 0.78, 1.2
GLABEL_PAD = 3.2          # pointe et marges du cadre d'une etiquette globale

def text_box(text, x, y, angle, just, size, pad=0.0):
    """Rectangle occupe par un texte ancre en (x, y), justifie en bas."""
    lines = text.split('\n')
    w = max(len(l) for l in lines) * size * CHAR_W + pad
    h = len(lines) * size * LINE_H
    if angle in (0, 180):
        x0 = x if just == 'left' else x - w
        if pad:
            x0 -= pad / 2 if just == 'left' else 0
        return (x0, y - h, x0 + w, y)
    y0 = y - w if just == 'left' else y
    return (x, y0, x + h, y0 + w)

def overlap(a, b, slack=0.3):
    return (a[0] < b[2] - slack and b[0] < a[2] - slack and
            a[1] < b[3] - slack and b[1] < a[3] - slack)

def sym_box(x, y, rot, bx):
    """Emprise d un symbole place en (x, y) avec rotation, depuis sa bbox librairie."""
    x0, y0, x1, y1 = bx
    if rot == 0:
        return (x + x0, y - y1, x + x1, y - y0)
    if rot == 180:
        return (x - x1, y + y0, x - x0, y + y1)
    if rot == 90:
        return (x + y0, y + x0, x + y1, y + x1)
    return (x - y1, y - x1, x - y0, y - x0)          # 270

# Le cartouche occupe le coin bas-droit de la feuille : rien ne doit y tomber.
TITLE_BLOCK = {'A3': (292.0, 246.0), 'A4': (200.0, 170.0)}

class Sheet:
    def __init__(self, lib, name, filename, paper='A3', title='', rev='', date='',
                 company='', comments=()):
        self.lib, self.name, self.filename, self.paper = lib, name, filename, paper
        self.title, self.rev, self.date, self.company = title, rev, date, company
        self.comments = list(comments)
        self.uuid = uid('sheetfile:' + filename)
        self.libsyms = {}
        self.items = []          # noeuds s-exp deja formes
        self.segs = []           # (x1, y1, x2, y2, net) pour la verification
        self.boxes = []          # (rect, description) pour la chasse aux recouvrements
        self.parts = []
        self.refs = set()
        self._n = 0

    # -- primitives -------------------------------------------------------
    def _k(self, tag):
        self._n += 1
        return uid(f'{self.filename}:{tag}:{self._n}')

    def _need(self, lib_id):
        if lib_id not in self.libsyms:
            self.libsyms[lib_id] = self.lib.flat(lib_id)[0]
        return self.lib.flat(lib_id)[1]

    def place(self, lib_id, ref, value, x, y, fp=None, unit=1, fields=None,
              datasheet='~', dnp=False, in_bom=True, hide_value=False,
              ref_at=None, val_at=None, rot=0):
        x, y = snap(x), snap(y)
        pins = self._need(lib_id)
        if rot and any(p['x'] or p['y'] for p in pins):
            raise ValueError(f'rotation refusee pour {lib_id} : broches hors origine')
        if fp and not fp_ok(fp):
            raise ValueError(f'empreinte inconnue : {fp} (pour {ref})')
        if ref in self.refs:
            raise ValueError(f'reference dupliquee : {ref}')
        self.refs.add(ref)
        u = uid(f'{self.filename}:sym:{ref}:{unit}')
        node = ['symbol', ['lib_id', q(lib_id)], ['at', fmt(x), fmt(y), str(rot)],
                ['unit', str(unit)],
                ['exclude_from_sim', 'no'], ['in_bom', 'yes' if in_bom else 'no'],
                ['on_board', 'yes'], ['dnp', 'yes' if dnp else 'no'],
                ['uuid', q(u)]]
        rx, ry = ref_at if ref_at else (x, y - 8.89)
        vx, vy = val_at if val_at else (x, y + 8.89)
        def prop(k, v, px, py, hide):
            e = ['effects', ['font', ['size', '1.27', '1.27']]]
            if hide:
                e.append(['hide', 'yes'])
            return ['property', q(k), q(v), ['at', fmt(px), fmt(py), '0'], e]
        node.append(prop('Reference', ref, rx, ry, ref.startswith('#')))
        node.append(prop('Value', value, vx, vy, hide_value or ref.startswith('#')))
        node.append(prop('Footprint', fp or '', x, y, True))
        node.append(prop('Datasheet', datasheet, x, y, True))
        node.append(prop('Description', '', x, y, True))
        for k, v in (fields or {}).items():
            node.append(prop(k, v, x, y, True))
        for p in pins:
            if p['unit'] in (0, unit):
                node.append(['pin', q(p['num']), ['uuid', q(uid(f'{u}:pin:{p["num"]}'))]])
        node.append(['instances', ['project', q('UsainBot'),
                     ['path', q(self.path()), ['reference', q(ref)], ['unit', str(unit)]]]])
        self.items.append(node)
        bx = self.lib.bbox(lib_id, unit)
        if ref.startswith('#'):
            self.boxes.append((sym_box(x, y, rot, bx), f'symbole {value}'))
        else:
            self.boxes.append((sym_box(x, y, rot, bx), f'corps {ref}'))
            for label, (px, py) in (('ref ' + ref, (rx, ry)),
                                    ('valeur ' + ref, (vx, vy))):
                w = len(ref if label.startswith('ref') else value) * 1.27 * CHAR_W
                self.boxes.append(((px - w / 2, py - 1.27 * LINE_H / 2,
                                    px + w / 2, py + 1.27 * LINE_H / 2), label))
        part = Part(self, ref, lib_id, x, y, unit, pins)
        self.parts.append(part)
        return part

    def path(self):
        return f'/{ROOT_UUID}/{self.uuid}' if self.filename != ROOT_FILE else f'/{ROOT_UUID}'

    def wire(self, a, b, net=None):
        a = (snap(a[0]), snap(a[1])); b = (snap(b[0]), snap(b[1]))
        self.segs.append((a[0], a[1], b[0], b[1], net))
        self.items.append(['wire', ['pts', ['xy', fmt(a[0]), fmt(a[1])],
                                    ['xy', fmt(b[0]), fmt(b[1])]],
                           ['stroke', ['width', '0'], ['type', 'default']],
                           ['uuid', q(self._k('wire'))]])

    def junction(self, p):
        p = (snap(p[0]), snap(p[1]))
        self.items.append(['junction', ['at', fmt(p[0]), fmt(p[1])], ['diameter', '0'],
                           ['color', '0', '0', '0', '0'], ['uuid', q(self._k('jct'))]])

    def nc(self, pin):
        self.items.append(['no_connect', ['at', fmt(pin.x), fmt(pin.y)],
                           ['uuid', q(self._k('nc'))]])

    def _label(self, kind, text, at, d, shape=None):
        at = (snap(at[0]), snap(at[1]))
        ang, just = LBL_DIR[(round(d[0]), round(d[1]))]
        node = [kind, q(text)]
        if shape:
            node.append(['shape', shape])
        node += [['at', fmt(at[0]), fmt(at[1]), str(ang)],
                 ['fields_autoplaced', 'yes'],
                 ['effects', ['font', ['size', '1.27', '1.27']], ['justify', just, 'bottom']],
                 ['uuid', q(self._k(kind))]]
        pad = GLABEL_PAD if kind == 'global_label' else 0.0
        self.boxes.append((text_box(text, at[0], at[1], ang, just, 1.27, pad),
                           f'etiquette {text!r}'))
        if kind == 'global_label':
            node.append(['property', q('Intersheetrefs'), q('${INTERSHEET_REFS}'),
                         ['at', fmt(at[0]), fmt(at[1]), '0'],
                         ['effects', ['font', ['size', '1.27', '1.27']], ['hide', 'yes']]])
        self.items.append(node)

    # -- raccordements ----------------------------------------------------
    def net(self, pin, name, stub=2.54):
        end = pin.out(stub)
        if stub:
            self.wire((pin.x, pin.y), end, name)
        self._label('label', name, end, (pin.dx, pin.dy))
        return end

    def gnet(self, pin, name, stub=2.54):
        end = pin.out(stub)
        if stub:
            self.wire((pin.x, pin.y), end, name)
        self._label('global_label', name, end, (pin.dx, pin.dy), shape='bidirectional')
        return end

    def label_at(self, name, at, d=(1, 0)):
        self._label('label', name, at, d)

    def glabel_at(self, name, at, d=(1, 0)):
        self._label('global_label', name, at, d, shape='bidirectional')

    def pwr(self, pin, rail, stub=2.54, lib='power'):
        """Place un symbole d'alimentation au bout d'un tronçon."""
        end = pin.out(stub)
        if stub:
            self.wire((pin.x, pin.y), end, rail)
        self.power_at(rail, end, lib)
        return end

    def power_at(self, rail, at, lib='power', rot=0):
        at = (snap(at[0]), snap(at[1]))
        lib_id = f'{lib}:{rail}'
        self._need(lib_id)
        global PWRN
        PWRN += 1
        ref = f'#PWR{PWRN:03d}'
        self.place(lib_id, ref, rail, at[0], at[1], in_bom=False, rot=rot)

    def note(self, text, x, y, size=1.27, bold=False):
        e = ['effects', ['font', ['size', fmt(size), fmt(size)]] +
             ([['bold', 'yes']] if bold else []), ['justify', 'left', 'bottom']]
        self.boxes.append((text_box(text, x, y, 0, 'left', size), 'note'))
        self.items.append(['text', q(text), ['exclude_from_sim', 'no'],
                           ['at', fmt(x), fmt(y), '0'], e,
                           ['uuid', q(self._k('text'))]])

    def box(self, x, y, w, h, label=None):
        self.items.append(['rectangle',
                           ['start', fmt(x), fmt(y)], ['end', fmt(x + w), fmt(y + h)],
                           ['stroke', ['width', '0.1'], ['type', 'dash']],
                           ['fill', ['type', 'none']],
                           ['uuid', q(self._k('rect'))]])
        if label:
            self.note(label, x + 1.27, y - 1.0, 1.6, bold=True)

    def bar(self, pins, spec_end, offset=7.62):
        """Relie plusieurs broches paralleles a un seul point, puis renvoie ce
        point. Evite d empiler autant d etiquettes identiques que de broches."""
        pins = sorted(pins, key=lambda p: (p.x, p.y))
        if abs(pins[0].dy) > 0.5:                       # broches verticales
            y = pins[0].y + pins[0].dy * offset
            for p in pins:
                self.wire((p.x, p.y), (p.x, y), spec_end)
            self.wire((pins[0].x, y), (pins[-1].x, y), spec_end)
            for p in pins[1:-1]:
                self.junction((p.x, y))
            end = (pins[-1].x, y)
        else:                                           # broches horizontales
            x = pins[0].x + pins[0].dx * offset
            for p in pins:
                self.wire((p.x, p.y), (x, p.y), spec_end)
            self.wire((x, pins[0].y), (x, pins[-1].y), spec_end)
            for p in pins[1:-1]:
                self.junction((x, p.y))
            end = (x, pins[-1].y)
        self.junction(end)
        return end

    # -- verification -----------------------------------------------------
    def check(self):
        """Courts-circuits geometriques : troncons colineaires de nets differents
        qui se recouvrent, ou extremite tombant au milieu d un fil etranger."""
        errs = []
        tb = TITLE_BLOCK.get(self.paper)
        if tb:
            for p in self.parts:
                if p.x > tb[0] and p.y > tb[1]:
                    errs.append(f'{self.filename}: {p.ref} a ({p.x}, {p.y}) '
                                f'tombe dans le cartouche')
            for it in self.items:
                if it[0] == 'text':
                    at = [c for c in it if isinstance(c, list) and c[0] == 'at'][0]
                    tx, ty = float(at[1]), float(at[2])
                    if tx > tb[0] and ty > tb[1]:
                        errs.append(f'{self.filename}: note a ({tx}, {ty}) '
                                    f'tombe dans le cartouche')
        vert = [(x1, min(y1, y2), max(y1, y2), n)
                for x1, y1, x2, y2, n in self.segs if x1 == x2]
        horz = [(y1, min(x1, x2), max(x1, x2), n)
                for x1, y1, x2, y2, n in self.segs if y1 == y2]
        for group, axis in ((vert, 'x'), (horz, 'y')):
            for i in range(len(group)):
                a, a0, a1, na = group[i]
                for j in range(i + 1, len(group)):
                    b, b0, b1, nb = group[j]
                    if a != b or na == nb:
                        continue
                    lo, hi = max(a0, b0), min(a1, b1)
                    if hi - lo > 1e-6:
                        errs.append(f'{self.filename}: {na!r} et {nb!r} se recouvrent '
                                    f'a {axis}={a}, de {lo} a {hi}')
        for x1, y1, x2, y2, n in self.segs:
            for px, py in ((x1, y1), (x2, y2)):
                for a, b, c, d, m in self.segs:
                    if m == n or (px, py) in ((a, b), (c, d)):
                        continue
                    if a == c == px and min(b, d) < py < max(b, d):
                        errs.append(f'{self.filename}: {n!r} touche {m!r} '
                                    f'en ({px}, {py})')
                    if b == d == py and min(a, c) < px < max(a, c):
                        errs.append(f'{self.filename}: {n!r} touche {m!r} '
                                    f'en ({px}, {py})')
        return sorted(set(errs))

    def check_overlaps(self):
        """Recouvrements de textes et de corps de composants.

        Une etiquette ecrite par-dessus un boitier ou une autre etiquette ne
        casse rien electriquement, mais rend la feuille illisible - et c est
        precisement ce que l ERC ne verra jamais.
        """
        out = []
        b = self.boxes
        for i in range(len(b)):
            for j in range(i + 1, len(b)):
                ra, na = b[i]
                rb, nb = b[j]
                # reference et valeur collent volontairement a leur composant
                def owner(n):
                    w = n.split()
                    return w[-1] if w[0] in ('corps', 'ref', 'valeur') else None
                if owner(na) and owner(na) == owner(nb):
                    continue
                if overlap(ra, rb):
                    out.append(f'{self.filename}: {na} recouvre {nb} '
                               f'vers ({ra[0]:.0f}, {ra[1]:.0f})')
        return sorted(set(out))

    # -- sortie -----------------------------------------------------------
    def render(self, sheets_block=None):
        root = ['kicad_sch',
                ['version', VERSION], ['generator', q('eeschema')],
                ['generator_version', q(GENVER)],
                ['uuid', q(self.uuid if self.filename != ROOT_FILE else ROOT_UUID)],
                ['paper', q(self.paper)]]
        tb = ['title_block', ['title', q(self.title)], ['date', q(self.date)],
              ['rev', q(self.rev)], ['company', q(self.company)]]
        for i, c in enumerate(self.comments, 1):
            tb.append(['comment', str(i), q(c)])
        root.append(tb)
        libs = ['lib_symbols']
        for k in sorted(self.libsyms):
            libs.append(self.libsyms[k])
        root.append(libs)
        root += self.items
        if sheets_block:
            root += sheets_block
        root.append(['embedded_fonts', 'no'])
        return sexp.dump(root) + '\n'

ROOT_UUID = uid('UsainBot:root')
ROOT_FILE = 'UsainBot.kicad_sch'
PWRN = 0
