# -*- coding: utf-8 -*-
"""Genere le schema hierarchique KiCad du robot UsainBot."""
import json, os, sys
import kigen
from kigen import SymLib, Sheet, q, fmt, uid, ROOT_UUID, ROOT_FILE

HERE = os.path.dirname(os.path.abspath(__file__))
ELEC = os.path.abspath(os.path.join(HERE, '..'))          # .../electronics
_args = [a for a in sys.argv[1:] if not a.startswith('--')]
DEST = _args[0] if _args else ELEC
REPORT = (sys.argv[sys.argv.index('--report') + 1]
          if '--report' in sys.argv else None)
PRJ  = os.path.join(ELEC, 'kicad-lib')
LIB  = SymLib([PRJ])

DATE, REV, COMPANY = '2026-08-30', 'A', 'Pacabot'

# ------------------------------------------------------------------ empreintes
R06  = 'Resistor_SMD:R_0402_1005Metric'     # petit signal : 0402 partout
R08  = 'Resistor_SMD:R_0805_2012Metric'
R12  = 'Resistor_SMD:R_1206_3216Metric'
C06  = 'Capacitor_SMD:C_0402_1005Metric'    # petit signal : 0402 partout
C0603 = 'Capacitor_SMD:C_0603_1608Metric'   # repli quand tension ou valeur depasse
C08  = 'Capacitor_SMD:C_0805_2012Metric'
C12  = 'Capacitor_SMD:C_1206_3216Metric'
C1210= 'Capacitor_SMD:C_1210_3225Metric'
CPOL = 'Capacitor_SMD:CP_Elec_6.3x7.7'
LED06= 'LED_SMD:LED_0603_1608Metric'
TP   = 'TestPoint:TestPoint_Pad_D1.5mm'
SOT23= 'Package_TO_SOT_SMD:SOT-23'

PWRLIB = {'GND': 'power', '+3V3': 'power', '+5V': 'power', 'VBUS': 'power',
          'PWR_FLAG': 'power',
          'VBAT': 'Pacabot', 'VPACK': 'Pacabot', '+3V3A': 'Pacabot', '+3V3_BLE': 'Pacabot'}
GNDISH = {'GND'}

# ------------------------------------------------------------------ raccords
def cx(sh, pin, spec, stub=2.54):
    """'@RAIL' -> symbole d'alim ; '$NET' -> label global ; 'NET' -> label local ; 'NC'."""
    if spec is None:
        return
    if spec == 'NC':
        sh.nc(pin); return
    if spec.startswith('@'):
        rail = spec[1:]
        stub = sh._stub(pin, stub)
        end = pin.out(stub)
        if stub:
            sh.wire((pin.x, pin.y), end, rail)
        d = (round(pin.dx), round(pin.dy))
        gnd = rail in GNDISH
        if d[1] != 0:
            # troncon vertical : masse en bas, rail en haut, jamais couches
            rot = 0 if (gnd and d[1] > 0) or (not gnd and d[1] < 0) else 180
        else:
            # troncon horizontal : petit coude, la masse descend, le rail monte.
            # Les controles de fils et d'encre attrapent les coudes hasardeux.
            e2 = (end[0], end[1] + (2.54 if gnd else -2.54))
            sh.wire(end, e2, rail)
            end = e2
            rot = 0
        sh.power_at(rail, end, PWRLIB[rail], rot=rot, owner=pin.ref)
    elif spec.startswith('$'):
        sh.gnet(pin, spec[1:], stub)
    else:
        sh.net(pin, spec, stub)

def out_pin(part):
    """Broche de sortie d une unite d ampli op (la numerotation change d une
    unite a l autre : 1, 7, 8, 14)."""
    for p in part.pins():
        if p.etype == 'output':
            return p
    raise KeyError(f'{part.ref} : pas de sortie')


def cx_bar(sh, part, nums, spec, offset=7.62, stub=2.54):
    """Plusieurs broches sur un meme net : une seule etiquette, pas une par broche.

    Les broches confondues (le BQ25887 double PMID, SW, SNS, BAT) sont
    dedoublonnees ; les broches espacees sont ramenees sur une barre commune.
    """
    pins, seen = [], set()
    for n in nums:
        p = part.pin(n)
        if (p.x, p.y) not in seen:
            seen.add((p.x, p.y))
            pins.append(p)
    if len(pins) == 1:
        cx(sh, pins[0], spec, stub)
        return
    net = spec[1:] if spec[0] in '@$' else spec
    pick = 'high' if (spec.startswith('@') and spec[1:] not in GNDISH) else 'low'
    end = sh.bar(pins, net, offset, pick)
    d = (round(pins[0].dx), round(pins[0].dy))
    cx(sh, kigen.Pin(end[0], end[1], d[0], d[1], '', '', 'passive'), spec, stub)


def flag_net(sh, net, x, y, glob=True):
    """PWR_FLAG raccorde a un net nomme (le net n a pas de symbole d alim)."""
    sh.power_at('PWR_FLAG', (x, y), 'power')
    sh.wire((x, y), (x, y + 5.08), net)
    (sh.glabel_at if glob else sh.label_at)(net, (x, y + 5.08), (0, 1))

def flag(sh, rail, x, y):
    """Rail + PWR_FLAG cote a cote, pour satisfaire l'ERC."""
    rot = 0 if rail in GNDISH else 180
    sh.power_at(rail, (x, y), PWRLIB[rail], rot=rot)
    sh.wire((x, y), (x + 5.08, y), rail)
    sh.power_at('PWR_FLAG', (x + 5.08, y), 'power', rot=180)

# --------------------------------------------------------------- deux-pattes
def vert(sh, lib_id, ref, val, x, y, top, bot, fp, fields=None, dnp=False):
    """Composant vertical : broche 1 en haut, broche 2 en bas."""
    p = sh.place(lib_id, ref, val, x, y, fp=fp, fields=fields, dnp=dnp,
                 fjust='left',
                 ref_at=(x + 3.6, y - 1.27), val_at=(x + 3.6, y + 1.27))
    cx(sh, p.pin('1'), top)
    cx(sh, p.pin('2'), bot)
    return p

def horiz(sh, lib_id, ref, val, x, y, left, right, fp, fields=None, dnp=False):
    p = sh.place(lib_id, ref, val, x, y, fp=fp, fields=fields, dnp=dnp,
                 ref_at=(x, y - 5.08), val_at=(x, y - 2.54))
    a, b = p.pin('1'), p.pin('2')
    if a.x > b.x:
        a, b = b, a
    cx(sh, a, left)
    cx(sh, b, right)
    return p

FLD_OFF = {C08: 2.6, C1210: 3.0, R08: 2.6, R12: 2.9,
           CPOL: 4.3, 'Capacitor_SMD:CP_Elec_8x10': 5.3,
           'Resistor_SMD:R_2512_6332Metric': 4.0}
R_POWER = {R06: '63mW', 'Resistor_SMD:R_0603_1608Metric': '100mW',
           R08: '125mW', R12: '250mW',
           'Resistor_SMD:R_2512_6332Metric': '1W'}


def C(sh, ref, val, x, y, top, bot, fp=C06, fields=None):
    """Condensateur : Value nue, champ Voltage visible, Dielectric masque.

    0402 par defaut ; si la valeur ou la tension demandee n existe pas
    proprement dans ce boitier, repli automatique en 0603.
    """
    volt = None
    if '/' in val:
        val, volt = [t.strip() for t in val.split('/', 1)]
    unit = 'p' if 'p' in val else 'n' if 'n' in val else 'u'
    if volt is None:
        volt = {'p': '50V', 'n': '25V'}.get(unit) or \
               ('16V' if val == '1uF' else '10V' if val.startswith('2u2') else '25V')
    if fp == C06:
        v = int(volt.rstrip('V'))
        fits = (unit == 'p' and v <= 50) or \
               (unit == 'n' and v <= (25 if val == '100nF' else 50)) or \
               (val == '1uF' and v <= 16) or (val.startswith('2u2') and v <= 10)
        if not fits:
            fp = C0603
    if fp in (CPOL, 'Capacitor_SMD:CP_Elec_8x10'):
        diel = 'ALU'
    elif unit == 'p':
        diel = 'C0G'
    elif unit == 'u' or fp == C1210:
        diel = 'X5R'
    else:
        diel = 'X7R'
    o = FLD_OFF.get(fp, 2.3)
    p = sh.place('Device:C', ref, val, x, y, fp=fp, fields=fields, fjust='left',
                 ref_at=(x + o, y - 2.54), val_at=(x + o, y),
                 extra=[('Voltage', volt, (x + o, y + 2.54), False),
                        ('Dielectric', diel, (x + o, y + 5.08), True)])
    cx(sh, p.pin('1'), top)
    cx(sh, p.pin('2'), bot)
    return p


def R(sh, ref, val, x, y, top, bot, fp=R06, fields=None, dnp=False):
    """Resistance : Value nue, champ Power visible."""
    power = R_POWER.get(fp, '100mW')
    if '/' in val:
        val, power = [t.strip().replace(' ', '') for t in val.split('/', 1)]
    o = FLD_OFF.get(fp, 2.3)
    p = sh.place('Device:R', ref, val, x, y, fp=fp, fields=fields, dnp=dnp,
                 fjust='left',
                 ref_at=(x + o, y - 2.54), val_at=(x + o, y),
                 extra=[('Power', power, (x + o, y + 2.54), False)])
    cx(sh, p.pin('1'), top)
    cx(sh, p.pin('2'), bot)
    return p

def Rh(sh, ref, val, x, y, left, right, fp=R06, fields=None):
    return R(sh, ref, val, x, y, left, right, fp, fields)

def tp(sh, ref, net, x, y, glob=True):
    p = sh.place('Connector:TestPoint', ref, net, x, y, fp=TP, hide_value=True,
                 ref_at=(x - 1.27, y - 3.05), val_at=(x + 2.54, y - 1.27))
    cx(sh, p.pin('1'), ('$' + net) if glob else net)
    return p

def nmos_switch(sh, ref, x, y, gate_net, drain, rref, rg='100R', rgd='100k'):
    """AO3400A en commutation basse : serie de grille et rappel a la masse."""
    q_ = sh.place('Transistor_FET:AO3400A', ref, 'AO3400A', x, y, fp=SOT23,
                  ref_at=(x + 7.62, y - 2.54), val_at=(x + 7.62, y))
    gnode = f'{ref}_G'
    cx(sh, q_.pin('G'), gnode)
    cx(sh, q_.pin('S'), '@GND')
    cx(sh, q_.pin('D'), drain)
    r1, r2 = rref
    Rh(sh, r1, rg, x - 30, y, gate_net, gnode)
    R(sh, r2, rgd, x - 16, y + 18, gnode, '@GND')
    return q_



# =====================================================================
#  01 - Alimentation, charge USB-C, protections
# =====================================================================
def sheet_power():
    sh = Sheet(LIB, 'Alimentation', '01-power.kicad_sch', paper='A3',
               title='UsainBot - Alimentation, charge USB-C, protections',
               rev=REV, date=DATE, company=COMPANY,
               comments=('Pack 2S LiFePO4 - bus VBAT 5,0 a 7,3 V',
                         'Chargeur elevateur BQ25887 place en amont de l interrupteur'))

    # ---------------------------------------------------------- USB-C
    sh.box(16, 24, 76, 92, 'A. Entree USB-C  -  charge, DFU, port serie')
    j1 = sh.place('Connector:USB_C_Receptacle_USB2.0_16P', 'J101', 'TYPE-C-31-M-12',
                  40, 62, fp='Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',
                  fields={'LCSC': 'C165948'}, ref_at=(40, 34), val_at=(58, 92))
    cx_bar(sh, j1, ('A1', 'B1', 'A12', 'B12', 'SH'), '@GND')
    cx_bar(sh, j1, ('A4', 'B4', 'A9', 'B9'), 'VBUS_IN')
    cx_bar(sh, j1, ('A6', 'B6'), 'USB_DP_C')
    cx_bar(sh, j1, ('A7', 'B7'), 'USB_DM_C')
    cx(sh, j1.pin('A5'), 'CC1');       cx(sh, j1.pin('B5'), 'CC2')
    cx(sh, j1.pin('A8'), 'NC');        cx(sh, j1.pin('B8'), 'NC')
    R(sh, 'R101', '5k1', 24, 102, 'CC1', '@GND')
    R(sh, 'R102', '5k1', 36, 102, 'CC2', '@GND')
    sh.note('CC1/CC2 : sans les deux 5,1 k aucun\nchargeur ne delivre le 5 V.', 50, 108, 1.0)

    # ---------------------------------------------------------- ESD USB
    sh.box(100, 24, 60, 46, 'B. Protection ESD')
    u1 = sh.place('Power_Protection:USBLC6-2SC6', 'U101', 'USBLC6-2SC6', 128, 44,
                  fp='Package_TO_SOT_SMD:SOT-23-6', ref_at=(128, 30), val_at=(128, 60))
    cx(sh, u1.pin('1'), 'USB_DP_C');  cx(sh, u1.pin('6'), '$USB_DP')
    cx(sh, u1.pin('3'), 'USB_DM_C');  cx(sh, u1.pin('4'), '$USB_DM')
    cx(sh, u1.pin('5'), 'VBUS_IN');   cx(sh, u1.pin('2'), '@GND')
    sh.note('Les paires 1/6 et 3/4 sont reliees en interne :\nle signal traverse le boitier.', 100, 68, 1.0)

    # ---------------------------------------------------------- chargeur
    sh.box(100, 78, 116, 168, 'C. Chargeur elevateur 2S  -  BQ25887')
    u2 = sh.place('Battery_Management:BQ25887RGE', 'U102', 'BQ25887RGER', 150, 150,
                  fp='Package_DFN_QFN:HVQFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm_ThermalVias',
                  fields={'LCSC': 'C2761614'}, ref_at=(150, 106), val_at=(150, 180))
    cx_bar(sh, u2, ('19', '20', '25'), '@GND')
    cx(sh, u2.pin('23'), 'VBUS_IN')                       # VBUS
    cx_bar(sh, u2, ('21', '22'), 'PMID')
    cx_bar(sh, u2, ('17', '18'), 'SW_CHG')
    cx_bar(sh, u2, ('15', '16'), 'SNS_CHG')
    cx_bar(sh, u2, ('13', '14'), '@VPACK')
    cx(sh, u2.pin('12'), 'BTST')
    cx(sh, u2.pin('11'), 'REGN')
    cx(sh, u2.pin('9'),  'MID_R')                          # via 300 ohm
    cx(sh, u2.pin('10'), 'CBSET_R')                        # via R de bilan
    cx(sh, u2.pin('8'),  'ILIM')
    cx(sh, u2.pin('7'),  'TS')
    cx(sh, u2.pin('24'), '$GND')                           # PSEL bas = adaptateur
    cx(sh, u2.pin('4'),  '$SDA2')
    cx(sh, u2.pin('5'),  '$SCL2')
    cx(sh, u2.pin('6'),  '$CHG_INT')
    cx(sh, u2.pin('3'),  'CD')
    cx(sh, u2.pin('2'),  'CHG_STAT')
    cx(sh, u2.pin('1'),  'CHG_PG')

    # etage de puissance du chargeur
    C(sh, 'C101', '1uF/25V', 106, 92, 'VBUS_IN', '@GND', C06)
    C(sh, 'C102', '22uF/25V', 116, 92, 'PMID', '@GND', C1210)
    C(sh, 'C103', '22uF/25V', 126, 92, 'PMID', '@GND', C1210)
    horiz(sh, 'Device:L', 'L101', '1uH / 4 A', 190, 88, 'PMID', 'SW_CHG',
          'Inductor_SMD:L_Taiyo-Yuden_NR-30xx')
    C(sh, 'C104', '47nF', 204, 88, 'BTST', 'SW_CHG', C06)
    C(sh, 'C105', '4u7F', 106, 196, 'REGN', '@GND', C08)
    C(sh, 'C106', '22uF/25V', 190, 112, 'SNS_CHG', '@GND', C1210)
    C(sh, 'C107', '22uF/25V', 204, 112, 'SNS_CHG', '@GND', C1210)
    C(sh, 'C108', '10uF/25V', 190, 132, '@VPACK', '@GND', C08)
    R(sh, 'R103', '383R', 122, 196, 'ILIM', '@GND')
    sh.note('IIN_max = KILIM / RILIM ~ 2,4 A', 136, 214, 1.0)

    # TS fige par le diviseur : pas de thermistance dans le pack
    R(sh, 'R104', '5k23', 106, 214, 'REGN', 'TS')
    R(sh, 'R105', '30k1', 122, 214, 'TS', '@GND')
    sh.note('Le diviseur emule un 103AT a 25 C : la fenetre de temperature\n'
            'est neutralisee, le pack n embarque pas de NTC.', 104, 228, 1.0)

    # equilibrage / point milieu
    Rh(sh, 'R106', '300R', 172, 168, 'PACK_MID', 'MID_R')
    R(sh, 'R107', '10R / 1W', 190, 168, 'PACK_MID', 'CBSET_R',
      'Resistor_SMD:R_2512_6332Metric')
    sh.note('R107 fixe le courant d equilibrage (400 mA max).', 158, 186, 1.0)

    # temoins et inhibition
    R(sh, 'R108', '10k', 106, 112, '@+3V3', 'CHG_STAT')
    R(sh, 'R109', '10k', 124, 112, '@+3V3', 'CHG_PG')
    horiz(sh, 'Device:LED', 'D101', 'vert - charge', 122, 142, 'CHG_STAT', 'CHG_LED_A', LED06)
    R(sh, 'R110', '2k2', 106, 128, '@+3V3', 'CHG_LED_A')
    R(sh, 'R111', '100k', 106, 160, 'REGN', 'CD')
    nmos_switch(sh, 'Q101', 178, 200, '$CHG_CD_EN', 'CD', rref=('R112', 'R113'))
    sh.note('CD haut = charge inhibee. La grille est au 0 V tant que le MCU\n'
            'n a pas ecrit VCELLREG : un pack LiFePO4 ne voit jamais le profil\n'
            'Li-ion par defaut (4,2 V/cellule), meme carte eteinte.', 140, 240, 1.0)
    return sh


def sheet_power_b(sh):
    # ------------------------------------------------- pack, coupure, inversion
    sh.box(220, 24, 190, 104, 'D. Pack 2S : puissance et equilibrage, interrupteur general')
    j2 = sh.place('Connector_Generic:Conn_01x02', 'J102', 'Pack 2S - puissance',
                  236, 46, fp='Connector_AMASS:AMASS_XT30U-M_1x02_P5.0mm_Vertical',
                  ref_at=(226, 38), val_at=(226, 58))
    cx(sh, j2.pin('1'), '@VPACK')      # B+
    cx(sh, j2.pin('2'), '@GND')        # B-
    j4 = sh.place('Connector_Generic:Conn_01x03', 'J104', 'Pack 2S - equilibrage',
                  272, 46, fp='Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical',
                  ref_at=(262, 38), val_at=(262, 60))
    # troncons de trois longueurs : les coudes des deux rails tombent sinon
    # tous deux sur la ligne de la broche du milieu, et court-circuitent B+
    # sur B- sans que rien ne le signale a l ecran.
    cx(sh, j4.pin('1'), '@GND', 7.62)       # B- (fil noir de la nappe)
    cx(sh, j4.pin('2'), 'PACK_MID', 2.54)   # point milieu (equilibrage BQ25887)
    cx(sh, j4.pin('3'), '@VPACK', 15.24)    # B+


    vert(sh, 'Device:Fuse', 'F101', '12 A', 316, 46, '@VPACK', 'VBAT_SW_IN', R12)

    # ------------------------------- mise sous tension par bouton poussoir
    # Une impulsion amorce, le microcontroleur se tient lui-meme, et c est lui
    # qui coupe. L interrupteur a glissiere qui etait ici demandait une place
    # au bord de carte que le pack, l equilibrage et les fils de l ESC ont
    # fini par prendre - et il ne savait pas eteindre proprement : couper le
    # 3,3 V sous les pieds du firmware n a jamais rien ecrit dans la flash.
    R(sh, 'R125', '10k', 228, 70, 'VBAT_SW_IN', 'BTN_N')
    R(sh, 'R127', '470k', 248, 70, 'BTN_N', '$PWR_BTN')
    R(sh, 'R128', '220k', 268, 70, '$PWR_BTN', '@GND')
    C(sh, 'C122', '100nF', 286, 70, '$PWR_BTN', '@GND')
    sw1 = sh.place('Switch:SW_Push', 'SW101', 'MARCHE / ARRET', 232, 102,
                   fp='Button_Switch_SMD:SW_SPST_B3U-1000P',
                   ref_at=(232, 94), val_at=(232, 98))
    cx(sh, sw1.pin('1'), 'BTN_N')
    cx(sh, sw1.pin('2'), '@GND')
    horiz(sh, 'Device:D_Schottky', 'D106', 'BAT54', 272, 102, 'PWR_G', 'BTN_N',
          'Diode_SMD:D_SOD-323')
    C(sh, 'C123', '1uF/16V', 300, 92, 'PWR_G', '@GND', C06)
    nmos_switch(sh, 'Q104', 390, 94, '$PWR_HOLD', 'PWR_G',
                rref=('R124', 'R126'))

    for qref, qx in (('Q102', 348), ('Q103', 388)):
        q_ = sh.place('Pacabot:AO4407A', qref, 'AO4407A', qx, 62,
                      fp='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
                      ref_at=(qx, 44), val_at=(qx, 48))
        cx_bar(sh, q_, ('1', '2', '3'), 'VBAT_SW_IN')     # source cote pack
        cx_bar(sh, q_, ('5', '6', '7', '8'), '@VBAT')     # drain cote charge
        cx(sh, q_.pin('4'), 'PWR_G')
    R(sh, 'R114', '100k', 340, 80, 'PWR_G', 'VBAT_SW_IN')
    sh.note('Pack : XT30 vertical pour le courant, JST-XH pour la nappe\n'
            'd equilibrage qui apporte le point milieu au BQ25887. Coupure par\n'
            'deux canaux P en parallele (Rds/2), grille rappelee a la source\n'
            'par R114 : coupe par defaut, aucune fuite de grille.\n'
            'MISE SOUS TENSION PAR BOUTON POUSSOIR. L appui tire la grille au\n'
            '0 V par D106 et les FET conduisent. Le firmware met PE0 a 1 des le\n'
            'demarrage : Q104 tient la grille, le bouton peut etre relache. Il\n'
            'lit ensuite le bouton sur PE1 (diviseur 470k/220k, 2,3 V au plein\n'
            'du pack) et coupe en relachant PE0 - apres avoir ferme la flash,\n'
            'ce qu un interrupteur ne savait pas faire. C123 donne 100 ms de\n'
            'retombee : un reset du MCU ne coupe pas l alimentation.\n'
            'A l arret : 7,3 V / 700 k, soit 10 uA.', 296, 245, 1.0)
    horiz(sh, 'Device:D_TVS', 'D102', 'SMBJ9.0A', 300, 118, '@VBAT', '@GND', 'Diode_SMD:D_SMB')
    C(sh, 'C109', '100uF/16V', 330, 118, '@VBAT', '@GND', CPOL)
    C(sh, 'C110', '100nF', 344, 118, '@VBAT', '@GND', C06)
    sh.note('Ecretage du freinage regeneratif : a 3 m/s, un arret a fond\n'
            'renvoie toute l energie cinetique dans un pack deja plein.', 236, 126, 1.0)

    # ------------------------------------------------------------- buck 3,3 V
    sh.box(220, 140, 190, 84, 'E. Convertisseur 3,3 V / 2 A  -  TPS62933')
    u3 = sh.place('Regulator_Switching:TPS62933', 'U103', 'TPS62933DRLR', 290, 176,
                  fp='Package_TO_SOT_SMD:SOT-583-8', fields={'LCSC': 'C3200405'},
                  ref_at=(290, 158), val_at=(290, 162))
    cx(sh, u3.pin('VIN'), '@VBAT')
    cx(sh, u3.pin('GND'), '@GND')
    cx(sh, u3.pin('SW'),  'SW_BUCK')
    cx(sh, u3.pin('BST'), 'BST_BUCK')
    cx(sh, u3.pin('FB'),  'FB_BUCK')
    cx(sh, u3.pin('RT'),  'RT_BUCK')
    cx(sh, u3.pin('SS'),  'SS_BUCK')
    cx(sh, u3.pin('EN'),  'EN_BUCK')
    C(sh, 'C111', '10uF/25V', 232, 156, '@VBAT', '@GND', C1210)
    C(sh, 'C112', '10uF/25V', 244, 156, '@VBAT', '@GND', C1210)
    C(sh, 'C113', '100nF', 258, 156, '@VBAT', '@GND', C06)
    R(sh, 'R115', '100k', 232, 200, '@VBAT', 'EN_BUCK')
    C(sh, 'C114', '100nF', 262, 200, 'BST_BUCK', 'SW_BUCK', C06)
    C(sh, 'C115', '10nF', 272, 206, 'SS_BUCK', '@GND', C06)
    R(sh, 'R116', '42k2', 282, 206, 'RT_BUCK', '@GND')
    horiz(sh, 'Device:L', 'L102', '4u7H / 3 A', 330, 164, 'SW_BUCK', '@+3V3',
          'Inductor_SMD:L_Taiyo-Yuden_NR-40xx')
    C(sh, 'C116', '22uF/10V', 348, 178, '@+3V3', '@GND', C08)
    C(sh, 'C117', '22uF/10V', 358, 178, '@+3V3', '@GND', C08)
    C(sh, 'C118', '100nF', 368, 178, '@+3V3', '@GND', C06)
    R(sh, 'R117', '100k', 330, 190, '@+3V3', 'FB_BUCK')
    R(sh, 'R118', '31k6', 330, 208, 'FB_BUCK', '@GND')
    sh.note('VOUT = 0,8 V x (1 + R117/R118) = 3,33 V.\n'
            'R116 fixe la frequence (~500 kHz) : a recaler sur la courbe fSW(RT).',
            234, 222, 1.0)

    # ------------------------------------------------- 3V3A et mesure de bord
    sh.box(16, 124, 80, 152, 'F. Rail analogique et surveillance de bord')
    vert(sh, 'Device:FerriteBead_Small', 'FB101', '600R @ 100 MHz', 32, 144,
         '@+3V3', '@+3V3A', 'Inductor_SMD:L_0805_2012Metric')
    C(sh, 'C119', '10uF/10V', 54, 152, '@+3V3A', '@GND', C08)
    C(sh, 'C120', '100nF', 68, 152, '@+3V3A', '@GND', C06)
    sh.note('Filtre en Pi, pas un second regulateur : la barrette\n'
            'et VREF+ partagent exactement le meme potentiel,\n'
            'donc la mesure est ratiometrique et l ondulation\n'
            'du buck s annule.', 18, 166, 1.0)
    R(sh, 'R119', '22k', 32, 190, '@VBAT', '$VBAT_SENSE')
    R(sh, 'R120', '10k', 32, 208, '$VBAT_SENSE', '@GND')
    C(sh, 'C121', '100nF', 54, 208, '$VBAT_SENSE', '@GND', C06)
    sh.note('7,3 V -> 2,28 V, directement sur PC0. Le 74HC4051 qui multiplexait\n'
            'cette mesure avec les deux IPROPI a disparu avec le passage au\n'
            'LQFP144 : chacun des trois a desormais son entree, et surtout les\n'
            'deux courants moteur se lisent au meme instant (PF11 sur ADC1,\n'
            'PF13 sur ADC2, meme numero de voie). Thevenin 6,9 k, C121 sert de\n'
            'reservoir de charge pour l echantillonnage.',
            18, 232, 1.0)
    sh.note('VPACK est deja pilote par la broche BAT du chargeur :\n'
            'il ne prend pas de drapeau.', 18, 242, 1.0)
    for rail, y in [('VBAT', 254), ('+3V3', 262), ('+3V3A', 270), ('GND', 278)]:
        flag(sh, rail, 26, y)
    flag_net(sh, 'VBUS_IN', 58, 254, glob=False)

    return sh


def rail_bar(sh, pins, rail, offset=7.62):
    """Relie plusieurs broches paralleles a un seul symbole d alimentation."""
    pins = sorted(pins, key=lambda p: p.x)
    y = pins[0].y + pins[0].dy * offset
    for p in pins:
        sh.wire((p.x, p.y), (p.x, y), rail)
    sh.wire((pins[0].x, y), (pins[-1].x, y), rail)
    for p in pins[1:-1]:
        sh.junction((p.x, y))
    mid = pins[len(pins) // 2]
    sh.power_at(rail, (mid.x, y), PWRLIB[rail])
    sh.junction((mid.x, y))


# Brochage du STM32H723ZGT6 (LQFP144), donne PAR NOM DE PORT et non par
# numero de broche. C'est ce qui a rendu le passage du LQFP100 au LQFP144
# sur : 85 des 87 affectations se sont transposees telles quelles, parce
# qu'une affectation est un choix de PORT (PA0 porte la voie de ligne 00),
# jamais un choix de patte. Une table numerotee aurait demande de recopier
# 144 lignes a la main, et une erreur de brochage ne se voit pas a l'ERC.
# Les broches absentes de cette table sont declarees non connectees
# automatiquement plus bas : aucune ne peut etre oubliee.
MCU_PORTS = {
    # --- service et horloge ------------------------------------------------
    'NRST': 'NRST',          'BOOT0': 'BOOT0',
    'PH0': 'OSC_IN',         'PH1': 'OSC_OUT',
    # --- alimentation et bouton --------------------------------------------
    'PE0': '$PWR_HOLD',      'PE1': '$PWR_BTN',
    # --- ponts moteur, codeurs ---------------------------------------------
    'PE9': '$MOT_L_IN1',     'PE11': '$MOT_L_IN2',
    'PE13': '$MOT_R_IN1',    'PE14': '$MOT_R_IN2',
    'PD0': '$MOT_L_nSLEEP',  'PD1': '$MOT_R_nSLEEP',
    'PD3': '$MOT_L_nFAULT',  'PD4': '$MOT_R_nFAULT',
    'PB4(NJTRST)': '$ENC_L_A', 'PB5': '$ENC_L_B',
    'PC6': '$ENC_R_A',       'PC7': '$ENC_R_B',
    # --- barrette de ligne : douze voies d ADC, une par capteur ------------
    'PA0': '$LINE_00', 'PA1': '$LINE_01', 'PA2': '$LINE_02', 'PA3': '$LINE_03',
    'PA4': '$LINE_04', 'PA5': '$LINE_05', 'PA6': '$LINE_06', 'PA7': '$LINE_07',
    'PB0': '$LINE_08', 'PB1': '$LINE_09', 'PC4': '$LINE_10', 'PC5': '$LINE_11',
    'PE7': '$IR_BANK_A',     'PE8': '$IR_BANK_B',
    # --- telemetrie : emission et trois voies de reception -----------------
    'PE2': '$TX_FL',         'PB2': '$TX_F',         'PC13': '$TX_L',
    'PC1': '$RX_F',          'PC2_C': '$RX_FL',      'PC3_C': '$RX_L',
    # --- surveillance analogique DIRECTE (le multiplexeur a disparu) -------
    # PF11 est ADC1_INP2 et PF13 ADC2_INP2 : meme numero de voie sur DEUX
    # convertisseurs, donc les deux courants moteur se lisent au meme
    # instant en mode double simultane. Le 74HC4051 l'interdisait par
    # construction - on lisait un moteur, on commutait, on attendait
    # l'etablissement, on lisait l'autre.
    'PF11': '$IPROPI_L',     'PF13': '$IPROPI_R',    'PC0': '$VBAT_SENSE',
    # --- inertie, flash, radio, USB ----------------------------------------
    'PE6': '$IMU_INT1',
    'PB12': '$IMU_nCS', 'PB13': '$IMU_SCK', 'PB14': '$IMU_MISO', 'PB15': '$IMU_MOSI',
    'PD2': '$FLASH_nCS',
    'PC10': '$FLASH_SCK', 'PC11': '$FLASH_MISO', 'PC12': '$FLASH_MOSI',
    'PA8': '$BLE_PWR_EN', 'PA9': '$BLE_TX', 'PA10': '$BLE_RX',
    'PA11': '$USB_DM', 'PA12': '$USB_DP',
    # --- IHM, turbine, chargeur, eclairage ---------------------------------
    'PE10': '$SW_UP', 'PE12': '$SW_DOWN', 'PE15': '$SW_LEFT',
    'PD10': '$SW_RIGHT', 'PD13': '$SW_PUSH', 'PD14': '$START_BTN',
    'PB10': '$SCL2', 'PB11': '$SDA2',
    'PB8': '$ESC_PWM', 'PB9': '$BUZZER',
    'PE3': '$CHG_CD_EN', 'PE4': '$CHG_INT', 'PE5': '$TRACK_EN',
    # --- debogage ----------------------------------------------------------
    'PA13(JTMS': 'SWDIO', 'PA14(JTCK': 'SWCLK', 'PB3(JTDO': 'SWO',
}
# broches d alimentation, traitees a part (VSS est empile sur une seule
# position dans le symbole : un seul raccordement les relie toutes)
MCU_ALIM = {'VDDA': '@+3V3A', 'VREF+': '@+3V3A', 'VSSA': '@GND',
            'VBAT': '@+3V3', 'VSS': '@GND',
            'VDD33USB': '@+3V3',    # separee sur le 144, absente du 100
            'PDR_ON': '@+3V3'}      # a VDD : reset interne actif



# =====================================================================
#  02 - Microcontroleur, horloge, debogage
# =====================================================================
def sheet_mcu():
    sh = Sheet(LIB, 'MCU', '02-mcu.kicad_sch', paper='A3',
               title='UsainBot - STM32H723ZGT6, horloge et debogage',
               rev=REV, date=DATE, company=COMPANY,
               comments=('Mode LDO seul (AN5312) : le LQFP144 n expose pas les broches SMPS',
                         'Passe du LQFP100 au LQFP144 le 4 septembre : 12 entrees ADC de plus'))
    u = sh.place('MCU_ST_STM32H7:STM32H723ZGTx', 'U201', 'STM32H723ZGT6', 200, 152,
                 fp='Package_QFP:LQFP-144_20x20mm_P0.5mm', fields={'LCSC': 'C730146'},
                 ref_at=(200, 52), val_at=(200, 258),
                 datasheet='https://www.st.com/resource/en/datasheet/stm32h723zg.pdf')

    vus = set()
    for nom, spec in MCU_PORTS.items():
        p = u.pin(nom)
        cx(sh, p, spec, stub=5.08)
        vus.add(p.num)

    # --- alimentations
    vdd = [p for p in u.pins() if p.name == 'VDD']
    rail_bar(sh, vdd, '+3V3', 10.16)
    vus |= {p.num for p in vdd}
    for nom, spec in MCU_ALIM.items():
        p = u.pin(nom)
        cx(sh, p, spec, stub=5.08 if nom in ('VDD33USB', 'PDR_ON') else 2.54)
        vus |= {q.num for q in u.pins() if q.name == nom}
    for num, net in (('71', 'VCAP1'), ('106', 'VCAP2')):   # deux positions
        cx(sh, u.pin(num), net)
        vus.add(num)

    # --- tout le reste est explicitement non connecte : aucune broche du
    #     boitier ne peut etre oubliee en silence
    libres = []
    for p in u.pins():
        if p.num in vus:
            continue
        sh.nc(p)
        libres.append(p.name)

    # --- decouplage : un 100 nF par broche VDD, plus les rails analogiques
    sh.box(268, 16, 142, 96,
           'Decouplage  -  un 100 nF par broche VDD (elles sont onze)')
    cent = ['C201', 'C202', 'C203', 'C204', 'C205', 'C207',
            'C217', 'C218', 'C219', 'C220', 'C221']
    for i, ref in enumerate(cent):
        C(sh, ref, '100nF', 282 + (i % 4) * 32, 36 + (i // 4) * 26,
          '@+3V3', '@GND')
    C(sh, 'C206', '4u7F/10V', 378, 88, '@+3V3', '@GND', C08)

    sh.box(268, 120, 142, 74, 'Rails analogiques, USB et VCAP')
    C(sh, 'C208', '100nF', 282, 140, '@+3V3A', '@GND')
    C(sh, 'C209', '1uF', 314, 140, '@+3V3A', '@GND')
    C(sh, 'C210', '100nF', 346, 140, '@+3V3A', '@GND')
    C(sh, 'C211', '1uF', 378, 140, '@+3V3A', '@GND')
    C(sh, 'C222', '100nF', 282, 168, '@+3V3', '@GND')
    C(sh, 'C212', '2u2F/10V', 320, 168, 'VCAP1', '@GND', C08)
    C(sh, 'C213', '2u2F/10V', 358, 168, 'VCAP2', '@GND', C08)
    sh.note('C208/C209 : VDDA.  C210/C211 : VREF+.  C222 : VDD33USB, broche\n'
            'separee sur le LQFP144 alors que le LQFP100 la reliait en interne.\n'
            'VCAP : 2,2 uF ceramique, ESR < 2 ohm, tres pres du boitier.\n'
            'PDR_ON est tiree a VDD : reset interne d alimentation actif.',
            270, 192, 1.0)

    # --- reset et boot
    sh.box(16, 62, 100, 42, 'Reset et selection du mode de demarrage')
    R(sh, 'R201', '10k', 28, 78, '@+3V3', 'NRST')
    C(sh, 'C214', '100nF', 42, 78, 'NRST', '@GND')
    R(sh, 'R202', '10k', 64, 78, 'BOOT0', '@GND')
    R(sh, 'R203', '10k', 78, 78, '@+3V3', 'BOOT0', R06, dnp=True)
    swr = sh.place('Switch:SW_Push', 'SW603', 'RESET', 100, 78,
                   fp='Button_Switch_SMD:SW_SPST_B3U-1000P',
                   ref_at=(100, 68), val_at=(100, 72))
    cx(sh, swr.pin('1'), 'NRST'); cx(sh, swr.pin('2'), '$GND')
    sh.note('R203 non montee : la poser force le bootloader DFU.', 20, 100, 1.0)

    # --- horloge
    sh.box(16, 112, 100, 54, 'Horloge HSE 25 MHz  -  obligatoire pour l USB')
    y1 = sh.place('Device:Crystal_GND24_Small', 'Y201', '25 MHz / 10 ppm', 56, 130,
                  fp='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',
                  ref_at=(56, 122), val_at=(56, 140))
    cx(sh, y1.pin('1'), 'OSC_IN')
    cx(sh, y1.pin('3'), 'XTAL_OUT')
    cx_bar(sh, y1, ('2', '4'), '@GND', offset=5.08)
    C(sh, 'C215', '10pF', 28, 152, 'OSC_IN', '@GND')
    C(sh, 'C216', '10pF', 84, 152, 'XTAL_OUT', '@GND')
    Rh(sh, 'R204', '220R', 96, 130, 'XTAL_OUT', 'OSC_OUT')
    sh.note('Charge a recaler sur le CL du quartz retenu :\nC = 2 x (CL - Cstray).', 20, 168, 1.0)

    # --- debogage
    sh.box(16, 176, 100, 62, 'Debogage SWD + SWO  -  Tag-Connect TC2030 (brochage Sp3ctra V4)')
    j = sh.place('Connector:TC2030', 'J201', 'TC2030-IDC-FP', 58, 206,
                 fp='Connector:Tag-Connect_TC2030-IDC-FP_2x03_P1.27mm_Vertical',
                 ref_at=(58, 186), val_at=(58, 228))
    for num, spec in [('1', '@+3V3'), ('2', 'SWO'), ('3', 'NRST'),
                      ('4', 'SWCLK'), ('5', 'SWDIO'), ('6', '$GND')]:
        cx(sh, j.pin(num), spec)
    sh.note('Empreinte seule, sans connecteur soude :\nla sonde se pose sur les pastilles.', 20, 234, 1.0)

    sh.note('Bilan : %d broches affectees, %d libres et marquees non connectees\n'
            'au schema. Le LQFP144 apporte les ports F et G, soit 32 E/S de plus\n'
            'et surtout DOUZE entrees ADC supplementaires (PF3 a PF14) : c est ce\n'
            'qui a permis de supprimer le multiplexeur 74HC4051 et de lire les\n'
            'deux courants moteur au meme instant.'
            % (len(MCU_PORTS) + len(MCU_ALIM) + 2, len(libres)), 16, 258, 1.1)
    return sh


# =====================================================================
#  03 - Ponts en H, moteurs, encodeurs
# =====================================================================
def sheet_motors():
    sh = Sheet(LIB, 'Moteurs', '03-motors.kicad_sch', paper='A3',
               title='UsainBot - Ponts en H DRV8874, moteurs GM12-N20 et encodeurs',
               rev=REV, date=DATE, company=COMPANY,
               comments=('PMODE haut = mode PWM IN1/IN2 : freinage actif et decroissance rapide',
                         'IPROPI recopie le courant moteur : calage, traction, coulometrie'))

    # reference de limitation commune aux deux ponts
    sh.box(16, 240, 268, 42, 'Reference de limitation de courant, commune aux deux ponts')
    R(sh, 'R301', '10k', 32, 254, '@+3V3', 'VREF_MOT')
    R(sh, 'R302', '6k8', 32, 272, 'VREF_MOT', '@GND')
    C(sh, 'C301', '100nF', 48, 272, 'VREF_MOT', '@GND')
    sh.note('VREF_MOT = 3,3 x 6,8/16,8 = 1,34 V.\n'
            'ITRIP = VREF / (AIPROPI x RIPROPI) = 1,34 / (450 uA/A x 1 k) ~ 3,0 A,\n'
            'soit environ deux fois le courant de calage du GM12-N20 a 6 V.\n'
            'Le seuil se change en retouchant R302 seule.', 70, 254, 1.0)

    for side, base, tag, refn in (('gauche', 68, 'L', 300), ('droit', 176, 'R', 350)):
        y = base
        u = sh.place('Pacabot:DRV8874PWPR', f'U{refn + 1}', 'DRV8874PWPR', 150, y,
                     fp='Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm',
                     fields={'LCSC': 'C1855818'},
                     ref_at=(150, y - 26), val_at=(150, y + 32),
                     datasheet='https://www.ti.com/lit/ds/symlink/drv8874.pdf')
        sh.box(16, y - 44, 394, 104, f'Moteur {side}  -  pont complet, 6 A crete, retour de courant')

        cx(sh, u.pin('1'),  f'$MOT_{tag}_IN1')
        cx(sh, u.pin('2'),  f'$MOT_{tag}_IN2')
        cx(sh, u.pin('3'),  f'$MOT_{tag}_nSLEEP')
        cx(sh, u.pin('4'),  f'$MOT_{tag}_nFAULT')
        cx(sh, u.pin('5'),  'VREF_MOT')
        cx(sh, u.pin('6'),  f'IPROPI_{tag}_RAW')
        cx(sh, u.pin('7'),  f'IMODE_{tag}')
        cx(sh, u.pin('16'), f'PMODE_{tag}')
        cx(sh, u.pin('11'), '@VBAT')
        cx(sh, u.pin('12'), f'VCP_{tag}')
        cx(sh, u.pin('13'), f'CPH_{tag}')
        cx(sh, u.pin('14'), f'CPL_{tag}')
        cx(sh, u.pin('8'),  f'MOT_{tag}_OUT1')
        cx(sh, u.pin('10'), f'MOT_{tag}_OUT2')
        for p in ('15', '9', '17'):
            cx(sh, u.pin(p), '@GND')

        # reseau de commande
        R(sh, f'R{refn + 3}', '100k', 62, y + 4, f'$MOT_{tag}_nSLEEP', '@GND')
        R(sh, f'R{refn + 4}', '10k', 78, y - 14, '@+3V3', f'$MOT_{tag}_nFAULT')
        R(sh, f'R{refn + 5}', '20k', 62, y + 26, f'IMODE_{tag}', '@GND')
        R(sh, f'R{refn + 6}', '10k', 78, y + 26, '@+3V3', f'PMODE_{tag}')
        # mesure de courant
        R(sh, f'R{refn + 7}', '1k', 30, y + 4, f'IPROPI_{tag}_RAW', '@GND')
        Rh(sh, f'R{refn + 8}', '100R', 46, y + 16, f'IPROPI_{tag}_RAW', f'$IPROPI_{tag}')
        C(sh, f'C{refn + 2}', '1nF', 30, y + 30, f'$IPROPI_{tag}', '@GND')
        # etage de puissance
        C(sh, f'C{refn + 3}', '100nF', 200, y - 30, '@VBAT', '@GND')
        C(sh, f'C{refn + 4}', '100uF/16V poly', 214, y - 30, '@VBAT', '@GND',
          'Capacitor_Tantalum_SMD:CP_EIA-7343-20_Kemet-V')
        C(sh, f'C{refn + 5}', '100nF', 228, y - 30, f'VCP_{tag}', '@VBAT')
        C(sh, f'C{refn + 6}', '22nF', 200, y - 12, f'CPH_{tag}', f'CPL_{tag}', C06)
        # connecteur moteur + encodeur
        j = sh.place('Pacabot:Motor_Faulhaber', f'J{refn + 1}',
                     'Moteur Faulhaber + IE2', 336, y,
                     fp='Connector_TE-Connectivity:'
                        'TE_Micro-MaTch_215079-6_2x03_P1.27mm_Vertical',
                     fields={'MPN': 'TE 7-215079-6'},
                     ref_at=(330, y - 12), val_at=(336, y + 12))
        cx(sh, j.pin('2'), f'MOT_{tag}_OUT1')     # M+  -  fil rouge
        cx(sh, j.pin('1'), f'MOT_{tag}_OUT2')     # M-
        cx(sh, j.pin('4'), '$+3V3')               # VDD encodeur
        cx(sh, j.pin('3'), '$GND')
        cx(sh, j.pin('6'), f'ENC_{tag}_A_RAW')
        cx(sh, j.pin('5'), f'ENC_{tag}_B_RAW')
        C(sh, f'C{refn + 7}', '100nF/50V', 380, y - 26,
          f'MOT_{tag}_OUT1', f'MOT_{tag}_OUT2', C08)
        Rh(sh, f'R{refn + 9}', '100R', 262, y + 22, f'ENC_{tag}_A_RAW', f'$ENC_{tag}_A')
        Rh(sh, f'R{refn + 10}', '100R', 282, y + 22, f'ENC_{tag}_B_RAW', f'$ENC_{tag}_B')
        C(sh, f'C{refn + 8}', '1nF', 302, y + 22, f'$ENC_{tag}_A', '@GND')
        C(sh, f'C{refn + 9}', '1nF', 316, y + 22, f'$ENC_{tag}_B', '@GND')
        sh.note('Nappe Faulhaber sur Micro-MaTch 215079-6 : impairs a gauche,\n'
                'fil rouge = M+. Fils moteur torsades, 100 nF aux bornes.', 250, y + 52, 1.0)
    return sh


# =====================================================================
#  04 - Barrette de ligne 12 voies
# =====================================================================
def sheet_line():
    sh = Sheet(LIB, 'Barrette', '04-line-array.kicad_sch', paper='A3',
               title='UsainBot - Barrette de ligne, 12 x ITR8307 au pas de 10 mm',
               rev=REV, date=DATE, company=COMPANY,
               comments=('Couverture +/-55 mm : voit les marques a 40 mm a droite',
                         'Emetteurs pulses en deux bancs : ambiante soustraite, diaphonie supprimee'))
    sh.note('Sequence declenchee par TIM6 a 2 kHz : tous emetteurs eteints (ambiante),\n'
            'puis banc A, puis banc B. La soustraction annule l eclairage de salle\n'
            '- exigence directe du chapitre 10 du reglement.', 18, 24, 1.2)
    sh.note('Les diodes sont alimentees en +3V3 et les phototransistors en +3V3A :\n'
            'les 120 mA d appel du banc ne traversent jamais la reference de l ADC.',
            18, 34, 1.2)

    cols = (62, 152, 242, 332)
    rows = (62, 122, 182)
    for i in range(12):
        x = cols[i % 4]
        y = rows[i // 4]
        bank = 'A' if i % 2 == 0 else 'B'
        line = f'$LINE_{i:02d}'
        u = sh.place('Pacabot:ITR8307', f'U{401 + i}', 'ITR8307/S17/TR8',
                     x, y, fp='Pacabot:ITR8307_dessous', fields={'LCSC': 'C81632'},
                     ref_at=(x, y - 7.62), val_at=(x, y + 8.89))
        cx(sh, u.pin('2'), f'IR_A{i:02d}')          # anode de la diode
        cx(sh, u.pin('1'), f'IR_BANK_{bank}_N')     # cathode -> banc commute
        cx(sh, u.pin('3'), '@+3V3A')                # collecteur
        cx(sh, u.pin('4'), line)                    # emetteur -> ADC
        R(sh, f'R{401 + i}', '100R', x - 26, y - 12, '@+3V3', f'IR_A{i:02d}')
        R(sh, f'R{421 + i}', '10k', x + 28, y + 10, line, '@GND')
        C(sh, f'C{401 + i}', '1nF', x + 40, y + 10, line, '@GND')

    sh.box(16, 216, 274, 62, 'Commutation des deux bancs d emetteurs')
    nmos_switch(sh, 'Q401', 120, 240, '$IR_BANK_A', 'IR_BANK_A_N', rref=('R441', 'R442'))
    nmos_switch(sh, 'Q402', 268, 240, '$IR_BANK_B', 'IR_BANK_B_N', rref=('R443', 'R444'))
    sh.note('Banc A : voies paires.        Banc B : voies impaires.', 150, 236, 1.2)
    sh.note('Le rapport cyclique sur la grille pilote le courant d emission :\n'
            'une garde au sol de 6 mm au lieu de 3 se rattrape en logiciel,\n'
            'sans retoucher le PCB.', 150, 262, 1.0)
    return sh


# =====================================================================
#  08 - Temoins de presence de ligne, un par capteur
# =====================================================================
def sheet_line_leds():
    sh = Sheet(LIB, 'Temoins de ligne', '08-line-leds.kicad_sch', paper='A3',
               title='UsainBot - Douze temoins de presence de ligne',
               rev=REV, date=DATE, company=COMPANY,
               comments=('PCA9685 sur I2C2 : douze PWM 12 bits sans consommer une broche de MCU',
                         'Chaque LED est posee au-dessus de son capteur, sur la moustache'))
    sh.note('Ce que l on regarde pendant un essai, ce n est pas un temoin d etat\n'
            'generique : c est ce que voit la barrette. Une LED par capteur, sur\n'
            'la moustache, a l aplomb du capteur qu elle rapporte - la ligne se\n'
            'lit d un coup d oeil sous le robot, et un capteur borgne se voit\n'
            'avant la course, pas apres.', 18, 22, 1.2)
    sh.note('Le rapport cyclique suit le signal : la LED s allume progressivement\n'
            'quand la ligne arrive sous le capteur. Un simple tout-ou-rien ne\n'
            'dirait pas si le capteur est au bord ou au centre du trait.',
            18, 44, 1.2)

    u = sh.place('Driver_LED:PCA9685PW', 'U105', 'PCA9685PW', 90, 150,
                 fp='Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm',
                 ref_at=(90, 88), val_at=(90, 214))
    cx(sh, u.pin('28'), '@+3V3')
    cx(sh, u.pin('14'), '@GND')
    cx(sh, u.pin('26'), '$SCL2')
    cx(sh, u.pin('27'), '$SDA2')
    cx_bar(sh, u, ('1', '2', '3', '4', '5', '24'), '@GND')   # adresse 0x40
    cx(sh, u.pin('23'), '$GND')          # OE actif bas : sorties toujours validees
    cx(sh, u.pin('25'), '$GND')          # pas d horloge externe
    for i in range(12):
        cx(sh, u.pin(str((6 + i) if i < 8 else (15 + i - 8))), f'LGN{i:02d}')
    for i in range(4):
        cx(sh, u.pin(str(19 + i)), 'NC')  # LED12 a LED15 en reserve
    C(sh, 'C124', '100nF', 140, 150, '@+3V3', '@GND')

    for i in range(12):
        x = 190 + (i % 3) * 76
        y = 44 + (i // 3) * 52
        R(sh, f'R{445 + i}', '1k', x, y, '@+3V3', f'LGN{i:02d}_A')
        horiz(sh, 'Device:LED', f'D{401 + i}', f'verte - capteur {i:02d}',
              x + 4, y + 30, f'LGN{i:02d}', f'LGN{i:02d}_A', LED06)
    sh.note('Adresse 0x40 (A0-A5 a la masse). Le bus I2C2 porte deja l ecran et\n'
            'le chargeur : douze voies font 52 octets, soit 1,2 ms a 400 kHz, en\n'
            'DMA hors de la boucle rapide. Quatre sorties restent libres.',
            18, 236, 1.0)
    return sh


# =====================================================================
#  05 - Telemetrie analogique et centrale inertielle
# =====================================================================
STATIONS = (('F',  'avant, 15 deg',         22),
            ('FL', 'avant-gauche, 45 deg', 150),
            ('L',  'gauche, 75 deg',       278))
# 15/45/75 : chaque visee garde ~15 deg d avance sur la normale, la balise
# est acquise avant d arriver a sa hauteur.


def sheet_sensors():
    sh = Sheet(LIB, 'Capteurs', '05-sensors.kicad_sch', paper='A2',
               title='UsainBot - Telemetrie analogique a detection synchrone, inertie',
               rev=REV, date=DATE, company=COMPANY,
               comments=('Trois stations identiques : plus aucun bus I2C dans la boucle critique',
                         'Couplage alternatif avant le gain, demodulation I/Q dans le firmware'))

    for k, (tag, vise, X) in enumerate(STATIONS):
        n = 500 + k * 20                      # bloc de references par station
        amp_ref = ('U501', 'U502', 'U504')[k]  # un boitier au pied de chaque photodiode
        Y = 26
        sh.box(X - 6, Y - 8, 122, 188, f'Station {tag}  -  {vise}')

        # -------- station couchee : les deux boitiers dans une empreinte --
        # Un seul symbole pour le couple TX/RX : l empreinte combinee
        # Telemetry_Duo_Coude porte les deux boitiers, le percage du
        # pare-soleil et ses deux pions ; deux symboles ne peuvent pas se
        # partager une empreinte.
        st = sh.place('Pacabot:Telemetry_Duo', f'TM{n + 1}', 'OPV302 + BPV10NF',
                      X + 42, Y + 30, fp='Pacabot:Telemetry_Duo_Coude',
                      ref_at=(X + 42, Y + 16), val_at=(X + 42, Y + 46))
        cx(sh, st.pin('1'), f'LAS_{tag}_K')      # TX cathode : cote MOSFET
        cx(sh, st.pin('2'), f'LAS_{tag}_A')      # TX anode : cote resistance
        cx(sh, st.pin('3'), '@+3V3A')            # RX cathode : polarisation
        cx(sh, st.pin('4'), f'PD_{tag}')         # RX anode : entree du TIA
        R(sh, f'R{n + 1}', '100R', X + 10, Y + 14, '@+3V3', f'LAS_{tag}_A')
        horiz(sh, 'Device:D_TVS', f'D{n + 3}', 'PESD3V3', X + 40, Y + 60,
              f'LAS_{tag}_K', '@GND', 'Diode_SMD:D_SOD-323')
        # passe-haut de grille : un GPIO fige ne peut pas laisser le laser
        # allume ; seule la porteuse 10-20 kHz traverse, le 100k de rappel
        # eteint la diode en ~1 ms.  La Schottky restaure les niveaux.
        horiz(sh, 'Device:C', f'C{n + 5}', '10nF', X + 56, Y + 4,
              f'$TX_{tag}', f'TXAC_{tag}', C06)
        horiz(sh, 'Device:D_Schottky', f'D{n + 4}', 'BAT54', X + 88, Y + 4,
              f'TXAC_{tag}', '@GND', 'Diode_SMD:D_SOD-323')
        nmos_switch(sh, f'Q{n + 1}', X + 100, Y + 28, f'TXAC_{tag}', f'LAS_{tag}_K',
                    rref=(f'R{n + 2}', f'R{n + 3}'))

        # -------- transimpedance ----------------------------------------
        t = sh.place('Amplifier_Operational:TLV9064', amp_ref, 'TLV9064',
                     X + 66, Y + 82, unit=1,
                     fp='Package_SO:TSSOP-14_4.4x5mm_P0.65mm',
                     ref_at=(X + 66, Y + 72), val_at=(X + 66, Y + 94))
        cx(sh, t.pin('-'), f'PD_{tag}')
        cx(sh, t.pin('+'), 'VREF_RX')
        cx(sh, out_pin(t), f'TIA_{tag}')
        R(sh, f'R{n + 4}', '220k', X + 66, Y + 62, f'PD_{tag}', f'TIA_{tag}')
        C(sh, f'C{n + 1}', '22pF', X + 88, Y + 62, f'PD_{tag}', f'TIA_{tag}')

        # -------- couplage alternatif puis gain -------------------------
        C(sh, f'C{n + 2}', '1nF', X + 18, Y + 122, f'TIA_{tag}', f'G_{tag}', C06)
        R(sh, f'R{n + 5}', '100k', X + 18, Y + 140, f'G_{tag}', 'VREF_MID')
        g = sh.place('Amplifier_Operational:TLV9064', amp_ref, 'TLV9064',
                     X + 66, Y + 128, unit=2,
                     fp='Package_SO:TSSOP-14_4.4x5mm_P0.65mm',
                     ref_at=(X + 66, Y + 118), val_at=(X + 66, Y + 140))
        cx(sh, g.pin('+'), f'G_{tag}')
        cx(sh, g.pin('-'), f'FB_{tag}')
        cx(sh, out_pin(g), f'AMP_{tag}')
        R(sh, f'R{n + 6}', '100k', X + 66, Y + 152, f'AMP_{tag}', f'FB_{tag}')
        R(sh, f'R{n + 7}', '910R', X + 88, Y + 152, f'FB_{tag}', f'CG_{tag}')
        C(sh, f'C{n + 3}', '1uF', X + 88, Y + 170, f'CG_{tag}', '@GND')
        Rh(sh, f'R{n + 8}', '1k', X + 104, Y + 128, f'AMP_{tag}', f'$RX_{tag}')
        C(sh, f'C{n + 4}', '4n7', X + 104, Y + 148, f'$RX_{tag}', '@GND')

    # ------------------------------------------------ references et alim
    sh.box(160, 218, 122, 68, 'References et alimentation des amplificateurs')
    R(sh, 'R561', '10k', 174, 236, '@+3V3A', 'VREF_RX')
    R(sh, 'R562', '2k2', 174, 254, 'VREF_RX', '@GND')
    C(sh, 'C561', '1uF', 192, 254, 'VREF_RX', '@GND', C06)
    R(sh, 'R563', '10k', 216, 236, '@+3V3A', 'VREF_MID_R')
    R(sh, 'R564', '10k', 216, 254, 'VREF_MID_R', '@GND')
    C(sh, 'C562', '1uF', 234, 254, 'VREF_MID_R', '@GND', C06)
    b = sh.place('Amplifier_Operational:TLV9064', 'U501', 'TLV9064', 262, 236, unit=4,
                 fp='Package_SO:TSSOP-14_4.4x5mm_P0.65mm',
                 ref_at=(262, 226), val_at=(262, 248))
    cx(sh, b.pin('+'), 'VREF_MID_R')
    cx(sh, b.pin('-'), 'VREF_MID')
    cx(sh, out_pin(b), 'VREF_MID')
    sp = sh.place('Amplifier_Operational:TLV9064', 'U502', 'TLV9064', 262, 268, unit=4,
                  fp='Package_SO:TSSOP-14_4.4x5mm_P0.65mm',
                  ref_at=(262, 260), val_at=(262, 280))
    cx(sh, sp.pin('+'), 'VREF_RX')
    cx(sh, sp.pin('-'), 'U502_SPARE')
    cx(sh, out_pin(sp), 'U502_SPARE')

    for i, (ref, x) in enumerate((('U501', 316), ('U502', 366))):
        p = sh.place('Amplifier_Operational:TLV9064', ref, 'TLV9064', x, 232, unit=5,
                     fp='Package_SO:TSSOP-14_4.4x5mm_P0.65mm',
                     ref_at=(x + 12, 227), val_at=(x + 12, 231))
        cx(sh, p.pin('V+'), '@+3V3A')
        cx(sh, p.pin('V-'), '@GND')
        C(sh, f'C{563 + i}', '100nF', x + 20, 232, '@+3V3A', '@GND')
    C(sh, 'C565', '10uF/10V', 398, 232, '@+3V3A', '@GND', C08)

    sensor_local_amplifiers(sh)

    # ------------------------------------------------------------ IMU
    sh.box(16, 218, 136, 68, 'Centrale inertielle  -  SPI2 a 10 MHz')
    u3 = sh.place('Pacabot:LSM6DSOTR', 'U503', 'LSM6DSOTR', 60, 246,
                  fp='Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y',
                  fields={'LCSC': 'C2655100'}, ref_at=(60, 224), val_at=(88, 228))
    cx(sh, u3.pin('1'),  '$IMU_MISO')
    cx(sh, u3.pin('4'),  '$IMU_INT1')
    cx(sh, u3.pin('5'),  '@+3V3')
    cx(sh, u3.pin('8'),  '@+3V3')
    cx(sh, u3.pin('12'), '$IMU_nCS')
    cx(sh, u3.pin('13'), '$IMU_SCK')
    cx(sh, u3.pin('14'), '$IMU_MOSI')
    cx_bar(sh, u3, ('2', '3'), '$GND', offset=5.08)
    cx_bar(sh, u3, ('6', '7'), '@GND', offset=5.08)
    for p in ('9', '10', '11'):
        cx(sh, u3.pin(p), 'NC')
    C(sh, 'C566', '100nF', 116, 250, '@+3V3', '@GND')
    C(sh, 'C567', '100nF', 132, 250, '@+3V3', '@GND')
    sh.note('SDX et SCX a la masse : bus auxiliaire inutilise.\n'
            'A implanter au centre de rotation, pres de l essieu.', 18, 280, 1.0)

    sh.note('Emission codee, couplage alternatif avant le gain, demodulation I/Q dans le '
            'firmware :\nle gain de traitement vient du retrecissement de bande, pas de l optique.',
            16, 212, 1.0)
    return sh


def sensor_local_amplifiers(sh):
    """Complement de la repartition physique : trois TIA/gains independants.

    Les trois boitiers identiques gardent les valeurs et fonctions des voies.
    U501D conserve la reference mediane a faible impedance. Les voies libres
    sont des suiveurs sur VREF_RX, sans charge, a l interieur des rails.
    """
    sh.box(420, 18, 154, 268, 'Implantation locale des trois chaines analogiques')
    sh.note('U501 : F ; U502 : FL ; U504 : L.\n'
            'A = TIA, B = gain, dans chaque boitier.\n'
            'R/C de contre-reaction au ras des broches 1/2 et 6/7.\n'
            'R508/C504, R528/C524 et R548/C544 au pied des ADC.\n'
            'Aucune longue liaison de photodiode entre stations.',
            426, 45, 1.0)
    for ref, unit, x, y in (('U501', 3, 455, 82), ('U502', 3, 535, 82),
                            ('U504', 3, 455, 142), ('U504', 4, 535, 142)):
        spare = sh.place('Amplifier_Operational:TLV9064', ref, 'TLV9064',
                         x, y, unit=unit,
                         fp='Package_SO:TSSOP-14_4.4x5mm_P0.65mm',
                         ref_at=(x, y - 10), val_at=(x, y + 12))
        cx(sh, spare.pin('+'), 'VREF_RX')
        cx(sh, spare.pin('-'), f'{ref}_SPARE_{unit}')
        cx(sh, out_pin(spare), f'{ref}_SPARE_{unit}')
    p = sh.place('Amplifier_Operational:TLV9064', 'U504', 'TLV9064',
                 455, 232, unit=5, fp='Package_SO:TSSOP-14_4.4x5mm_P0.65mm',
                 ref_at=(467, 227), val_at=(467, 231))
    cx(sh, p.pin('V+'), '@+3V3A')
    cx(sh, p.pin('V-'), '@GND')
    C(sh, 'C568', '100nF', 495, 232, '@+3V3A', '@GND')
    sh.note('C563 / C564 / C568 : 100 nF local, broche 4 vers masse.\n'
            'Entrees inutilisees polarisees par VREF_RX, sorties bouclees.\n'
            'Plan de masse continu ; retours TX eloignes des noeuds PD.',
            426, 270, 1.0)


# =====================================================================
#  06 - Interface homme-machine
# =====================================================================
def sheet_hmi():
    sh = Sheet(LIB, 'IHM', '06-hmi.kicad_sch', paper='A3',
               title='UsainBot - Afficheur, switch 5 directions, buzzer, depart, temoins',
               rev=REV, date=DATE, company=COMPANY,
               comments=('Chapitre 5 art. 1 : configuration sans outillage, un petit tournevis au plus',
                         'L OLED n est jamais rafraichi pendant une tentative (transfert bloquant ~30 ms)'))

    # ---------------------------------------------------------- afficheur
    sh.box(16, 24, 150, 76, 'Afficheur OLED SSD1306 0,96 pouce  -  bus I2C2, hors PCBA')
    j = sh.place('Connector_Generic:Conn_01x04', 'J601', 'OLED SSD1306 I2C', 60, 54,
                 fp='Pacabot:OLED_096_I2C',
                 ref_at=(46, 42), val_at=(46, 68))
    cx(sh, j.pin('1'), '$GND')
    cx(sh, j.pin('2'), '$+3V3')
    cx(sh, j.pin('3'), '$SCL2')
    cx(sh, j.pin('4'), '$SDA2')
    R(sh, 'R601', '4k7', 110, 60, '@+3V3', '$SDA2')
    R(sh, 'R602', '4k7', 126, 60, '@+3V3', '$SCL2')
    sh.note('Tirage du bus I2C2, partage avec le chargeur.\nBus lent, jamais sollicite en course.', 20, 92, 1.0)

    # ------------------------------------------------- switch 5 directions
    sh.box(180, 24, 230, 110, 'Switch 5 directions  -  navigation a deux dimensions, une seule piece')
    sw = sh.place('Pacabot:SW_Nav_5Way', 'SW601', 'SKRHABE010', 240, 70,
                  fp='Pacabot:SKRHABE010', fields={'LCSC': 'C144855'},
                  ref_at=(240, 52), val_at=(240, 88))
    dirs = (('1', 'SW_UP'), ('2', 'SW_DOWN'), ('3', 'SW_LEFT'),
            ('4', 'SW_RIGHT'), ('5', 'SW_PUSH'))
    for num, net in dirs:
        cx(sh, sw.pin(num), '$' + net)
    cx(sh, sw.pin('6'), '@GND')
    for i, (_, net) in enumerate(dirs):
        R(sh, f'R{603 + i}', '10k', 300 + i * 20, 52, '@+3V3', '$' + net)
        C(sh, f'C{601 + i}', '100nF', 300 + i * 20, 96, '$' + net, '@GND')
    sh.note('Alps SKRHABE010, joystick 4 directions + appui central, 7,35 x 7,5 mm.\n'
            'Contacts A-D vers UP/RIGHT/DOWN/LEFT : l affectation reelle des\n'
            'directions se recale au firmware.', 184, 128, 1.0)

    # ---------------------------------------------------------- depart
    sh.box(16, 144, 194, 76, 'Depart  -  moyen conforme au chapitre 2 du reglement')
    swp = sh.place('Switch:SW_Push', 'SW602', 'START', 60, 168,
                   fp='Button_Switch_SMD:SW_SPST_B3U-1000P',
                   ref_at=(60, 158), val_at=(60, 162))
    cx(sh, swp.pin('1'), '$START_BTN')
    cx(sh, swp.pin('2'), '@GND')
    R(sh, 'R608', '10k', 130, 168, '@+3V3', '$START_BTN')
    C(sh, 'C606', '100nF', 146, 168, '$START_BTN', '@GND')
    sh.note('Le bouton suffit au reglement, le geste devant le telemetre\n'
            'n en est qu un complement (machine a etats du firmware).', 20, 220, 1.0)

    # ---------------------------------------------------------- buzzer
    sh.box(224, 144, 186, 76, 'Buzzer passif  -  TIM17, le seul retour lisible robot au sol')
    bz = sh.place('Device:Buzzer', 'BZ601', 'buzzer magnetique 9 x 5,5 mm', 280, 168,
                  fp='Buzzer_Beeper:MagneticBuzzer_ProSignal_ABI-009-RC',
                  ref_at=(292, 160), val_at=(292, 164))
    cx(sh, bz.pin('1'), '@+3V3')
    cx(sh, bz.pin('2'), 'BUZZ_D')
    horiz(sh, 'Device:D_Schottky', 'D601', 'BAT54', 330, 190, '@+3V3', 'BUZZ_D',
          'Diode_SMD:D_SOD-323')
    horiz(sh, 'Device:C', 'C607', '100nF', 244, 178, '$BUZZER', 'BZAC', C06)
    horiz(sh, 'Device:D_Schottky', 'D610', 'BAT54', 352, 214, 'BZAC', '@GND',
          'Diode_SMD:D_SOD-323')
    nmos_switch(sh, 'Q601', 280, 190, 'BZAC', 'BUZZ_D', rref=('R609', 'R610'))
    sh.note('Roue libre obligatoire (bobine) ; grille couplee en alternatif :\n'
            'un GPIO fige ne peut pas laisser 200 mA en continu dans le buzzer.',
            300, 208, 1.0)

    sh.note('Plus de temoins d etat generiques : les trois LED verte / rouge /\n'
            'jaune et leurs trois GPIO ont ete rendus le 4 septembre. Ce qu on\n'
            'regarde pendant un essai, c est la barrette - chaque capteur de\n'
            'ligne a maintenant sa LED (feuille 04). Le temoin " BLE alimente "\n'
            'visible du jury reste cable sur le rail +3V3_BLE lui-meme\n'
            '(feuille 07) : il ne peut pas mentir sur l etat reel du module.',
            18, 250, 1.0)

    # ------------------------------------------- eclairage de suivi camera
    sh.box(16, 104, 160, 38,
           'Suivi camera  -  1 bleue au nez, 2 rouges aux coins arriere')
    for i, (ref, rref_, col, rv) in enumerate((
            ('D606', 'R615', 'bleue - nez', '220R'),
            ('D608', 'R617', 'rouge - coin arriere gauche', '300R'),
            ('D609', 'R618', 'rouge - coin arriere droit', '300R'))):
        x = 38 + i * 30
        R(sh, rref_, rv, x, 112, '@VBAT', f'{ref}_A')
        horiz(sh, 'Device:LED', ref, col, x + 2, 132, 'TRACK_SW', f'{ref}_A',
              LED06)
    sh.note('Deux des trois bleues du nez ont ete rendues le 4 septembre : il en\n'
            'reste une sur l axe. Avec les deux rouges des coins arriere, la\n'
            'camera a toujours un triangle - position ET cap - et le nez, qui\n'
            'est la partie la plus etroite et la plus chargee de la carte, y\n'
            'gagne deux LED et deux resistances de place.', 18, 156, 1.0)
    nmos_switch(sh, 'Q602', 152, 112, '$TRACK_EN', 'TRACK_SW',
                rref=('R619', 'R620'))
    return sh


# =====================================================================
#  07 - Traces, liaison sans fil, turbine
# =====================================================================
def sheet_comms():
    sh = Sheet(LIB, 'Traces et turbine', '07-comms.kicad_sch', paper='A3',
               title='UsainBot - Flash de traces, module BLE, embase ESC de turbine',
               rev=REV, date=DATE, company=COMPANY,
               comments=('Chapitre 2 : moyens de communication inhibes au moment du depart',
                         'Broche BEC de l embase ESC laissee non connectee'))

    # ---------------------------------------------------------- flash SPI
    sh.box(16, 24, 170, 96, 'Memoire de traces  -  W25Q128 sur SPI3, 50 MHz')
    u = sh.place('Memory_Flash:W25Q128JVS', 'U701', 'W25Q128JVSIQ', 90, 66,
                 fp='Package_SO:SOIC-8_5.3x5.3mm_P1.27mm', ref_at=(90, 46), val_at=(90, 90))
    cx(sh, u.pin('1'), '$FLASH_nCS')
    cx(sh, u.pin('2'), '$FLASH_MISO')
    cx(sh, u.pin('3'), 'FLASH_nWP')
    cx(sh, u.pin('4'), '@GND')
    cx(sh, u.pin('5'), '$FLASH_MOSI')
    cx(sh, u.pin('6'), '$FLASH_SCK')
    cx(sh, u.pin('7'), 'FLASH_nHOLD')
    cx(sh, u.pin('8'), '@+3V3')
    R(sh, 'R701', '10k', 150, 42, '@+3V3', 'FLASH_nWP')
    R(sh, 'R702', '10k', 166, 42, '@+3V3', 'FLASH_nHOLD')
    C(sh, 'C701', '100nF', 150, 90, '@+3V3', '@GND')
    sh.note('Log 1 kHz de 20 signaux sur un tour complet, puis vidage par USB.', 20, 114, 1.0)

    # ---------------------------------------------------------- module BLE
    sh.box(196, 24, 214, 130, 'Module BLE detachable  -  alimentation coupee par interrupteur de charge')
    q1 = sh.place('Transistor_FET:Q_PMOS_GSD', 'Q701', 'SI2301CDS', 300, 54, fp=SOT23,
                  ref_at=(310, 46), val_at=(310, 50))
    cx(sh, q1.pin('S'), '@+3V3')
    cx(sh, q1.pin('D'), '@+3V3_BLE')
    cx(sh, q1.pin('G'), 'BLE_PG')
    R(sh, 'R703', '100k', 268, 46, '@+3V3', 'BLE_PG')
    nmos_switch(sh, 'Q702', 268, 84, '$BLE_PWR_EN', 'BLE_PG', rref=('R704', 'R705'))
    C(sh, 'C702', '10uF/10V', 336, 62, '$+3V3_BLE', '@GND', C08)
    C(sh, 'C703', '100nF', 348, 62, '@+3V3_BLE', '@GND')
    R(sh, 'R706', '1k', 366, 62, '@+3V3_BLE', 'BLE_LED_A')
    horiz(sh, 'Device:LED', 'D701', 'bleue', 378, 88, '@GND', 'BLE_LED_A', LED06)
    flag(sh, '+3V3_BLE', 336, 96)
    j1 = sh.place('Connector_Generic:Conn_01x04', 'J701', 'Module OTA (ESP32-C3)',
                  240, 122, fp='Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',
                  ref_at=(224, 106), val_at=(224, 138))
    cx(sh, j1.pin('1'), '$GND')
    cx(sh, j1.pin('2'), '$+3V3_BLE')
    cx(sh, j1.pin('3'), '$BLE_TX')
    cx(sh, j1.pin('4'), '$BLE_RX')
    sh.note('PA8 haut = module alimente. Grille rappelee au rail par R703 :\n'
            'MCU eteint ou GPIO en haute impedance, le module reste hors tension.\n'
            'Module conseille : ESP32-C3 SuperMini - OTA par WiFi natif (rapide),\n'
            'pont UART 921600 Bd vers le STM32. Un HM-11 BLE 4.0 plafonne a\n'
            '2-3 ko/s : 2 a 4 min pour 256 ko de firmware. Broche 3 = RX du\n'
            'module, broche 4 = TX : a recroiser selon la serigraphie.',
            200, 150, 1.0)

    # ---------------------------------------------------------- turbine
    sh.box(16, 168, 394, 76, 'Turbine d appui  -  l ESC est autonome, la carte ne lui envoie qu une consigne')
    j2 = sh.place('Connector_Generic:Conn_01x01', 'J702', 'Signal ESC (coudee)',
                  90, 200,
                  fp='Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Horizontal',
                  ref_at=(76, 192), val_at=(76, 208))
    cx(sh, j2.pin('1'), 'ESC_SIG')
    Rh(sh, 'R707', '100R', 150, 202, '$ESC_PWM', 'ESC_SIG')
    sh.note('Une seule broche, et COUDEE : le variateur est debout juste a cote,\n'
            'son fil de commande arrive a plat le long de la carte. Le cordon\n'
            'trois fils est coupe - le fil central (BEC) sort 5 ou 6 V sur la\n'
            'plupart des variateurs et emporterait le rail 3,3 V, et le fil de\n'
            'masse est inutile puisque le meme cuivre revient par le fil noir de\n'
            'puissance soude en J103, a quelques millimetres de la.', 76, 232, 1.0)
    sh.note('Calibre : la turbine tire 11 A a 8,4 V, mais elle est ici sur VBAT\n'
            '(5,0 a 7,3 V) et le courant d une helice suit le carre de la tension :\n'
            '11 x (6,4/8,4)^2 = 6,4 A sur le plateau LiFePO4. Les 10 A continus du\n'
            'MultiStar tiennent donc, avec 15 A de crete a la mise en rotation.\n'
            'A verifier a la pince amperemetrique au premier essai en charge.',
            176, 240, 1.0)
    j3 = sh.place('Connector_Generic:Conn_01x02', 'J103', 'MultiStar 10A (debout)',
                  300, 200, fp='Pacabot:ESC_Multistar_10A',
                  ref_at=(286, 190), val_at=(286, 212))
    cx(sh, j3.pin('1'), '@VBAT')
    cx(sh, j3.pin('2'), '@GND')
    C(sh, 'C704', '220uF/10V', 344, 202, '@VBAT', '@GND', CPOL)  # VBAT <= 7,3 V
    C(sh, 'C705', '100nF', 358, 202, '@VBAT', '@GND')
    sh.note('Turnigy MultiStar 10A BLHeli-S (Opto) : 22 x 12 mm, 5,1 g, 10 A\n'
            'continu / 15 A crete. Il est DEBOUT sur sa tranche cote entree de\n'
            'puissance, ses deux fils soudes dans J103 et un collier au corps :\n'
            '12 x 5 mm d emprise pour 22 mm de haut. Aucun connecteur ne\n'
            's intercale sur le courant de la turbine.', 286, 240, 1.0)
    sh.note('Puissance prise sur VBAT en amont des ponts moteurs, avec son propre decouplage.\n'
            'Rampe la consigne : une montee en regime brutale fait chuter VBAT et peut faire\n'
            'redemarrer le MCU en pleine ligne droite. L armement de l ESC fait partie de la\n'
            'sequence de pre-depart, pas du demarrage du firmware.\n\n'
            'F101 12 A et les deux AO4407A en parallele de la feuille 01 laissent\n'
            'la marge.',
            18, 254, 1.0)
    return sh


# =====================================================================
#  Feuille racine
# =====================================================================
def add_sheet(root, child, x, y, w, h, page):
    node = ['sheet', ['at', fmt(x), fmt(y)], ['size', fmt(w), fmt(h)],
            ['exclude_from_sim', 'no'], ['in_bom', 'yes'], ['on_board', 'yes'],
            ['dnp', 'no'], ['fields_autoplaced', 'yes'],
            ['stroke', ['width', '0.1524'], ['type', 'solid']],
            ['fill', ['color', '0', '0', '0', '0.0000']],
            ['uuid', q(child.uuid)],
            ['property', q('Sheetname'), q(child.name),
             ['at', fmt(x), fmt(y - 0.7112), '0'],
             ['effects', ['font', ['size', '1.27', '1.27']], ['justify', 'left', 'bottom']]],
            ['property', q('Sheetfile'), q(child.filename),
             ['at', fmt(x), fmt(y + h + 1.4224), '0'],
             ['effects', ['font', ['size', '1.27', '1.27']], ['justify', 'left', 'top']]],
            ['instances', ['project', q('UsainBot'),
                           ['path', q('/' + ROOT_UUID), ['page', q(str(page))]]]]]
    root.items.append(node)


def sheet_root(children):
    sh = Sheet(LIB, 'UsainBot', ROOT_FILE, paper='A3',
               title='UsainBot - robot suiveur de ligne, epreuve Formule 1 TNRS',
               rev=REV, date=DATE, company=COMPANY,
               comments=('STM32H723VGT6 - 12 voies de ligne - 2 ponts DRV8874 - pack 2S LiFePO4',
                         'Reglement Formule 1 v2.11 (2025) - carte 4 couches, assemblage JLCPCB'))
    sh.note('UsainBot  -  architecture materielle', 20, 30, 4.0, bold=True)
    sh.note('Les feuilles communiquent par etiquettes globales : chaque bloc se lit seul,\n'
            'et le renommage d un signal se propage sans retoucher les entrees de feuille.',
            20, 40, 1.4)

    lay = [(20, 56, 170, 42, 2), (20, 108, 170, 42, 3),
           (20, 160, 170, 42, 4), (20, 212, 170, 42, 5),
           (210, 56, 170, 42, 6), (210, 108, 170, 42, 7),
           (210, 160, 170, 42, 8), (210, 212, 170, 42, 9)]
    for child, (x, y, w, h, page) in zip(children, lay):
        add_sheet(sh, child, x, y, w, h, page)

    blurb = {
        '01-power.kicad_sch': 'USB-C, chargeur elevateur BQ25887, pack 2S,\ncoupure generale, anti-inversion, buck 3,3 V, rail 3V3A',
        '02-mcu.kicad_sch': 'STM32H723VGT6 en LQFP100, decouplage, quartz 25 MHz,\nreset, BOOT0, empreinte Tag-Connect SWD + SWO',
        '03-motors.kicad_sch': 'Deux DRV8874 en mode PWM, limitation de courant,\nconnecteurs moteur + encodeur, filtrage de quadrature',
        '04-line-array.kicad_sch': 'Douze ITR8307 au pas de 10 mm, deux bancs d emetteurs\npulses, charges d emetteur sur le rail analogique',
        '05-sensors.kicad_sch': 'Deux VL53L1X sur languette sechable, voie analogique\nrapide a gauche, LSM6DSO sur SPI2',
        '06-hmi.kicad_sch': 'OLED I2C2, switch 5 directions, buzzer sur TIM17,\nbouton et jack de depart, temoins',
        '07-comms.kicad_sch': 'Flash W25Q128 sur SPI3, module BLE a alimentation\ncommutee, embase ESC et puissance de turbine',
        '08-line-leds.kicad_sch': 'Douze temoins de presence de ligne sur PCA9685,\nun par capteur de la moustache, pilotes en PWM par I2C2',
    }
    for child, (x, y, w, h, _) in zip(children, lay):
        sh.note(blurb[child.filename], x + 3, y + 14, 1.2)

    sh.note('Points ouverts :\n'
            '-  la turbine est sur VBAT : 6,4 A au plateau LiFePO4 contre 11 A a 8,4 V, d ou le\n'
            '   MultiStar 10 A. A verifier a la pince au premier essai en charge ;\n'
            '-  OPV302 et BPV10NF hors bibliotheque JLCPCB : pose manuelle, les deux sont couches\n'
            '   dans le support imprime de la station ;\n'
            '-  les seize entrees ADC du LQFP100 sont toutes prises (12 voies de ligne, 3 voies de\n'
            '   telemetrie, 1 sortie de multiplexeur) : U104 ne peut pas etre supprime sans passer\n'
            '   au LQFP144 ;\n'
            '-  valeurs a recaler : R116 (frequence du buck), R107 (courant d equilibrage),\n'
            '   charge du quartz, R421-R432 (gain des voies de ligne).',
            20, 288, 1.3)
    return sh


def main():
    kids = [sheet_power_b(sheet_power()), sheet_mcu(), sheet_motors(),
            sheet_line(), sheet_sensors(), sheet_hmi(), sheet_comms(),
            sheet_line_leds()]
    root = sheet_root(kids)
    si = ['sheet_instances', ['path', q('/'), ['page', q('1')]]]
    for i, k in enumerate(kids, 2):
        si.append(['path', q('/' + k.uuid), ['page', q(str(i))]])
    os.makedirs(DEST, exist_ok=True)
    open(os.path.join(DEST, root.filename), 'w', encoding='utf-8').write(root.render([si]))
    for k in kids:
        open(os.path.join(DEST, k.filename), 'w', encoding='utf-8').write(k.render())
    if REPORT:
        agg = {k: set() for k in ('glabel', 'label', 'text', 'textb', 'field')}
        for sh in kids + [root]:
            for k, v in sh.strings.items():
                agg[k] |= v
        json.dump({'sheets': [sh.report() for sh in kids + [root]],
                   'strings': {k: sorted(v) for k, v in agg.items()}},
                  open(REPORT, 'w', encoding='utf-8'), ensure_ascii=False)
    bad = [e for k in kids + [root] for e in k.check()]
    if bad:
        print('COLLISIONS ELECTRIQUES :')
        for e in bad:
            print('   ', e)
    over = [e for k in kids + [root] for e in k.check_overlaps()]
    if over:
        print(f'RECOUVREMENTS : {len(over)}')
        for e in over:
            print('   ', e)
    n = sum(len([p for p in k.parts if not p.ref.startswith('#')]) for k in kids)
    print(f'{len(kids) + 1} feuilles, {n} composants (hors symboles d alimentation)')
    for k in kids:
        print(f'  {k.filename:26s} {len([p for p in k.parts if not p.ref.startswith("#")]):3d} composants')


main()
