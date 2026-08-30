# -*- coding: utf-8 -*-
"""Construit electronics/kicad-lib/Pacabot.kicad_sym : symboles propres au projet."""
import json, os, sys
import sexp
from kigen import SymLib, q, fmt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(
    os.path.join(HERE, '..', 'kicad-lib', 'Pacabot.kicad_sym'))
lib = SymLib()

def P(name, val, x, y, ang, length=2.54, etype='bidirectional', style='line'):
    return ['pin', etype, style, ['at', fmt(x), fmt(y), str(ang)], ['length', fmt(length)],
            ['name', q(name), ['effects', ['font', ['size', '1.27', '1.27']]]],
            ['number', q(val), ['effects', ['font', ['size', '1.27', '1.27']]]]]

def prop(k, v, x=0.0, y=0.0, hide=True, ang=0):
    e = ['effects', ['font', ['size', '1.27', '1.27']]]
    if hide:
        e.append(['hide', 'yes'])
    return ['property', q(k), q(v), ['at', fmt(x), fmt(y), str(ang)], e]

def rect(x1, y1, x2, y2):
    return ['rectangle', ['start', fmt(x1), fmt(y1)], ['end', fmt(x2), fmt(y2)],
            ['stroke', ['width', '0.254'], ['type', 'default']],
            ['fill', ['type', 'background']]]

syms = []

# ------------------------------------------------------------ DRV8874PWPR
left = [(12.7, '1', 'EN/IN1', 'input'), (10.16, '2', 'PH/IN2', 'input'),
        (7.62, '3', 'nSLEEP', 'input'), (5.08, '4', '~{nFAULT}', 'open_collector'),
        (0.0, '5', 'VREF', 'input'), (-2.54, '6', 'IPROPI', 'output'),
        (-7.62, '7', 'IMODE', 'input'), (-10.16, '16', 'PMODE', 'input')]
right = [(12.7, '11', 'VM', 'power_in'), (10.16, '12', 'VCP', 'power_out'),
         (7.62, '13', 'CPH', 'passive'), (5.08, '14', 'CPL', 'passive'),
         (-5.08, '8', 'OUT1', 'output'), (-7.62, '10', 'OUT2', 'output')]
bottom = [(-5.08, '15', 'GND', 'power_in'), (0.0, '9', 'PGND', 'power_in'),
          (5.08, '17', 'PAD', 'power_in')]
pins = [P(n, num, -15.24, y, 0, etype=t) for y, num, n, t in left]
pins += [P(n, num, 15.24, y, 180, etype=t) for y, num, n, t in right]
pins += [P(n, num, x, -20.32, 90, etype=t) for x, num, n, t in bottom]
syms.append(['symbol', q('DRV8874PWPR'),
             ['pin_names', ['offset', '1.016']],
             ['exclude_from_sim', 'no'], ['in_bom', 'yes'], ['on_board', 'yes'],
             prop('Reference', 'U', -15.24, 20.32, False),
             prop('Value', 'DRV8874PWPR', 15.24, 20.32, False),
             prop('Footprint', 'Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm'),
             prop('Datasheet', 'https://www.ti.com/lit/ds/symlink/drv8874.pdf'),
             prop('Description', 'Pont en H 37 V / 6 A, retour de courant IPROPI, HTSSOP-16 PowerPAD'),
             prop('ki_keywords', 'H-bridge motor driver DRV887x'),
             prop('ki_fp_filters', 'HTSSOP*1EP*4.4x5mm*P0.65mm*'),
             ['symbol', q('DRV8874PWPR_0_1'), rect(-12.7, 17.78, 12.7, -17.78)],
             ['symbol', q('DRV8874PWPR_1_1')] + pins])

# ------------------------------------------------------------ LSM6DSOTR
flat, _ = lib.flat('Sensor_Motion:LSM6DS3')
clone = json.loads(json.dumps(flat))
clone[1] = q('LSM6DSOTR')
for n in clone:
    if isinstance(n, list) and n[0] == 'symbol':
        n[1] = q(sexp.unq(n[1]).replace('LSM6DS3', 'LSM6DSOTR', 1))
        # SDX et SCX sont strappees a la masse (bus auxiliaire inutilise) :
        # les laisser bidirectionnelles fait crier l ERC sans raison.
        for p in sexp.find_all(n, 'pin'):
            if sexp.unq(sexp.find(p, 'number')[1]) in ('2', '3'):
                p[1] = 'passive'
    if isinstance(n, list) and n[0] == 'property':
        k = sexp.unq(n[1])
        if k == 'Value':
            n[2] = q('LSM6DSOTR')
        elif k == 'Datasheet':
            n[2] = q('https://www.st.com/resource/en/datasheet/lsm6dso.pdf')
        elif k == 'Description':
            n[2] = q('Centrale inertielle 6 axes, SPI/I2C, LGA-14 3x2.5 mm')
syms.append(clone)

# ------------------------------------------------------------ SW_Nav_5Way
np_ = [P('UP', '1', -12.7, 7.62, 0, etype='passive'),
       P('DOWN', '2', -12.7, 2.54, 0, etype='passive'),
       P('LEFT', '3', -12.7, -2.54, 0, etype='passive'),
       P('RIGHT', '4', -12.7, -7.62, 0, etype='passive'),
       P('PUSH', '5', 12.7, 7.62, 180, etype='passive'),
       P('COM', '6', 12.7, -7.62, 180, etype='passive')]
syms.append(['symbol', q('SW_Nav_5Way'),
             ['pin_names', ['offset', '1.016']],
             ['exclude_from_sim', 'no'], ['in_bom', 'yes'], ['on_board', 'yes'],
             prop('Reference', 'SW', -10.16, 13.97, False),
             prop('Value', 'SW_Nav_5Way', 10.16, 13.97, False),
             prop('Footprint', ''),
             prop('Datasheet', '~'),
             prop('Description', 'Switch 5 directions (haut, bas, gauche, droite, appui) a commun unique'),
             prop('ki_keywords', 'navigation switch 5-way joystick TS-006'),
             ['symbol', q('SW_Nav_5Way_0_1'), rect(-10.16, 11.43, 10.16, -11.43)],
             ['symbol', q('SW_Nav_5Way_1_1')] + np_])

# ------------------------------------------------------------ ITR8307
# Copie du symbole standard : les broches du phototransistor sont retypees en
# passif. Collecteur ouvert / emetteur ouvert font hurler l ERC des qu on les
# relie a un rail, ce qui est pourtant exactement le montage voulu ici.
flat_itr, _ = lib.flat('Sensor_Proximity:ITR8307-S17-TR8')
itr = json.loads(json.dumps(flat_itr))
itr[1] = q('ITR8307')
for n in itr:
    if isinstance(n, list) and n[0] == 'symbol':
        n[1] = q(sexp.unq(n[1]).replace('ITR8307-S17-TR8', 'ITR8307', 1))
        for p in sexp.find_all(n, 'pin'):
            if sexp.unq(sexp.find(p, 'number')[1]) in ('3', '4'):
                p[1] = 'passive'
    if isinstance(n, list) and n[0] == 'property':
        k = sexp.unq(n[1])
        if k == 'Value':
            n[2] = q('ITR8307/S17/TR8')
        elif k == 'Footprint':
            n[2] = q('OptoDevice:Everlight_ITR8307')
        elif k == 'Description':
            n[2] = q('Capteur reflectif infrarouge, SMD-4, pas de 10 mm sur la barrette')
syms.append(itr)

# ------------------------------------------------------------ AO4407A (SO-8)
gp = [P('G', '4', -12.7, 0.0, 0, etype='input')]
gp += [P('S', n, x, -12.7, 90, etype='passive') for n, x in zip(('1','2','3'), (-5.08, 0.0, 5.08))]
gp += [P('D', n, x, 12.7, 270, etype='passive') for n, x in zip(('5','6','7','8'), (-7.62, -2.54, 2.54, 7.62))]
syms.append(['symbol', q('AO4407A'),
             ['pin_names', ['offset', '1.016']],
             ['exclude_from_sim', 'no'], ['in_bom', 'yes'], ['on_board', 'yes'],
             prop('Reference', 'Q', -10.16, 15.24, False),
             prop('Value', 'AO4407A', 10.16, 15.24, False),
             prop('Footprint', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'),
             prop('Datasheet', 'http://www.aosmd.com/pdfs/datasheet/AO4407A.pdf'),
             prop('Description', 'MOSFET canal P -30 V / -12 A, SO-8 (protection anti-inversion)'),
             prop('ki_keywords', 'P-channel MOSFET reverse polarity protection SO-8'),
             prop('ki_fp_filters', 'SOIC*3.9x4.9mm*P1.27mm*'),
             ['symbol', q('AO4407A_0_1'), rect(-10.16, 10.16, 10.16, -10.16),
              ['polyline', ['pts', ['xy', '-5.08', '5.08'], ['xy', '5.08', '5.08'],
                            ['xy', '0', '0'], ['xy', '-5.08', '5.08']],
               ['stroke', ['width', '0.254'], ['type', 'default']],
               ['fill', ['type', 'none']]]],
             ['symbol', q('AO4407A_1_1')] + gp])

# ------------------------------------------------------------ rails propres
BASE, _ = lib.flat('power:+3V3')
for rail, desc in [('VBAT', 'Bus batterie commute 5,0 a 7,3 V'),
                   ('VPACK', 'Sortie brute du pack 2S, en amont de l interrupteur'),
                   ('+3V3A', 'Rail 3,3 V analogique filtre (VDDA, VREF+, barrette)'),
                   ('+3V3_BLE', 'Rail 3,3 V commute du module BLE')]:
    c = json.loads(json.dumps(BASE))
    c[1] = q(rail)
    for n in c:
        if isinstance(n, list) and n[0] == 'symbol':
            n[1] = q(sexp.unq(n[1]).replace('+3V3', rail, 1))
            for p in sexp.find_all(n, 'pin'):
                sexp.find(p, 'name')[1] = q(rail)
        if isinstance(n, list) and n[0] == 'property':
            k = sexp.unq(n[1])
            if k == 'Value':
                n[2] = q(rail)
            elif k == 'Description':
                n[2] = q(desc)
    syms.append(c)

root = ['kicad_symbol_lib', ['version', '20241209'], ['generator', q('kicad_symbol_editor')],
        ['generator_version', q('9.0')]] + syms
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w', encoding='utf-8').write(sexp.dump(root) + '\n')

# Normalisation par KiCad lui-meme : le schema embarque une copie de chaque
# symbole et la compare a la librairie. Sans ce passage, la moindre difference
# de mise en forme leve un avertissement << ne correspond pas a la copie >>.
import shutil, subprocess
cli = shutil.which('kicad-cli')
if cli:
    subprocess.run([cli, 'sym', 'upgrade', '--force', OUT],
                   check=True, capture_output=True)
    print('ecrit et normalise', OUT, '-', len(syms), 'symboles')
else:
    print('ecrit', OUT, '-', len(syms), 'symboles')
    print('ATTENTION : kicad-cli absent, lancer << kicad-cli sym upgrade --force >> '
          'sur ce fichier avant design.py')
