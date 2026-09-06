"""Generateur de schemas KiCad 10 (S-expressions) pour le projet UsainBot."""
import os, re, glob, math, uuid as _uuid, hashlib, json
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
        local = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             '..', 'kicad-lib')
        for d in glob.glob(FPDIR + '/*.pretty') + glob.glob(local + '/*.pretty'):
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
    __slots__ = ('x', 'y', 'dx', 'dy', 'num', 'name', 'etype', 'ref')
    def __init__(self, x, y, dx, dy, num, name, etype, ref=''):
        self.x, self.y, self.dx, self.dy = x, y, dx, dy
        self.num, self.name, self.etype = num, name, etype
        self.ref = ref
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
            pin = Pin(round(ax, 4), round(ay, 4), dx, dy, p['num'], p['name'], p['etype'], ref)
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
# Valeurs de repli seulement : tools/calibrate.py fait rendre chaque chaine par
# KiCad lui-meme et mesure l'encre ; les rectangles exacts sont dans metrics.json.
CHAR_W, LINE_H = 0.78, 1.2
GLABEL_PAD = 3.2          # pointe et marges du cadre d'une etiquette globale
LBL_SIZE = 1.0            # texte des etiquettes, sous les noms de broches
FLD_SIZE = 1.0            # texte des champs reference / valeur / tension

TOOLSDIR = os.path.dirname(os.path.abspath(__file__))

def _load_json(name):
    p = os.path.join(TOOLSDIR, name)
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    return {}

ADJUST  = _load_json('placement.json')   # cle -> [dx, dy] ou (":stub") -> mm
METRICS = _load_json('metrics.json')     # kind -> {texte -> [x0, y0, x1, y1]}

def movable_ref(ref):
    return bool(re.match(r'(R|C|L|D|Q|FB|TP)\d', ref))

def _measured(kind, line, size):
    m = METRICS.get(kind, {}).get(line)
    if m is None:
        return None
    k = size / 1.27
    return [v * k for v in m]

def text_box(text, x, y, angle, just, size, pad=0.0, kind=None):
    """Rectangle occupe par un texte ancre en (x, y).

    Si la chaine a ete calibree (metrics.json), le rectangle est celui que
    KiCad a reellement dessine, au pixel pres ; sinon repli heuristique.
    """
    lines = text.split('\n')
    if kind in ('glabel', 'label', 'text', 'textb', 'field'):
        rels = [_measured('text' if kind == 'field' else kind, l, size)
                for l in lines]
        if all(r is not None for r in rels):
            pitch = METRICS.get('_', {}).get('pitch', 1.63) * size / 1.27
            x0 = min(r[0] for r in rels)
            x1 = max(r[2] for r in rels)
            y0 = min(r[1] + i * pitch for i, r in enumerate(rels))
            y1 = max(r[3] + i * pitch for i, r in enumerate(rels))
            if kind == 'field':                       # champs : centres sur l'ancre
                w, h = x1 - x0, y1 - y0
                if just == 'left':                    # a gauche, centre en y
                    return (x + x0, y - h / 2, x + x1, y + h / 2)
                return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
            if angle == 180 and just == 'right':      # miroir en x
                return (x - x1, y + y0, x - x0, y + y1)
            return (x + x0, y + y0, x + x1, y + y1)
    w = max(len(l) for l in lines) * size * CHAR_W + pad
    h = len(lines) * size * LINE_H
    if kind == 'field':                                # champs : centres sur l'ancre
        if just == 'left':
            return (x, y - h / 2, x + w, y + h / 2)
        return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
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
        self.strings = {'glabel': set(), 'label': set(), 'text': set(),
                        'textb': set(), 'field': set()}
        self._notes = {}
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
              ref_at=None, val_at=None, rot=0, fjust='center', extra=()):
        adj = ADJUST.get(f'{self.filename}:{ref}')
        if adj:
            x, y = x + adj[0], y + adj[1]
            if ref_at:
                ref_at = (ref_at[0] + adj[0], ref_at[1] + adj[1])
            if val_at:
                val_at = (val_at[0] + adj[0], val_at[1] + adj[1])
            # les champs additionnels (Voltage, Power) suivent aussi :
            # l ecart ref / valeur / tension est le meme sur tout le schema
            extra = [(k, v, (px + adj[0], py + adj[1]), h)
                     for k, v, (px, py), h in extra]
        x, y = snap(x), snap(y)
        rj = ADJUST.get(f'{self.filename}:{ref}:ref')
        if rj and ref_at:
            ref_at = (ref_at[0] + rj[0], ref_at[1] + rj[1])
        vj = ADJUST.get(f'{self.filename}:{ref}:val')
        if vj and val_at:
            val_at = (val_at[0] + vj[0], val_at[1] + vj[1])
        pins = self._need(lib_id)
        if rot and any(p['x'] or p['y'] for p in pins):
            raise ValueError(f'rotation refusee pour {lib_id} : broches hors origine')
        if fp and not fp_ok(fp):
            raise ValueError(f'empreinte inconnue : {fp} (pour {ref})')
        if (ref, unit) in self.refs:
            raise ValueError(f'reference dupliquee : {ref} unite {unit}')
        self.refs.add((ref, unit))
        u = uid(f'{self.filename}:sym:{ref}:{unit}')
        node = ['symbol', ['lib_id', q(lib_id)], ['at', fmt(x), fmt(y), str(rot)],
                ['unit', str(unit)],
                ['exclude_from_sim', 'no'], ['in_bom', 'yes' if in_bom else 'no'],
                ['on_board', 'yes'], ['dnp', 'yes' if dnp else 'no'],
                ['uuid', q(u)]]
        rx, ry = ref_at if ref_at else (x, y - 8.89)
        vx, vy = val_at if val_at else (x, y + 8.89)
        def prop(k, v, px, py, hide):
            e = ['effects', ['font', ['size', fmt(FLD_SIZE), fmt(FLD_SIZE)]]]
            if fjust == 'left':
                e.append(['justify', 'left'])
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
        for k, v, (px, py), hide in extra:
            node.append(prop(k, v, px, py, hide))
        for p in pins:
            if p['unit'] in (0, unit):
                node.append(['pin', q(p['num']), ['uuid', q(uid(f'{u}:pin:{p["num"]}'))]])
        node.append(['instances', ['project', q('UsainBot'),
                     ['path', q(self.path()), ['reference', q(ref)], ['unit', str(unit)]]]])
        self.items.append(node)
        bx = self.lib.bbox(lib_id, unit)
        owner = getattr(self, '_pwr_owner', '')
        pkey = f'{self.filename}:{owner}' if owner and movable_ref(owner) else None
        pmov = bool(pkey)
        self._pwr_owner = ''
        if ref.startswith('#'):
            self.boxes.append((sym_box(x, y, rot, bx), f'symbole {value}', pkey, pmov, {}))
        else:
            key = f'{self.filename}:{ref}'
            mov = movable_ref(ref)
            self.boxes.append((sym_box(x, y, rot, bx), f'corps {ref}', key, mov, {}))
            shown = [('ref ' + ref, ref, (rx, ry), key + ':ref')]
            if not hide_value:
                shown.append(('valeur ' + ref, value, (vx, vy), key + ':val'))
            for k, v, (px, py), hide in extra:
                if not hide:
                    shown.append(('valeur ' + ref, v, (px, py), key + ':' + k))
            for label, txt, (px, py), fkey in shown:
                self.strings['field'].add(txt)
                # sur un passif, les champs bougent avec le composant : l ecart
                # ref / valeur / tension reste le meme partout. Ils ne sont
                # independants que sur les boitiers fixes, ou c est le seul levier.
                self.boxes.append((text_box(txt, px, py, 0,
                                            'left' if fjust == 'left' else 'center',
                                            FLD_SIZE, kind='field'),
                                   label, key if mov else fkey, True, {}))
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

    def _label(self, kind, text, at, d, shape=None, owner=None):
        at = (snap(at[0]), snap(at[1]))
        ang, just = LBL_DIR[(round(d[0]), round(d[1]))]
        node = [kind, q(text)]
        if shape:
            node.append(['shape', shape])
        node += [['at', fmt(at[0]), fmt(at[1]), str(ang)],
                 ['fields_autoplaced', 'yes'],
                 ['effects', ['font', ['size', fmt(LBL_SIZE), fmt(LBL_SIZE)]],
                  # etiquette globale : texte centre verticalement dans le cadre,
                  # comme KiCad le fait ; etiquette locale : posee sur le fil
                  ['justify', just] if kind == 'global_label'
                  else ['justify', just, 'bottom']],
                 ['uuid', q(self._k(kind))]]
        pad = GLABEL_PAD * LBL_SIZE / 1.27 if kind == 'global_label' else 0.0
        tkind = 'glabel' if kind == 'global_label' else 'label'
        self.strings[tkind].add(text)
        key = f'{self.filename}:{owner[0]}:{owner[1]}:stub' if owner else None
        self.boxes.append((text_box(text, at[0], at[1], ang, just, LBL_SIZE, pad, tkind),
                           f'etiquette {text!r}', key, 'stub' if key else False,
                           {'a': [at[0], at[1]], 'd': round(d[0]), 'g': tkind == 'glabel'}))
        if kind == 'global_label':
            node.append(['property', q('Intersheetrefs'), q('${INTERSHEET_REFS}'),
                         ['at', fmt(at[0]), fmt(at[1]), '0'],
                         ['effects', ['font', ['size', '1.27', '1.27']], ['hide', 'yes']]])
        self.items.append(node)

    # -- raccordements ----------------------------------------------------
    def _stub(self, pin, stub):
        if pin.ref:
            stub += ADJUST.get(f'{self.filename}:{pin.ref}:{pin.num}:stub', 0)
        return stub

    def net(self, pin, name, stub=2.54):
        stub = self._stub(pin, stub)
        end = pin.out(stub)
        if stub:
            self.wire((pin.x, pin.y), end, name)
        self._label('label', name, end, (pin.dx, pin.dy),
                    owner=(pin.ref, pin.num) if pin.ref else None)
        return end

    def gnet(self, pin, name, stub=2.54):
        stub = self._stub(pin, stub)
        end = pin.out(stub)
        if stub:
            self.wire((pin.x, pin.y), end, name)
        self._label('global_label', name, end, (pin.dx, pin.dy),
                    shape='bidirectional', owner=(pin.ref, pin.num) if pin.ref else None)
        return end

    def label_at(self, name, at, d=(1, 0)):
        self._label('label', name, at, d)

    def glabel_at(self, name, at, d=(1, 0)):
        self._label('global_label', name, at, d, shape='bidirectional')

    def pwr(self, pin, rail, stub=2.54, lib='power'):
        """Place un symbole d'alimentation au bout d'un tronçon."""
        stub = self._stub(pin, stub)
        end = pin.out(stub)
        if stub:
            self.wire((pin.x, pin.y), end, rail)
        self.power_at(rail, end, lib, owner=pin.ref)
        return end

    def power_at(self, rail, at, lib='power', rot=0, owner=''):
        at = (snap(at[0]), snap(at[1]))
        self._pwr_owner = owner
        lib_id = f'{lib}:{rail}'
        self._need(lib_id)
        global PWRN
        PWRN += 1
        ref = f'#PWR{PWRN:03d}'
        self.place(lib_id, ref, rail, at[0], at[1], in_bom=False, rot=rot)

    def note(self, text, x, y, size=1.27, bold=False, movable=True):
        h = hashlib.md5(text.encode()).hexdigest()[:8]
        occ = self._notes.get(h, 0)
        self._notes[h] = occ + 1
        key = f'{self.filename}:note:{h}:{occ}' if movable else None
        adj = ADJUST.get(key) if key else None
        if adj:
            x, y = x + adj[0], y + adj[1]
        kind = 'textb' if bold else 'text'
        for line in text.split('\n'):
            self.strings[kind].add(line)
        e = ['effects', ['font', ['size', fmt(size), fmt(size)]] +
             ([['bold', 'yes']] if bold else []), ['justify', 'left', 'bottom']]
        self.boxes.append((text_box(text, x, y, 0, 'left', size, kind=kind),
                           'note', key, movable, {}))
        self.items.append(['text', q(text), ['exclude_from_sim', 'no'],
                           ['at', fmt(x), fmt(y), '0'], e,
                           ['uuid', q(self._k('text'))]])

    def box(self, x, y, w, h, label=None):
        self.items.append(['rectangle',
                           ['start', fmt(x), fmt(y)], ['end', fmt(x + w), fmt(y + h)],
                           ['stroke', ['width', '0.1'], ['type', 'dash']],
                           ['fill', ['type', 'none']],
                           ['uuid', q(self._k('rect'))]])
        for x0, y0, x1, y1 in ((x, y, x + w, y), (x, y + h, x + w, y + h),
                               (x, y, x, y + h), (x + w, y, x + w, y + h)):
            self.boxes.append(((min(x0, x1) - 0.2, min(y0, y1) - 0.2,
                                max(x0, x1) + 0.2, max(y0, y1) + 0.2),
                               'cadre', None, False, {}))
        if label:
            self.note(label, x + 1.27, y - 1.0, 1.6, bold=True, movable=False)

    def bar(self, pins, spec_end, offset=7.62, pick='low'):
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
            end = (x, pins[0].y if pick == 'high' else pins[-1].y)
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
        # Deux EXTREMITES de nets differents au meme point. Le test precedent
        # les ecarte expressement (un coude partage une extremite avec son
        # propre troncon) ; entre nets differents c est pourtant un
        # court-circuit franc, et le plus discret de tous puisque rien ne se
        # croise a l ecran. C est ce qui a relie B+ a B- sur la prise
        # d equilibrage : les deux coudes de rail retombaient tous deux sur la
        # ligne de la broche du milieu.
        ends = {}
        for x1, y1, x2, y2, n in self.segs:
            for pt in ((x1, y1), (x2, y2)):
                ends.setdefault(pt, set()).add(n)
        for pt, ns in ends.items():
            if len(ns) > 1:
                a, b = sorted(ns)[:2]
                errs.append(f'{self.filename}: {a!r} et {b!r} se rejoignent '
                            f'en ({pt[0]}, {pt[1]})')
        return sorted(set(errs))

    def overlap_pairs(self):
        """Paires d indices de boites qui se recouvrent (hors meme proprietaire)."""
        out = []
        b = self.boxes
        for i in range(len(b)):
            for j in range(i + 1, len(b)):
                ra, na, ka = b[i][0], b[i][1], b[i][2]
                rb, nb, kb = b[j][0], b[j][1], b[j][2]
                def owner(n):
                    w = n.split()
                    return w[-1] if w[0] in ('corps', 'ref', 'valeur') else None
                if owner(na) and owner(na) == owner(nb):
                    continue
                if na == 'cadre' and nb == 'cadre':
                    continue          # les bords de zones peuvent se toucher
                if ka is not None and ka == kb:
                    continue
                if ka and kb and (ka.startswith(kb + ':') or kb.startswith(ka + ':')):
                    continue          # etiquette contre son propre composant
                # deux etiquettes voisines au pas de 2,54 mm : seuls leurs
                # cadres se frolent (~0,35 mm), c'est l'aspect normal d'une
                # colonne de broches - on ne s'alarme qu'au-dela.
                slack = 0.55 if (na.startswith('etiquette')
                                 and nb.startswith('etiquette')) else 0.3
                if overlap(ra, rb, slack):
                    out.append((i, j))
        return out

    def check_overlaps(self):
        """Recouvrements de textes et de corps de composants.

        Une etiquette ecrite par-dessus un boitier ou une autre etiquette ne
        casse rien electriquement, mais rend la feuille illisible - et c est
        precisement ce que l ERC ne verra jamais.
        """
        out = []
        for i, j in self.overlap_pairs():
            ra, na = self.boxes[i][0], self.boxes[i][1]
            nb = self.boxes[j][1]
            out.append(f'{self.filename}: {na} recouvre {nb} '
                       f'vers ({ra[0]:.0f}, {ra[1]:.0f})')
        return sorted(set(out))

    def report(self):
        """Etat geometrique de la feuille, pour l optimiseur de placement."""
        return {'file': self.filename, 'paper': self.paper,
                'boxes': [{'rect': [round(v, 3) for v in r], 'desc': d,
                           'key': k, 'movable': m, 'meta': mt}
                          for r, d, k, m, mt in self.boxes],
                'pairs': self.overlap_pairs(),
                'geom': self.check()}

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
