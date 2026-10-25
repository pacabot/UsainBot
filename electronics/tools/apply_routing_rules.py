#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Applique au projet KiCad les regles calculees par routing_rules.py.

Trois ecritures ciblees, rien d autre n est touche :
  1. UsainBot.kicad_pro : classes de nets, affectations par motif, regles
     de carte, largeurs/vias/paire differentielle predefinies ;
  2. UsainBot.kicad_dru : regles DRC contextuelles (isolations par role) ;
  3. UsainBot.kicad_pcb : bloc (stackup ...) seul, remplace par JLC04161H-3313.
Le script est idempotent : le relancer reecrit les memes valeurs.
"""
import json
from pathlib import Path

import routing_rules as rr

PRJ = Path(__file__).resolve().parent.parent
PRO = PRJ / 'UsainBot.kicad_pro'
PCB = PRJ / 'UsainBot.kicad_pcb'
DRU = PRJ / 'UsainBot.kicad_dru'

# ------------------------------------------------------------ classes
# largeur = largeur de routage par defaut (tronc), arrondie au-dessus du
# calcul IPC-2221B a dT = 20 C ; wmin = minimum DRC hors courtyards.
USB_W, USB_GAP = 0.18, 0.20          # 89,7 ohms differentiel (solveur 2D)
CLASSES = [
    # nom, largeur, isolation, via (diam, foret), wmin, motifs, couleur
    ('PUISSANCE_PACK', 3.5, 0.20, (0.8, 0.4), 1.0,
     ['VPACK'], 'rgba(220, 40, 40, 0.8)'),
    ('PUISSANCE_VBAT', 3.2, 0.20, (0.8, 0.4), 1.0,
     ['VBAT', '/Alimentation/VBAT_SW_IN'], 'rgba(230, 120, 30, 0.8)'),
    ('MOTEUR_3A', 1.0, 0.20, (0.8, 0.4), 0.9,
     ['/Moteurs/MOT_?_OUT?'], 'rgba(200, 60, 160, 0.8)'),
    ('CHARGEUR_3A', 1.0, 0.15, (0.8, 0.4), 0.9,
     ['/Alimentation/VBUS_IN', '/Alimentation/PMID', '/Alimentation/SW_CHG',
      '/Alimentation/SNS_CHG'], 'rgba(230, 190, 30, 0.8)'),
    ('BUCK_2A', 0.6, 0.15, (0.8, 0.4), 0.5,
     ['/Alimentation/SW_BUCK'], 'rgba(160, 110, 40, 0.8)'),
    ('MASSE', 0.5, 0.15, (0.6, 0.3), 0.2,
     ['GND'], 'rgba(90, 90, 90, 0.8)'),
    ('RAIL_3V3', 0.4, 0.15, (0.6, 0.3), 0.2,
     ['+3V3'], 'rgba(40, 140, 220, 0.8)'),
    ('FAIBLE_300mA', 0.25, 0.15, (0.6, 0.3), 0.2,
     ['+3V3A', '+3V3_BLE', '/Barrette/IR_BANK_?_N', '/IHM/BUZZ_D',
      '/IHM/TRACK_SW', '/Capteurs/LAS_*', '/Alimentation/PACK_MID',
      '/Alimentation/CBSET_R', '/Alimentation/MID_R'], 'rgba(60, 170, 170, 0.8)'),
    ('USB_90R', USB_W, 0.15, (0.6, 0.3), USB_W - 0.01,
     ['USB_DP', 'USB_DM', '/Alimentation/USB_DP_C', '/Alimentation/USB_DM_C'],
     'rgba(40, 180, 60, 0.8)'),
    ('ANALOGIQUE', 0.2, 0.15, (0.6, 0.3), 0.15,
     ['/Capteurs/PD_*', '/Capteurs/TIA_*', '/Capteurs/G_*', '/Capteurs/CG_*',
      '/Capteurs/FB_*', '/Capteurs/AMP_*', '/Capteurs/VREF_*', 'RX_*',
      'LINE_??', 'IPROPI_?', '/Moteurs/IPROPI_?_RAW', '/Moteurs/VREF_MOT',
      'VBAT_SENSE', '/MCU/OSC_*', '/MCU/XTAL_OUT'], 'rgba(120, 80, 220, 0.8)'),
]

# Roles pour les regles contextuelles (motifs de nets, jokers KiCad)
COMMUTATION = ['/Alimentation/SW_BUCK', '/Alimentation/SW_CHG',
               '/Alimentation/BST_BUCK', '/Alimentation/BTST',
               '/Moteurs/MOT_?_OUT?', '/Moteurs/CP?_?', '/Moteurs/VCP_?',
               '/IHM/BUZZ_D', '/Barrette/IR_BANK_?_N']
EMISSION = ['TX_*', '/Capteurs/TXAC_*', '/Capteurs/LAS_*', 'ESC_PWM',
            '/Traces et turbine/ESC_SIG']
HAUTE_IMPEDANCE = ['/Capteurs/PD_*', '/Capteurs/TIA_*']
SENSIBLE = [p for c in CLASSES if c[0] == 'ANALOGIQUE' for p in c[5]]
USB = CLASSES[[c[0] for c in CLASSES].index('USB_90R')][5]


def any_net(side, pats):
    return '(' + ' || '.join(f"{side}.NetName == '{p}'" for p in pats) + ')'


def dru_text():
    hors = "!A.intersectsCourtyard('*')"
    r = ['(version 1)',
         '# Genere par tools/apply_routing_rules.py - justification :',
         '# routing-rules/README.md. Valeurs en mm explicites (sans unite,',
         '# KiCad lit des nanometres).', '']

    def rule(name, cons, cond):
        r.append(f'(rule "{name}"')
        for c in cons:
            r.append(f'  {c}')
        r.append(f'  (condition "{cond}"))')
        r.append('')

    # 1. largeurs minimales des classes de courant, hors courtyards (le
    #    retrecissement a l entree d une pastille fine reste permis)
    for name, w, _cl, _via, wmin, _p, _c in CLASSES:
        if name in ('USB_90R',):
            continue
        rule(f'Largeur mini {name}',
             [f'(constraint track_width (min {wmin}mm))'],
             f"A.Type == 'Track' && A.hasNetclass('{name}') && {hors}")
    # 2. USB : largeur tenue a +/-0,01 mm, ecart de paire, garde 0,3 mm
    rule('USB 90 ohms : largeur',
         [f'(constraint track_width (min {USB_W - 0.01:.2f}mm) (opt {USB_W}mm) '
          f'(max {USB_W + 0.01:.2f}mm))'],
         f"A.Type == 'Track' && A.hasNetclass('USB_90R') && {hors}")
    rule('USB 90 ohms : ecart de paire',
         [f'(constraint clearance (min {USB_GAP - 0.01:.2f}mm))'],
         f"A.hasNetclass('USB_90R') && B.hasNetclass('USB_90R') && {hors}")
    rule('USB 90 ohms : garde aux autres nets',
         ['(constraint clearance (min 0.3mm))'],
         f"A.hasNetclass('USB_90R') && !B.hasNetclass('USB_90R') && {hors}")
    # 3. noeuds commutes : 0,3 mm de tout autre net hors courtyards
    rule('Noeuds commutes : 0,3 mm',
         ['(constraint clearance (min 0.3mm))'],
         f'{any_net("A", COMMUTATION)} && {hors}')
    # 4. analogique : 0,3 mm (regle des 3W pour 0,15 mm), 0,5 mm en TIA
    rule('Analogique : 0,3 mm',
         ['(constraint clearance (min 0.3mm))'],
         f'{any_net("A", SENSIBLE)} && {hors}')
    rule('Entrees TIA 220 k : 0,5 mm',
         ['(constraint clearance (min 0.5mm))'],
         f'{any_net("A", HAUTE_IMPEDANCE)} && {hors}')
    # 5. agresseurs contre victimes : 1 mm
    rule('Commutation et emission loin de l analogique : 1 mm',
         ['(constraint clearance (min 1.0mm))'],
         f'({any_net("A", COMMUTATION)} || {any_net("A", EMISSION)}) && '
         f'{any_net("B", SENSIBLE)} && {hors}')
    # 6. vias des classes de puissance : foret 0,4 mm minimum
    pw = [c[0] for c in CLASSES if c[3] == (0.8, 0.4)]
    rule('Vias de puissance 0,4 / 0,8',
         ['(constraint hole_size (min 0.4mm))',
          '(constraint via_diameter (min 0.8mm))'],
         "A.Type == 'Via' && (" + ' || '.join(f"A.hasNetclass('{n}')" for n in pw) + ')')
    return '\n'.join(r)


def netclass(name, w, cl, via, color, prio, tmpl):
    d = dict(tmpl)
    d.update(name=name, track_width=w, clearance=cl, via_diameter=via[0],
             via_drill=via[1], priority=prio, pcb_color=color,
             diff_pair_width=USB_W, diff_pair_gap=USB_GAP, diff_pair_via_gap=0.25)
    return d


def update_pro():
    pro = json.loads(PRO.read_text())
    ns = pro['net_settings']
    tmpl = next(c for c in ns['classes'] if c['name'] == 'Default')
    tmpl.update(track_width=0.15, clearance=0.15, via_diameter=0.6, via_drill=0.3,
                diff_pair_width=USB_W, diff_pair_gap=USB_GAP, diff_pair_via_gap=0.25)
    ns['classes'] = [tmpl] + [netclass(n, w, cl, via, col, i, tmpl)
                              for i, (n, w, cl, via, _wm, _p, col) in enumerate(CLASSES)]
    ns['netclass_patterns'] = [{'netclass': c[0], 'pattern': p}
                               for c in CLASSES for p in c[5]]
    ds = pro['board']['design_settings']
    ds['rules'].update(min_clearance=0.15, min_track_width=0.15, min_via_diameter=0.5,
                       min_via_annular_width=0.1, min_through_hole_diameter=0.2,   # vias thermiques U102
                       min_hole_clearance=0.25, min_hole_to_hole=0.25,
                       min_copper_edge_clearance=0.5, min_connection=0.15)
    ds['track_widths'] = [0.0, 0.15, 0.2, 0.25, 0.4, 0.6, 1.0, 1.5, 2.0, 3.2, 3.5]
    ds['via_dimensions'] = [{'diameter': 0.0, 'drill': 0.0},
                            {'diameter': 0.6, 'drill': 0.3},
                            {'diameter': 0.8, 'drill': 0.4}]
    ds['diff_pair_dimensions'] = [{'gap': 0.0, 'via_gap': 0.0, 'width': 0.0},
                                  {'gap': USB_GAP, 'via_gap': 0.25, 'width': USB_W}]
    z = ds['defaults'].setdefault('zones', {})
    z.update(min_clearance=0.3, min_thickness=0.25, thermal_relief_gap=0.5,
             thermal_relief_spoke_width=0.5)
    PRO.write_text(json.dumps(pro, indent=2, ensure_ascii=False) + '\n')


def stackup_text():
    def cu(name):
        th = rr.CU_OUT if name in ('F.Cu', 'B.Cu') else rr.CU_IN
        return (f'\t\t\t(layer "{name}"\n\t\t\t\t(type "copper")\n'
                f'\t\t\t\t(thickness {th})\n\t\t\t)\n')

    def diel(i, kind, th, er, material):
        return (f'\t\t\t(layer "dielectric {i}"\n\t\t\t\t(type "{kind}")\n'
                f'\t\t\t\t(thickness {th:.4f})\n\t\t\t\t(material "{material}")\n'
                f'\t\t\t\t(epsilon_r {er})\n\t\t\t\t(loss_tangent 0.02)\n\t\t\t)\n')

    def mask(name, kind):
        return (f'\t\t\t(layer "{name}"\n\t\t\t\t(type "{kind}")\n'
                '\t\t\t\t(color "Black")\n\t\t\t\t(thickness 0.01)\n'
                '\t\t\t\t(material "Epoxy")\n\t\t\t\t(epsilon_r 3.3)\n'
                '\t\t\t\t(loss_tangent 0)\n\t\t\t)\n')
    s = '\t\t(stackup\n'
    s += '\t\t\t(layer "F.SilkS"\n\t\t\t\t(type "Top Silk Screen")\n\t\t\t)\n'
    s += '\t\t\t(layer "F.Paste"\n\t\t\t\t(type "Top Solder Paste")\n\t\t\t)\n'
    s += mask('F.Mask', 'Top Solder Mask')
    s += cu('F.Cu') + diel(1, 'prepreg', rr.PREPREG, rr.ER_PREPREG, '3313 x1')
    s += cu('In1.Cu') + diel(2, 'core', rr.CORE, rr.ER_CORE, 'FR4')
    s += cu('In2.Cu') + diel(3, 'prepreg', rr.PREPREG, rr.ER_PREPREG, '3313 x1')
    s += cu('B.Cu')
    s += mask('B.Mask', 'Bottom Solder Mask')
    s += '\t\t\t(layer "B.Paste"\n\t\t\t\t(type "Bottom Solder Paste")\n\t\t\t)\n'
    s += '\t\t\t(layer "B.SilkS"\n\t\t\t\t(type "Bottom Silk Screen")\n\t\t\t)\n'
    s += '\t\t\t(copper_finish "ENIG")\n\t\t\t(dielectric_constraints no)\n\t\t)\n'
    return s


def update_pcb():
    txt = PCB.read_text()
    a = txt.index('\t\t(stackup\n')
    b = txt.index('\n\t\t(pad_to_mask_clearance', a) + 1
    new = txt[:a] + stackup_text() + txt[b:]
    if new != txt:
        PCB.write_text(new)


def apply(_res=None):
    update_pro()
    DRU.write_text(dru_text() + '\n')
    update_pcb()


if __name__ == '__main__':
    apply()
