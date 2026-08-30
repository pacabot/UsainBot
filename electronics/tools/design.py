# -*- coding: utf-8 -*-
"""Genere le schema hierarchique KiCad du robot UsainBot."""
import os, sys
import kigen
from kigen import SymLib, Sheet, q, fmt, uid, ROOT_UUID, ROOT_FILE

HERE = os.path.dirname(os.path.abspath(__file__))
ELEC = os.path.abspath(os.path.join(HERE, '..'))          # .../electronics
DEST = sys.argv[1] if len(sys.argv) > 1 else ELEC
PRJ  = os.path.join(ELEC, 'kicad-lib')
LIB  = SymLib([PRJ])

DATE, REV, COMPANY = '2026-08-30', 'A', 'Pacabot'

# ------------------------------------------------------------------ empreintes
R06  = 'Resistor_SMD:R_0603_1608Metric'
R08  = 'Resistor_SMD:R_0805_2012Metric'
R12  = 'Resistor_SMD:R_1206_3216Metric'
C06  = 'Capacitor_SMD:C_0603_1608Metric'
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
        end = pin.out(stub)
        if stub:
            sh.wire((pin.x, pin.y), end)
        # pas de coude : deux troncons paralleles ne se croisent jamais.
        # La broche du symbole d alimentation est a son origine, donc le tourner
        # ne deplace rien : on l oriente seulement pour que le dessin tombe juste.
        d = (round(pin.dx), round(pin.dy))
        if rail in GNDISH:
            rot = {(0, 1): 0, (0, -1): 180, (-1, 0): 90, (1, 0): 270}[d]
        else:
            rot = {(0, -1): 0, (0, 1): 180, (-1, 0): 270, (1, 0): 90}[d]
        sh.power_at(rail, end, PWRLIB[rail], rot=rot)
    elif spec.startswith('$'):
        sh.gnet(pin, spec[1:], stub)
    else:
        sh.net(pin, spec, stub)

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
    end = sh.bar(pins, net, offset)
    d = (round(pins[0].dx), round(pins[0].dy))
    cx(sh, kigen.Pin(end[0], end[1], d[0], d[1], '', '', 'passive'), spec, stub)


def flag_net(sh, net, x, y, glob=True):
    """PWR_FLAG raccorde a un net nomme (le net n a pas de symbole d alim)."""
    sh.power_at('PWR_FLAG', (x, y), 'power')
    sh.wire((x, y), (x, y + 5.08), net)
    (sh.glabel_at if glob else sh.label_at)(net, (x, y + 5.08), (0, 1))

def flag(sh, rail, x, y):
    """Rail + PWR_FLAG cote a cote, pour satisfaire l'ERC."""
    sh.power_at(rail, (x, y), PWRLIB[rail], rot=180)
    sh.wire((x, y), (x + 5.08, y), rail)
    sh.power_at('PWR_FLAG', (x + 5.08, y), 'power', rot=180)

# --------------------------------------------------------------- deux-pattes
def vert(sh, lib_id, ref, val, x, y, top, bot, fp, fields=None, dnp=False):
    """Composant vertical : broche 1 en haut, broche 2 en bas."""
    p = sh.place(lib_id, ref, val, x, y, fp=fp, fields=fields, dnp=dnp,
                 ref_at=(x + 3.81, y - 1.27), val_at=(x + 3.81, y + 1.27))
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

def C(sh, ref, val, x, y, top, bot, fp=C06, fields=None):
    return vert(sh, 'Device:C', ref, val, x, y, top, bot, fp, fields)

def R(sh, ref, val, x, y, top, bot, fp=R06, fields=None, dnp=False):
    return vert(sh, 'Device:R', ref, val, x, y, top, bot, fp, fields, dnp)

def Rh(sh, ref, val, x, y, left, right, fp=R06, fields=None):
    return horiz(sh, 'Device:R', ref, val, x, y, left, right, fp, fields)

def tp(sh, ref, net, x, y, glob=True):
    p = sh.place('Connector:TestPoint', ref, net, x, y, fp=TP,
                 ref_at=(x + 2.54, y - 3.81), val_at=(x + 2.54, y - 1.27))
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
    sh.box(100, 78, 112, 168, 'C. Chargeur elevateur 2S  -  BQ25887')
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
    cx(sh, u2.pin('24'), '@GND')                           # PSEL bas = adaptateur
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

    # thermistance du pack sur TS
    R(sh, 'R104', '5k23', 106, 214, 'REGN', 'TS')
    R(sh, 'R105', '30k1', 122, 214, 'TS', '@GND')
    j4 = sh.place('Connector_Generic:Conn_01x02', 'J104', 'NTC pack 10k B3435',
                  116, 232, fp='Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical',
                  ref_at=(110, 224), val_at=(110, 242))
    cx(sh, j4.pin('1'), 'TS'); cx(sh, j4.pin('2'), '@GND')

    # equilibrage / point milieu
    Rh(sh, 'R106', '300R', 172, 168, 'PACK_MID', 'MID_R')
    Rh(sh, 'R107', '10R / 1 W', 190, 168, 'PACK_MID', 'CBSET_R', R12)
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
    sh.box(220, 24, 190, 104, 'D. Pack 2S, coupure generale et protection contre l inversion')
    j2 = sh.place('Connector_Generic:Conn_01x02', 'J102', 'Pack 2S LiFePO4 (XT30)',
                  236, 46, fp='Connector_AMASS:AMASS_XT30U-M_1x02_P5.0mm_Vertical',
                  ref_at=(226, 38), val_at=(226, 58))
    cx(sh, j2.pin('1'), '@VPACK'); cx(sh, j2.pin('2'), '@GND')
    j3 = sh.place('Connector_Generic:Conn_01x03', 'J103', 'Equilibrage JST-XH 2S',
                  236, 82, fp='Connector_JST:JST_XH_B3B-XH-AM_1x03_P2.50mm_Vertical',
                  ref_at=(226, 72), val_at=(226, 96))
    cx(sh, j3.pin('1'), '@GND')        # B-
    cx(sh, j3.pin('2'), 'PACK_MID')    # point milieu
    cx(sh, j3.pin('3'), '@VPACK')      # B+
    sh.note('Le chargeur est en amont de l interrupteur :\nle robot se recharge eteint.', 226, 106, 1.0)

    vert(sh, 'Device:Fuse', 'F101', '10 A', 288, 46, '@VPACK', 'VBAT_SW_IN', R12)
    j5 = sh.place('Connector_Generic:Conn_01x02', 'J105', 'ON/OFF deporte 10 A',
                  288, 78, fp='Connector_JST:JST_VH_B2P-VH_1x02_P3.96mm_Vertical',
                  ref_at=(278, 70), val_at=(278, 92))
    cx(sh, j5.pin('1'), 'VBAT_SW_IN'); cx(sh, j5.pin('2'), 'VBAT_SW_OUT')

    q2 = sh.place('Pacabot:AO4407A', 'Q102', 'AO4407A', 362, 62,
                  fp='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
                  ref_at=(334, 58), val_at=(334, 62))
    cx_bar(sh, q2, ('5', '6', '7', '8'), 'VBAT_SW_OUT')   # drain cote batterie
    cx_bar(sh, q2, ('1', '2', '3'), '@VBAT')              # source cote charge
    cx(sh, q2.pin('4'), 'QREV_G')
    R(sh, 'R114', '100k', 340, 80, 'QREV_G', '@GND')
    sh.note('Canal P en serie cote haut : drain vers la batterie, source vers la charge.\n'
            'Polarite correcte -> Vgs = -Vbat, le canal conduit. Polarite inversee -> bloque.\n'
            'Une Schottky aurait coute 1,2 W a 3 A.', 300, 100, 1.0)
    horiz(sh, 'Device:D_TVS', 'D102', 'SMBJ9.0A', 300, 118, '@VBAT', '@GND', 'Diode_SMD:D_SMB')
    C(sh, 'C109', '100uF/16V', 330, 118, '@VBAT', '@GND', CPOL)
    C(sh, 'C110', '100nF', 344, 118, '@VBAT', '@GND', C06)
    sh.note('Ecretage du freinage regeneratif : a 3 m/s, un arret a fond\n'
            'renvoie toute l energie cinetique dans un pack deja plein.', 236, 126, 1.0)

    # ------------------------------------------------------------- buck 3,3 V
    sh.box(220, 140, 190, 92, 'E. Convertisseur 3,3 V / 2 A  -  TPS62933')
    u3 = sh.place('Regulator_Switching:TPS62933', 'U103', 'TPS62933DRLR', 290, 176,
                  fp='Package_TO_SOT_SMD:SOT-583-8', fields={'LCSC': 'C3200405'},
                  ref_at=(290, 158), val_at=(290, 204))
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
    C(sh, 'C115', '10nF', 272, 210, 'SS_BUCK', '@GND', C06)
    R(sh, 'R116', '42k2', 282, 210, 'RT_BUCK', '@GND')
    horiz(sh, 'Device:L', 'L102', '4u7H / 3 A', 330, 164, 'SW_BUCK', '@+3V3',
          'Inductor_SMD:L_Taiyo-Yuden_NR-40xx')
    C(sh, 'C116', '22uF/10V', 348, 178, '@+3V3', '@GND', C08)
    C(sh, 'C117', '22uF/10V', 358, 178, '@+3V3', '@GND', C08)
    C(sh, 'C118', '100nF', 368, 178, '@+3V3', '@GND', C06)
    R(sh, 'R117', '100k', 330, 196, '@+3V3', 'FB_BUCK')
    R(sh, 'R118', '31k6', 330, 214, 'FB_BUCK', '@GND')
    sh.note('VOUT = 0,8 V x (1 + R117/R118) = 3,33 V.\n'
            'R116 fixe la frequence (~500 kHz) : a recaler sur la courbe fSW(RT).',
            234, 228, 1.0)

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
    R(sh, 'R119', '68k', 32, 196, '@VBAT', '$VBAT_SENSE')
    R(sh, 'R120', '33k', 32, 214, '$VBAT_SENSE', '@GND')
    C(sh, 'C121', '100nF', 54, 214, '$VBAT_SENSE', '@GND', C06)
    sh.note('7,3 V -> 2,38 V sur ADC3 (PC0)', 18, 230, 1.0)
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


MCU_PINS = {
    # --- cote gauche -------------------------------------------------------
    '14': 'NRST',            '94': 'BOOT0',          '20': '@+3V3A',
    '12': 'OSC_IN',          '13': 'OSC_OUT',
    '97': '$TOF_F_INT',      '98': '$TOF_FL_INT',
    '1':  '$CHG_CD_EN',      '2':  '$CHG_INT',
    '3':  'TP_PE4',          '4':  'TP_PE5',         '5':  '$IMU_INT1',
    '37': '$IR_BANK_A',      '38': '$IR_BANK_B',
    '39': '$MOT_L_IN1',      '40': '$SW_UP',
    '41': '$MOT_L_IN2',      '42': '$SW_DOWN',
    '43': '$MOT_R_IN1',      '44': '$MOT_R_IN2',     '45': '$SW_LEFT',
    '81': '$MOT_L_nSLEEP',   '82': '$MOT_R_nSLEEP',  '83': '$FLASH_nCS',
    '84': '$MOT_L_nFAULT',   '85': '$MOT_R_nFAULT',
    '86': '$TOF_F_XSHUT',    '87': '$TOF_FL_XSHUT',
    '88': 'NC', '55': 'NC', '56': 'NC', '58': 'NC', '59': 'NC',
    '57': '$SW_RIGHT',       '60': '$SW_PUSH',       '61': '$START_BTN',
    '62': '$LED_STATUS',
    '48': 'VCAP1',           '73': 'VCAP2',
    # --- cote droit --------------------------------------------------------
    '22': '$LINE_00', '23': '$LINE_01', '24': '$LINE_02', '25': '$LINE_03',
    '28': '$LINE_04', '29': '$LINE_05', '30': '$LINE_06', '31': '$LINE_07',
    '34': '$LINE_08', '35': '$LINE_09', '32': '$LINE_10', '33': '$LINE_11',
    '67': '$BLE_PWR_EN', '68': '$BLE_TX', '69': '$BLE_RX',
    '70': '$USB_DM', '71': '$USB_DP',
    '72': 'SWDIO', '76': 'SWCLK', '77': 'TP_PA15',
    '36': '$IR_LASER_EN', '89': 'SWO',
    '90': '$ENC_L_A', '91': '$ENC_L_B', '63': '$ENC_R_A', '64': '$ENC_R_B',
    '92': '$SCL1', '93': '$SDA1', '46': '$SCL2', '47': '$SDA2',
    '95': '$ESC_PWM', '96': '$BUZZER',
    '51': '$IMU_nCS', '52': '$IMU_SCK', '53': '$IMU_MISO', '54': '$IMU_MOSI',
    '15': '$VBAT_SENSE', '16': '$IPROPI_L', '17': '$IPROPI_R', '18': '$TOF_ANA',
    '65': '$LED_ERROR', '66': '$LED_USER',
    '78': '$FLASH_SCK', '79': '$FLASH_MISO', '80': '$FLASH_MOSI',
    '7': 'TP_PC13', '8': 'TP_PC14', '9': 'TP_PC15',
}


# =====================================================================
#  02 - Microcontroleur, horloge, debogage
# =====================================================================
def sheet_mcu():
    sh = Sheet(LIB, 'MCU', '02-mcu.kicad_sch', paper='A3',
               title='UsainBot - STM32H723VGT6, horloge et debogage',
               rev=REV, date=DATE, company=COMPANY,
               comments=('Mode LDO seul (AN5312) : le LQFP100 n expose pas les broches SMPS',
                         'PB3 est reserve au SWO, d ou l abandon de TIM2'))
    u = sh.place('MCU_ST_STM32H7:STM32H723VGTx', 'U201', 'STM32H723VGT6', 200, 150,
                 fp='Package_QFP:LQFP-100_14x14mm_P0.5mm', fields={'LCSC': 'C730142'},
                 ref_at=(200, 72), val_at=(200, 228),
                 datasheet='https://www.st.com/resource/en/datasheet/stm32h723vg.pdf')

    for num, spec in MCU_PINS.items():
        cx(sh, u.pin(num), spec, stub=5.08)

    # alimentations
    rail_bar(sh, [u.pin(n) for n in ('11', '27', '50', '75', '100')], '+3V3', 10.16)
    cx(sh, u.pin('6'),  '@+3V3')      # VBAT interne
    cx(sh, u.pin('21'), '@+3V3A')     # VDDA
    cx(sh, u.pin('10'), '@GND')       # les cinq VSS partagent le meme point
    cx(sh, u.pin('19'), '@GND')       # VSSA

    # decouplage
    sh.box(120, 20, 200, 32, 'Decouplage  -  un 100 nF par broche VDD, au plus pres du boitier')
    for i, ref in enumerate(('C201', 'C202', 'C203', 'C204', 'C205')):
        C(sh, ref, '100nF', 128 + i * 12, 36, '@+3V3', '@GND')
    C(sh, 'C206', '4u7F/10V', 188, 36, '@+3V3', '@GND', C08)
    C(sh, 'C207', '100nF', 200, 36, '@+3V3', '@GND')
    C(sh, 'C208', '100nF', 224, 36, '@+3V3A', '@GND')
    C(sh, 'C209', '1uF', 236, 36, '@+3V3A', '@GND')
    C(sh, 'C210', '100nF', 260, 36, '@+3V3A', '@GND')
    C(sh, 'C211', '1uF', 272, 36, '@+3V3A', '@GND')
    sh.note('C208/C209 : VDDA        C210/C211 : VREF+', 224, 50, 1.0)
    C(sh, 'C212', '2u2F/10V', 128, 200, 'VCAP1', '@GND', C08)
    C(sh, 'C213', '2u2F/10V', 142, 200, 'VCAP2', '@GND', C08)
    sh.note('VCAP : 2,2 uF ceramique, ESR < 2 ohm, tres pres du boitier.', 118, 212, 1.0)

    # reset et boot
    sh.box(20, 62, 96, 42, 'Reset et selection du mode de demarrage')
    R(sh, 'R201', '10k', 32, 78, '@+3V3', 'NRST')
    C(sh, 'C214', '100nF', 46, 78, 'NRST', '@GND')
    R(sh, 'R202', '10k', 68, 78, 'BOOT0', '@GND')
    R(sh, 'R203', '10k', 82, 78, '@+3V3', 'BOOT0', R06, dnp=True)
    tp(sh, 'TP201', 'BOOT0', 100, 74, glob=False)
    sh.note('R203 non montee : la poser force le bootloader DFU.', 24, 100, 1.0)

    # horloge
    sh.box(20, 112, 96, 54, 'Horloge HSE 25 MHz  -  obligatoire pour l USB')
    y1 = sh.place('Device:Crystal_GND24_Small', 'Y201', '25 MHz / 10 ppm', 60, 130,
                  fp='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',
                  ref_at=(60, 122), val_at=(60, 140))
    cx(sh, y1.pin('1'), 'OSC_IN')
    cx(sh, y1.pin('3'), 'XTAL_OUT')
    cx_bar(sh, y1, ('2', '4'), '@GND', offset=5.08)
    C(sh, 'C215', '10pF', 32, 152, 'OSC_IN', '@GND')
    C(sh, 'C216', '10pF', 88, 152, 'XTAL_OUT', '@GND')
    Rh(sh, 'R204', '220R', 100, 130, 'XTAL_OUT', 'OSC_OUT')
    sh.note('Charge a recaler sur le CL du quartz retenu :\nC = 2 x (CL - Cstray).', 24, 168, 1.0)

    # debogage
    sh.box(20, 176, 96, 62, 'Debogage SWD + SWO  -  Tag-Connect TC2050-IDC-NL')
    j = sh.place('Connector:TC2050', 'J201', 'TC2050-IDC-NL', 62, 206,
                 fp='Connector:Tag-Connect_TC2050-IDC-NL_2x05_P1.27mm_Vertical',
                 ref_at=(62, 186), val_at=(62, 228))
    for num, spec in [('1', '@+3V3'), ('2', 'SWDIO'), ('3', '@GND'), ('4', 'SWCLK'),
                      ('5', '@GND'), ('6', 'SWO'), ('7', 'NC'), ('8', 'NC'),
                      ('9', '@GND'), ('10', 'NRST')]:
        cx(sh, j.pin(num), spec)
    sh.note('Empreinte seule, sans connecteur soude :\nla sonde se pose sur les pastilles.', 24, 234, 1.0)

    # pastilles de test sur les reserves
    sh.box(330, 20, 80, 88, 'Reserves sorties sur pastilles')
    for i, n in enumerate(('TP_PE4', 'TP_PE5', 'TP_PA15', 'TP_PC13', 'TP_PC14', 'TP_PC15')):
        tp(sh, f'TP{202 + i}', n, 344, 34 + i * 12, glob=False)
    sh.note('PD7-PD9 et PD11-PD12 restent libres,\nmarques non connectes au schema.', 334, 104, 1.0)
    sh.note('Bilan : 74 broches affectees sur 82 disponibles.', 330, 118, 1.2)
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
        C(sh, f'C{refn + 4}', '100uF/16V', 214, y - 30, '@VBAT', '@GND', CPOL)
        C(sh, f'C{refn + 5}', '100nF', 228, y - 30, f'VCP_{tag}', '@VBAT')
        horiz(sh, 'Device:C', f'C{refn + 6}', '22nF', 200, y - 12, f'CPH_{tag}', f'CPL_{tag}', C06)
        # connecteur moteur + encodeur
        j = sh.place('Connector_Generic:Conn_01x06', f'J{refn + 1}',
                     f'Moteur {side} + encodeur', 330, y,
                     fp='Connector_JST:JST_PH_B6B-PH-K_1x06_P2.00mm_Vertical',
                     ref_at=(316, y - 12), val_at=(316, y + 14))
        cx(sh, j.pin('1'), f'MOT_{tag}_OUT1')
        cx(sh, j.pin('2'), f'MOT_{tag}_OUT2')
        cx(sh, j.pin('3'), '@+3V3')
        cx(sh, j.pin('4'), '@GND')
        cx(sh, j.pin('5'), f'ENC_{tag}_A_RAW')
        cx(sh, j.pin('6'), f'ENC_{tag}_B_RAW')
        horiz(sh, 'Device:C', f'C{refn + 7}', '100nF / X7R 50 V', 380, y - 26,
              f'MOT_{tag}_OUT1', f'MOT_{tag}_OUT2', C08)
        Rh(sh, f'R{refn + 9}', '100R', 268, y + 24, f'ENC_{tag}_A_RAW', f'$ENC_{tag}_A')
        Rh(sh, f'R{refn + 10}', '100R', 268, y + 38, f'ENC_{tag}_B_RAW', f'$ENC_{tag}_B')
        C(sh, f'C{refn + 8}', '1nF', 292, y + 30, f'$ENC_{tag}_A', '@GND')
        C(sh, f'C{refn + 9}', '1nF', 306, y + 30, f'$ENC_{tag}_B', '@GND')
        sh.note('Fils moteur torsades, 100 nF aux bornes.\n'
                'Filtre d entree du timer active en plus du RC.', 250, y + 52, 1.0)
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
                     x, y, fp='OptoDevice:Everlight_ITR8307', fields={'LCSC': 'C81632'},
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
    nmos_switch(sh, 'Q402', 280, 240, '$IR_BANK_B', 'IR_BANK_B_N', rref=('R443', 'R444'))
    sh.note('Banc A : voies paires.        Banc B : voies impaires.', 150, 236, 1.2)
    sh.note('Le rapport cyclique sur la grille pilote le courant d emission :\n'
            'une garde au sol de 6 mm au lieu de 3 se rattrape en logiciel,\n'
            'sans retoucher le PCB.', 150, 262, 1.0)
    return sh


# =====================================================================
#  05 - Telemetrie et centrale inertielle
# =====================================================================
def sheet_sensors():
    sh = Sheet(LIB, 'Capteurs', '05-sensors.kicad_sch', paper='A3',
               title='UsainBot - Telemetrie ToF, voie analogique rapide, inertie',
               rev=REV, date=DATE, company=COMPANY,
               comments=('Les deux VL53L1X vivent sur la languette verticale sechable, a 45 mm du sol',
                         'Adresse I2C identique en sortie de reset : readdressage au boot par XSHUT'))

    for k, (ref, tag, label, x) in enumerate((('U501', 'F', 'avant, 0 deg', 60),
                                              ('U502', 'FL', 'avant-gauche, 45 deg', 200))):
        u = sh.place('Sensor_Distance:VL53L1CXV0FY1', ref, 'VL53L1CBV0FY/1', x, 80,
                     fp='Sensor_Distance:ST_VL53L1x', fields={'LCSC': 'C2970716'},
                     ref_at=(x, 58), val_at=(x, 104))
        sh.box(x - 44, 30, 122, 130, f'Telemetre ToF {label}')
        cx(sh, u.pin('1'),  '@+3V3')
        cx(sh, u.pin('11'), '@+3V3')
        cx_bar(sh, u, ('2', '3', '4', '6', '12'), '@GND')
        cx(sh, u.pin('5'),  f'$TOF_{tag}_XSHUT')
        cx(sh, u.pin('7'),  f'$TOF_{tag}_INT')
        cx(sh, u.pin('8'),  'NC')
        cx(sh, u.pin('9'),  '$SDA1')
        cx(sh, u.pin('10'), '$SCL1')
        C(sh, f'C{501 + k * 2}', '100nF', x - 34, 130, '@+3V3', '@GND')
        C(sh, f'C{502 + k * 2}', '4u7F', x - 22, 130, '@+3V3', '@GND', C08)
        R(sh, f'R{501 + k * 2}', '10k', x + 44, 120, '@+3V3', f'$TOF_{tag}_XSHUT')
        R(sh, f'R{502 + k * 2}', '10k', x + 62, 120, '@+3V3', f'$TOF_{tag}_INT')

    R(sh, 'R505', '2k2', 24, 178, '@+3V3', '$SDA1')
    R(sh, 'R506', '2k2', 40, 178, '@+3V3', '$SCL1')
    sh.note('Tirage unique du bus I2C1, cote carte mere.', 18, 192, 1.0)
    sh.note('Composants nus reflowes par JLCPCB, pas de modules tout faits :\n'
            'c est l orientation qui compte, et elle doit etre gravee dans le cuivre.\n'
            'Mode long, budget 20 ms -> 50 Hz, soit 6 cm entre deux mesures a 3 m/s.',
            18, 202, 1.0)

    # ---------------------------------------------------------------- IMU
    sh.box(300, 30, 110, 130, 'Centrale inertielle  -  SPI2 a 10 MHz')
    u3 = sh.place('Pacabot:LSM6DSOTR', 'U503', 'LSM6DSOTR', 350, 84,
                  fp='Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y',
                  fields={'LCSC': 'C2655100'}, ref_at=(350, 60), val_at=(350, 110))
    cx(sh, u3.pin('1'),  '$IMU_MISO')
    cx(sh, u3.pin('2'),  '@GND')
    cx(sh, u3.pin('3'),  '@GND')
    cx(sh, u3.pin('4'),  '$IMU_INT1')
    cx(sh, u3.pin('5'),  '@+3V3')
    cx_bar(sh, u3, ('6', '7'), '@GND', offset=5.08)
    cx(sh, u3.pin('8'),  '@+3V3')
    cx(sh, u3.pin('9'),  'NC')
    cx(sh, u3.pin('10'), 'NC')
    cx(sh, u3.pin('11'), 'NC')
    cx(sh, u3.pin('12'), '$IMU_nCS')
    cx(sh, u3.pin('13'), '$IMU_SCK')
    cx(sh, u3.pin('14'), '$IMU_MOSI')
    C(sh, 'C505', '100nF', 312, 130, '@+3V3', '@GND')
    C(sh, 'C506', '100nF', 324, 130, '@+3V3', '@GND')
    sh.note('SDX et SCX a la masse : le bus auxiliaire n est pas utilise.\n'
            'A implanter au centre de rotation, pres de l essieu moteur.', 302, 150, 1.0)

    # ------------------------------------------ telemetre analogique lateral
    sh.box(16, 214, 268, 66, 'Telemetre analogique lateral gauche  -  mur de la Q1')
    R(sh, 'R507', '15R', 34, 232, '@+3V3', 'LASER_A')
    horiz(sh, 'Device:LED', 'D501', 'OPV302 - laser IR 850 nm', 64, 246,
          'LASER_K', 'LASER_A', 'Package_TO_SOT_THT:TO-18-2')
    nmos_switch(sh, 'Q501', 128, 246, '$IR_LASER_EN', 'LASER_K', rref=('R508', 'R509'))
    q2 = sh.place('Device:Q_Photo_NPN', 'Q502', 'BPW77NA', 182, 240,
                  fp='Package_TO_SOT_THT:TO-18-2', ref_at=(190, 232), val_at=(190, 236))
    cx(sh, q2.pin('C'), '@+3V3A')
    cx(sh, q2.pin('E'), 'PT_E')
    R(sh, 'R510', '47k', 206, 256, 'PT_E', '@GND')
    Rh(sh, 'R511', '1k', 230, 240, 'PT_E', '$TOF_ANA')
    C(sh, 'C507', '1nF', 256, 256, '$TOF_ANA', '@GND')
    sh.note('Lu a chaque conversion ADC, donc a 1 kHz, la ou un VL53L1X\n'
            'plafonne a 50 Hz. Calibration en intensite contre le vrai mur\n'
            'pendant les essais libres.\n\n'
            'Approvisionnement OPV302 / BPW77 a confirmer : pose manuelle\n'
            'sur une carte par ailleurs assemblee, ou repli sur un VL53L1X.\n'
            'Empreintes TO-18 a recaler sur le boitier reellement recu.',
            296, 176, 1.0)
    return sh


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
                 fp='Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',
                 ref_at=(46, 42), val_at=(46, 68))
    cx(sh, j.pin('1'), '@GND')
    cx(sh, j.pin('2'), '@+3V3')
    cx(sh, j.pin('3'), '$SCL2')
    cx(sh, j.pin('4'), '$SDA2')
    R(sh, 'R601', '4k7', 110, 60, '@+3V3', '$SDA2')
    R(sh, 'R602', '4k7', 126, 60, '@+3V3', '$SCL2')
    sh.note('Tirage du bus I2C2, partage avec le chargeur.\nBus lent, jamais sollicite en course.', 20, 92, 1.0)

    # ------------------------------------------------- switch 5 directions
    sh.box(180, 24, 230, 110, 'Switch 5 directions  -  navigation a deux dimensions, une seule piece')
    sw = sh.place('Pacabot:SW_Nav_5Way', 'SW601', 'TS-006 ou equivalent', 240, 70,
                  fp='', ref_at=(240, 52), val_at=(240, 88))
    dirs = (('1', 'SW_UP'), ('2', 'SW_DOWN'), ('3', 'SW_LEFT'),
            ('4', 'SW_RIGHT'), ('5', 'SW_PUSH'))
    for num, net in dirs:
        cx(sh, sw.pin(num), '$' + net)
    cx(sh, sw.pin('6'), '@GND')
    for i, (_, net) in enumerate(dirs):
        R(sh, f'R{603 + i}', '10k', 300 + i * 20, 52, '@+3V3', '$' + net)
        C(sh, f'C{601 + i}', '100nF', 300 + i * 20, 96, '$' + net, '@GND')
    sh.note('Empreinte a confirmer sur la reference retenue (LCSC C3674) :\n'
            'commun unique cote masse, cinq contacts au repos ouverts.', 184, 128, 1.0)

    # ---------------------------------------------------------- depart
    sh.box(16, 144, 194, 76, 'Depart  -  moyen conforme au chapitre 2 du reglement')
    swp = sh.place('Switch:SW_Push', 'SW602', 'START', 60, 168,
                   fp='Button_Switch_SMD:SW_SPST_B3U-1000P',
                   ref_at=(60, 158), val_at=(60, 162))
    cx(sh, swp.pin('1'), '$START_BTN')
    cx(sh, swp.pin('2'), '@GND')
    jj = sh.place('Connector_Generic:Conn_01x02', 'J602', 'Jack de depart', 60, 200,
                  fp='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',
                  ref_at=(46, 192), val_at=(46, 210))
    cx(sh, jj.pin('1'), '$START_BTN')
    cx(sh, jj.pin('2'), '@GND')
    R(sh, 'R608', '10k', 130, 168, '@+3V3', '$START_BTN')
    C(sh, 'C606', '100nF', 146, 168, '$START_BTN', '@GND')
    sh.note('Bouton et jack en parallele : les deux moyens que le reglement\n'
            'enumere sont cables, le geste devant le telemetre n en est\n'
            'qu un complement (voir la machine a etats du firmware).', 20, 220, 1.0)

    # ---------------------------------------------------------- buzzer
    sh.box(224, 144, 186, 76, 'Buzzer passif  -  TIM17, le seul retour lisible robot au sol')
    bz = sh.place('Device:Buzzer', 'BZ601', 'buzzer magnetique 9 x 5,5 mm', 280, 168,
                  fp='Buzzer_Beeper:MagneticBuzzer_ProSignal_ABI-009-RC',
                  ref_at=(292, 160), val_at=(292, 164))
    cx(sh, bz.pin('1'), '@+3V3')
    cx(sh, bz.pin('2'), 'BUZZ_D')
    horiz(sh, 'Device:D_Schottky', 'D601', 'BAT54', 330, 190, '@+3V3', 'BUZZ_D',
          'Diode_SMD:D_SOD-323')
    nmos_switch(sh, 'Q601', 280, 194, '$BUZZER', 'BUZZ_D', rref=('R609', 'R610'))
    sh.note('Diode de roue libre obligatoire : la bobine du buzzer\nrenvoie sa surtension dans le drain.', 300, 208, 1.0)

    # ---------------------------------------------------------- temoins
    sh.box(16, 228, 268, 48, 'Temoins')
    for i, (ref, net, col) in enumerate((('D602', 'LED_STATUS', 'verte - etat'),
                                         ('D603', 'LED_ERROR', 'rouge - defaut'),
                                         ('D604', 'LED_USER', 'jaune - libre'))):
        x = 40 + i * 84
        R(sh, f'R{611 + i}', '1k', x, 244, '$' + net, f'{net}_A')
        horiz(sh, 'Device:LED', ref, col, x + 32, 244, '@GND', f'{net}_A', LED06)
    sh.note('Le temoin " BLE alimente " visible du jury est cable sur le rail\n'
            '+3V3_BLE lui-meme (feuille 07) : il ne peut pas mentir sur l etat\n'
            'reel de l alimentation du module.', 18, 264, 1.0)
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
    C(sh, 'C702', '10uF/10V', 336, 62, '@+3V3_BLE', '@GND', C08)
    C(sh, 'C703', '100nF', 348, 62, '@+3V3_BLE', '@GND')
    R(sh, 'R706', '1k', 366, 62, '@+3V3_BLE', 'BLE_LED_A')
    horiz(sh, 'Device:LED', 'D701', 'bleue', 378, 88, '@GND', 'BLE_LED_A', LED06)
    flag(sh, '+3V3_BLE', 336, 96)
    j1 = sh.place('Connector_Generic:Conn_01x06', 'J701', 'Module BLE (HM-11 / ESP32-C3)',
                  240, 122, fp='Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',
                  ref_at=(224, 106), val_at=(224, 138))
    cx(sh, j1.pin('1'), '@GND')
    cx(sh, j1.pin('2'), '@+3V3_BLE')
    cx(sh, j1.pin('3'), '$BLE_TX')
    cx(sh, j1.pin('4'), '$BLE_RX')
    cx(sh, j1.pin('5'), 'NC')
    cx(sh, j1.pin('6'), 'NC')
    sh.note('PA8 haut = module alimente. Grille rappelee au rail par R703 :\n'
            'MCU eteint ou GPIO en haute impedance, le module reste hors tension.\n'
            'Broche 3 = RX du module, broche 4 = TX du module : a recroiser\n'
            'selon la serigraphie du module retenu.', 200, 150, 1.0)

    # ---------------------------------------------------------- turbine
    sh.box(16, 168, 394, 76, 'Turbine d appui  -  l ESC est autonome, la carte ne lui envoie qu une consigne')
    j2 = sh.place('Connector_Generic:Conn_01x03', 'J702', 'Embase ESC (signal)', 90, 200,
                  fp='Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
                  ref_at=(76, 188), val_at=(76, 214))
    cx(sh, j2.pin('1'), '@GND')
    cx(sh, j2.pin('2'), 'NC')
    cx(sh, j2.pin('3'), 'ESC_SIG')
    Rh(sh, 'R707', '100R', 150, 202, '$ESC_PWM', 'ESC_SIG')
    sh.note('Broche 2 = BEC. La plupart des ESC y sortent 5 ou 6 V :\n'
            'reliee au rail 3,3 V elle emporte toute la carte.\n'
            'Elle reste donc explicitement non connectee.', 76, 226, 1.0)
    j3 = sh.place('Connector_Generic:Conn_01x02', 'J703', 'Puissance turbine (XT30)',
                  300, 200, fp='Connector_AMASS:AMASS_XT30U-M_1x02_P5.0mm_Vertical',
                  ref_at=(286, 190), val_at=(286, 212))
    cx(sh, j3.pin('1'), '@VBAT')
    cx(sh, j3.pin('2'), '@GND')
    C(sh, 'C704', '220uF/16V', 344, 202, '@VBAT', '@GND', 'Capacitor_SMD:CP_Elec_8x10')
    C(sh, 'C705', '100nF', 358, 202, '@VBAT', '@GND')
    sh.note('Puissance prise sur VBAT en amont des ponts moteurs, avec son propre decouplage.\n'
            'Rampe la consigne : une montee en regime brutale fait chuter VBAT et peut faire\n'
            'redemarrer le MCU en pleine ligne droite. L armement de l ESC fait partie de la\n'
            'sequence de pre-depart, pas du demarrage du firmware.\n\n'
            'La turbine peut tirer 5 a 15 A : verifier que le fusible F101, l interrupteur J105\n'
            'et le MOSFET Q102 de la feuille 01 sont dimensionnes en consequence.',
            18, 252, 1.0)
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
           (210, 160, 170, 42, 8)]
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
    }
    for child, (x, y, w, h, _) in zip(children, lay):
        sh.note(blurb[child.filename], x + 3, y + 14, 1.2)

    sh.note('Points ouverts reportes du document d architecture :\n'
            '-  interrupteur et fusible dimensionnes a 10 A ; si la turbine tire vraiment 15 A,\n'
            '   c est toute la chaine de coupure qu il faut remonter, pas seulement le fusible ;\n'
            '-  OPV302 et BPW77 probablement hors bibliotheque JLCPCB : pose manuelle ou repli ToF ;\n'
            '-  valeurs marquees a recaler : R116 (frequence du buck), R107 (courant d equilibrage),\n'
            '   charge du quartz, R421-R432 (gain des voies de ligne).',
            210, 226, 1.3)
    return sh


def main():
    kids = [sheet_power_b(sheet_power()), sheet_mcu(), sheet_motors(),
            sheet_line(), sheet_sensors(), sheet_hmi(), sheet_comms()]
    root = sheet_root(kids)
    si = ['sheet_instances', ['path', q('/'), ['page', q('1')]]]
    for i, k in enumerate(kids, 2):
        si.append(['path', q('/' + k.uuid), ['page', q(str(i))]])
    os.makedirs(DEST, exist_ok=True)
    open(os.path.join(DEST, root.filename), 'w', encoding='utf-8').write(root.render([si]))
    for k in kids:
        open(os.path.join(DEST, k.filename), 'w', encoding='utf-8').write(k.render())
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
