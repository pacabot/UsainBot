"""Reviewed schematic blocks for the common 2S pack and external Bullet ESC.

The ESC module has six electrical ports but only three land on this PCB.
J103 is its three-pin mounting interface; ESC103 and M703 are off-board
electrical symbols. This preserves a real three-pad footprint without fake
motor copper on the motherboard. The module is counted once in the BOM.
"""
from pathlib import Path
import sexp
from kigen import q, fmt

ESC_FP = 'Pacabot:EMAX_Bullet_12A_Vertical_3Pin_PROTOTYPE'
ESC_URL = 'https://emax-usa.com/products/d-shot-bullet-series-12a-esc-blheli-s'

def prop(k, v, x=0, y=0, hidden=True):
    effects = ['effects', ['font', ['size', '1.27', '1.27']]]
    if hidden:
        effects.append(['hide', 'yes'])
    return ['property', q(k), q(v), ['at', fmt(x), fmt(y), '0'], effects]

def pin(number, name, x, y, angle, kind='passive'):
    return ['pin', kind, 'line', ['at', fmt(x), fmt(y), str(angle)],
            ['length', '2.54'],
            ['name', q(name), ['effects', ['font', ['size', '1.27', '1.27']]]],
            ['number', q(number), ['effects', ['font', ['size', '1.27', '1.27']]]]]

def symbol(name, ref, pins, description, fp='', on_board=True):
    return ['symbol', q(name), ['pin_names', ['offset', '1.016']],
            ['exclude_from_sim', 'no'], ['in_bom', 'yes'],
            ['on_board', 'yes' if on_board else 'no'],
            prop('Reference', ref, -12.7, 13.97, False),
            prop('Value', name, 0, -13.97, False), prop('Footprint', fp),
            prop('Datasheet', ESC_URL), prop('Description', description),
            ['symbol', q(name + '_0_1'),
             ['rectangle', ['start', '-17.78', '10.16'], ['end', '17.78', '-10.16'],
              ['stroke', ['width', '0.254'], ['type', 'default']],
              ['fill', ['type', 'background']]]],
            ['symbol', q(name + '_1_1')] + pins]

def ensure_symbols(library):
    root = sexp.parse(Path(library).read_text())[0]
    entries = [
        symbol('EMAX_Bullet_12A_EMX_SC_1873', 'ESC', [
            pin('1', 'GND_POWER', -20.32, -5.08, 0, 'power_in'),
            pin('2', 'SIGNAL', -20.32, 0, 0, 'input'),
            pin('3', '+BATT', -20.32, 5.08, 0, 'power_in'),
            pin('4', 'MOTOR_A', 20.32, 5.08, 180, 'output'),
            pin('5', 'MOTOR_B', 20.32, 0, 180, 'output'),
            pin('6', 'MOTOR_C', 20.32, -5.08, 180, 'output')],
            'Exact EMAX Bullet 12A BLHeli-S EMX-SC-1873; module outside motherboard. '
            'Input mounting via J103; phases wired directly to motor. Pin numbers are project mapping, '
            'not manufacturer numbering. Logic GND to power GND continuity must be measured.',
            ESC_FP, False),
        symbol('ESC_Vertical_Mount3', 'J', [
            pin('1', 'GND_POWER', -20.32, -5.08, 0),
            pin('2', 'SIGNAL', -20.32, 0, 0),
            pin('3', '+BATT', -20.32, 5.08, 0)],
            'Three motherboard holes for solid copper pins soldered to ESC input pads; '
            'prototype geometry estimated from photographs; insulating support required.', ESC_FP),
        symbol('Turbine_3Phase_Offboard', 'M', [
            pin('1', 'A', -20.32, 5.08, 0),
            pin('2', 'B', -20.32, 0, 0),
            pin('3', 'C', -20.32, -5.08, 0)],
            'Three phase turbine motor, wired directly to ESC; no motherboard pads.', '', False)
    ]
    names = {sexp.unq(s[1]) for s in entries}
    root[:] = [n for n in root if not (isinstance(n, list) and n[0] == 'symbol' and sexp.unq(n[1]) in names)]
    root.extend(entries)
    Path(library).write_text(sexp.dump(root) + '\n')

def offboard(sh, ref):
    for item in sh.items:
        if not isinstance(item, list) or item[0] != 'symbol':
            continue
        props = {sexp.unq(p[1]): sexp.unq(p[2]) for p in sexp.find_all(item, 'property')}
        if props.get('Reference') == ref:
            sexp.find(item, 'on_board')[1] = 'no'

def build_esc(sh, api):
    cx, C, Rh = api['cx'], api['C'], api['Rh']
    sh.box(16, 168, 394, 74, 'Turbine : EMAX Bullet 12A EMX-SC-1873 / BLHeli-S / sans BEC')
    Rh(sh, 'R707', '100R', 42, 190, '$ESC_PWM', 'ESC_SIG')
    mount = sh.place('Pacabot:ESC_Vertical_Mount3', 'J103', 'Montage vertical ESC (prototype)',
                     112, 208, fp=ESC_FP, in_bom=False,
                     ref_at=(112, 193), val_at=(112, 223),
                     fields={'Mechanical_status': 'PROTOTYPE - measure physical ESC before fabrication',
                             'Power_pins': 'Solid copper diameter 1.20 mm; holes 1.40 mm; pads 3.00 mm'})
    esc = sh.place('Pacabot:EMAX_Bullet_12A_EMX_SC_1873', 'ESC103', 'EMAX Bullet 12A EMX-SC-1873',
                   240, 208, fp=ESC_FP, datasheet=ESC_URL,
                   ref_at=(240, 189), val_at=(240, 193),
                   fields={'Manufacturer': 'EMAX', 'MPN': 'EMX-SC-1873',
                           'Motherboard_interface': 'J103; phases 4/5/6 are direct external wires',
                           'Ground_check': 'Confirm small logic GND continuity to large power GND before assembly'})
    for part in (mount, esc):
        cx(sh, part.pin('1'), '@GND', 7.62)
        cx(sh, part.pin('2'), 'ESC_SIG', 2.54)
        cx(sh, part.pin('3'), '@VPACK', 12.7)
    offboard(sh, 'ESC103')
    motor = sh.place('Pacabot:Turbine_3Phase_Offboard', 'M703', 'Turbine / fils hors PCB',
                     368, 208, in_bom=False, ref_at=(368, 193), val_at=(368, 223))
    offboard(sh, 'M703')
    for ep, mp, letter in [('4', '1', 'A'), ('5', '2', 'B'), ('6', '3', 'C')]:
        cx(sh, esc.pin(ep), 'ESC_PHASE_' + letter)
        cx(sh, motor.pin(mp), 'ESC_PHASE_' + letter)
    C(sh, 'C704', '220uF/16V', 170, 210, '@VPACK', '@GND', api['CPOL'])
    sh._need('Device:C_Polarized')
    for item in sh.items:
        if isinstance(item, list) and item[0] == 'symbol':
            props = {sexp.unq(p[1]): sexp.unq(p[2]) for p in sexp.find_all(item, 'property')}
            if props.get('Reference') == 'C704':
                sexp.find(item, 'lib_id')[1] = q('Device:C_Polarized')
    C(sh, 'C705', '100nF', 188, 210, '@VPACK', '@GND')
    sh.note('J103 : trois pins sur la carte. ESC103 et M703 : circuit externe, exclus du PCB.\n'
            'Les sorties moteur ne passent pas dans le cuivre de la carte.\n'
            'PCB ESC 11 x 15 mm; montage vertical avec soutien isolant a realiser.\n'
            'Entraxes et epaisseurs estimes sur photos : valider sur la piece avant fabrication.', 18, 255, 1.0)
    sh.note('VPACK = batterie brute : ESC sous tension tant que le pack est branche.\n'
            'F101 et le bouton coupent la carte / traction, pas la branche ESC.\n'
            'Pack commun 2S : protection generale et profil de charge a definir avec les cellules.\n'
            'Petit GND logique et gros GND puissance : continuite a mesurer; sinon 4e liaison requise.', 18, 277, 1.0)

def build_battery(sh, api, footprint):
    j = sh.place('Connector_Generic:Conn_01x03', 'J102', 'Pack 2S - AMASS MR30',
                  254, 46, fp=footprint, ref_at=(254, 33), val_at=(254, 61),
                  datasheet='https://lucidar.me/en/electronics/files/mr30pb-m.pdf',
                  fields={'Manufacturer': 'AMASS', 'MPN': 'MR30PB-M30.G.Y', 'Mating_connector': 'MR30-F.G.Y; optional cover 98023.PG', 'Harness': 'Project pinout: 1 GND / 2 PACK_MID / 3 VPACK; AWG16 power, AWG24 MID; 5cm power leads each assumed', 'Rated_current': '20 A per manufacturer at deltaT 85K with AWG16; thermal validation required at 15.5A continuous /18.5A peak', 'Mechanical_revision': 'AMASS MR30PB-M 2021V1: 11.9x5.3x10.4mm; 3mm tails; pitch3.50; drill1.80+0.20/0', 'Operating_budget': 'ESC 12A continuous /15A peak + 2 DC motors x1A + electronics provisional1.5A'})
    api['cx'](sh, j.pin('1'), '@GND', 7.62)
    api['cx'](sh, j.pin('2'), 'PACK_MID', 2.54)
    api['cx'](sh, j.pin('3'), '@VPACK', 15.24)
