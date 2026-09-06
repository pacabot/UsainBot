#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Empreintes Pacabot specifiques, ecrites en S-expression.

- OLED_096_I2C : embase 1x4 P2,54 + 4 percages M2 du module OLED 0,96".
  Courtyard limite a l embase et aux percages : le module est sur
  entretoises, le MCU vit dessous.  ENTRAXES A VERIFIER sur le module reel.
- SKRHABE010 : joystick Alps 4 directions + appui central, plan de pose
  releve sur le catalogue SKRH (vue face de pose, retournee ici en vue
  dessus).  Numeros de pads = broches du symbole SW_Nav_5Way
  (1 UP=A, 2 DOWN=C, 3 LEFT=D, 4 RIGHT=B, 5 PUSH=Center, 6 = commun).
- Telemetry_Duo : percage M2 centre entre les deux boitiers optiques d une
  station (entraxe 8,5 mm), pour visser un support/capot.
- ESC_Multistar_10A : le variateur de turbine monte DEBOUT sur sa tranche,
  cote entree de puissance - deux percages pour ses fils d alimentation,
  deux trous de collier, emprise 12 x 5 pour 22 mm de haut.
"""
import os, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'kicad-lib', 'Pacabot.pretty')


def U():
    return str(uuid.uuid4())


def fp_header(name, descr, attr='smd'):
    return (f'(footprint "{name}"\n\t(version 20240108)\n'
            f'\t(generator "pacabot")\n\t(generator_version "1")\n'
            f'\t(layer "F.Cu")\n\t(descr "{descr}")\n'
            f'\t(attr {attr})\n')


def text(kind, s, x, y, layer, size=1.0, hide=False):
    h = ' hide' if hide else ''
    return (f'\t(fp_text {kind} "{s}"\n\t\t(at {x} {y})\n'
            f'\t\t(layer "{layer}"){h}\n\t\t(uuid "{U()}")\n'
            f'\t\t(effects (font (size {size} {size}) (thickness 0.15)))\n\t)\n')


def line(x1, y1, x2, y2, layer, w=0.12):
    return (f'\t(fp_line (start {x1} {y1}) (end {x2} {y2}) '
            f'(stroke (width {w}) (type solid)) (layer "{layer}") '
            f'(uuid "{U()}"))\n')


def rect(x1, y1, x2, y2, layer, w=0.12):
    return (f'\t(fp_rect (start {x1} {y1}) (end {x2} {y2}) '
            f'(stroke (width {w}) (type solid)) (fill none) (layer "{layer}") '
            f'(uuid "{U()}"))\n')


def circle(cx, cy, r, layer, w=0.12):
    return (f'\t(fp_circle (center {cx} {cy}) (end {cx + r} {cy}) '
            f'(stroke (width {w}) (type solid)) (fill none) (layer "{layer}") '
            f'(uuid "{U()}"))\n')


def pad_smd(num, x, y, w, h):
    return (f'\t(pad "{num}" smd rect (at {x} {y}) (size {w} {h}) '
            f'(layers "F.Cu" "F.Paste" "F.Mask") (uuid "{U()}"))\n')


def pad_tht(num, x, y, dia, drill):
    return (f'\t(pad "{num}" thru_hole circle (at {x} {y}) (size {dia} {dia}) '
            f'(drill {drill}) (layers "*.Cu" "*.Mask") '
            f'(remove_unused_layers no) (uuid "{U()}"))\n')


def npth(x, y, drill):
    return (f'\t(pad "" np_thru_hole circle (at {x} {y}) '
            f'(size {drill} {drill}) (drill {drill}) (layers "F&B.Cu" "*.Mask") '
            f'(uuid "{U()}"))\n')


def write(name, body):
    path = os.path.join(OUT, name + '.kicad_mod')
    open(path, 'w').write(body + ')\n')
    print('  ', name)


# ------------------------------------------------------------- OLED 0,96"
# Cotes RELEVEES AU PIED A COULISSE sur l exemplaire du projet (09/2026) et
# reportees dans mechanics/oled096_i2c.py, qui produit le modele 3D : la
# variante montee est la carte raccourcie 27,0 x 24,7, pas les 27,3 x 27,8
# du module generique. L ecart portait sur les entraxes (23,0 x 20,7 au lieu
# de 23,3 x 23,8) : 1,55 mm sur les percages du haut et du bas, de quoi
# empecher les quatre entretoises de tomber en face.
W, H = 27.0, 24.7                 # carte du module (mesure)
HX, HY = W / 2 - 2.0, H / 2 - 2.0   # percages a 2 mm des bords -> 23,0 x 20,7
PIN_Y = -(H / 2 - 1.5)            # embase au bord haut
ENTRETOISE = 6.0                  # hauteur d entretoise : la queue des
                                  # broches (8,5 mm sous la face arriere)
                                  # ressort alors de 0,9 mm sous la carte
s = fp_header('OLED_096_I2C',
              'Module OLED 0,96 pouce SSD1306 I2C sur entretoises - '
              'embase 1x4 P2.54 + 4 percages M2. Carte 27,0 x 24,7 mesuree '
              f'sur la piece, entraxes {2 * HX:.1f} x {2 * HY:.1f}, module '
              f'porte a {ENTRETOISE} mm.', 'through_hole')
s += text('reference', 'REF**', 0, -H / 2 - 1.6, 'F.SilkS')
s += text('value', 'OLED_096_I2C', 0, H / 2 + 1.6, 'F.Fab')
for i in range(4):
    s += pad_tht(i + 1, -3.81 + i * 2.54, PIN_Y, 1.7, 1.0)
for sx in (-1, 1):
    for sy in (-1, 1):
        s += npth(sx * HX, sy * HY, 2.2)
s += rect(-W / 2, -H / 2, W / 2, H / 2, 'F.SilkS')
s += rect(-12.5, -8.05, 12.5, 5.95, 'F.SilkS')    # fenetre de verre (25 x 14)
s += text('user', 'GND VCC SCL SDA', 0, PIN_Y - 2.2, 'F.SilkS', 0.8)
s += rect(-W / 2, -H / 2, W / 2, H / 2, 'F.Fab', 0.1)
# courtyard : seulement l embase et les percages, le dessous reste habitable
s += rect(-5.2, PIN_Y - 1.3, 5.2, PIN_Y + 1.3, 'F.CrtYd', 0.05)
for sx in (-1, 1):
    for sy in (-1, 1):
        s += rect(sx * HX - 1.6, sy * HY - 1.6, sx * HX + 1.6, sy * HY + 1.6,
                  'F.CrtYd', 0.05)
for _m, _z in (('OLED_0.96_SSD1306_I2C_128x64', ENTRETOISE),
               ('OLED_Standoffs_M2x6', 0.0)):
    s += (f'\t(model "${{KIPRJMOD}}/kicad-lib/3d/{_m}.step"\n'
          f'\t\t(offset (xyz 0 0 {_z})) (scale (xyz 1 1 1)) '
          '(rotate (xyz 0 0 0)))\n')
write('OLED_096_I2C', s)

# ---------------------------------------------------------- SKRHABE010
# vue dessus (plan catalogue retourne) ; colonnes a +/-3.575
COL = 3.575
s = fp_header('SKRHABE010',
              'Alps SKRHABE010 - 4 directions + appui central, 7.35x7.5x1.8. '
              'Plan de pose du catalogue SKRH. Pads numerotes comme le '
              'symbole SW_Nav_5Way.')
s += text('reference', 'REF**', 0, -6.2, 'F.SilkS')
s += text('value', 'SKRHABE010', 0, 6.4, 'F.Fab')
# colonne droite (vue dessus) : A(1) / Center(5) / C(2)
s += pad_smd(1, COL, -1.85, 1.35, 1.4)
s += pad_smd(5, COL, 0, 1.35, 1.0)
s += pad_smd(2, COL, 1.85, 1.35, 1.4)
# colonne gauche : B(4) / Commun(6) / D(3)
s += pad_smd(4, -COL, -1.85, 1.35, 1.4)
s += pad_smd(6, -COL, 0, 1.35, 1.0)
s += pad_smd(3, -COL, 1.85, 1.35, 1.4)
# pattes mecaniques du capot (non numerotees)
s += pad_smd('', 0, -4.05, 2.0, 1.8)
s += pad_smd('', 0, 4.05, 2.0, 1.8)
# bossages de guidage
s += npth(0, -2.5, 0.75)
s += npth(0, 1.65, 1.05)
s += rect(-3.675, -3.75, 3.675, 3.75, 'F.SilkS')
s += circle(0, 0, 2.1, 'F.SilkS')
s += line(3.9, -2.7, 3.9, -1.0, 'F.SilkS')        # repere broche 1
s += rect(-3.675, -3.75, 3.675, 3.75, 'F.Fab', 0.1)
s += rect(-4.5, -5.2, 4.5, 5.2, 'F.CrtYd', 0.05)
s += ('\t(model "${KIPRJMOD}/kicad-lib/3d/SKRHABE010.step"\n'
      '\t\t(offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))\n')
write('SKRHABE010', s)

# ------------------------------------------------------- Telemetry_Duo
s = fp_header('Telemetry_Duo',
              'Percage M2 au centre du duo optique d une station de '
              'telemetrie (TX + RX a entraxe 10) - fixation d un support.',
              'through_hole exclude_from_pos_files exclude_from_bom')
s += text('reference', 'REF**', 0, -8.5, 'F.SilkS', 0.8)
s += text('value', 'Telemetry_Duo', 0, 8.5, 'F.Fab', 0.8)
s += npth(0, 0, 2.2)
s += circle(0, 0, 1.6, 'F.SilkS')
for sy in (-1, 1):
    s += circle(0, sy * 5.0, 3.45, 'F.Fab', 0.1)    # gabarits TX/RX
write('Telemetry_Duo', s)   # pas de courtyard : vis sur le support

# ------------------------------------------- ESC de turbine, monte DEBOUT
# Le Turnigy MultiStar 10A BLHeli-S (carte 22 x 12, 5,1 g, 10 A continu /
# 15 A crete, 2-4S, sans BEC) est fixe SUR LA TRANCHE, cote entree de
# puissance : ses deux fils d alimentation descendent dans les percages et le
# tiennent debout, les trois fils moteur sortent en haut vers la turbine.
# L emprise au sol tombe a 12 x 5 mm pour 22 mm de haut - la bande arriere
# n a que 7,2 mm de libre entre l embase USB et le courtyard de l equerre,
# c est la seule facon de l y loger.
# Le collier n est pas decoratif : deux soudures sur un robot qui encaisse
# 8 g au freinage ne tiennent pas un porte-a-faux de 22 mm.
ESC_W, ESC_T, ESC_H = 12.0, 5.0, 22.0
D_HOLE, D_PAD, PITCH = 2.0, 4.2, 5.08
s = fp_header('ESC_Multistar_10A',
              'Turnigy MultiStar 10A BLHeli-S Rev16 (Opto) monte DEBOUT sur '
              f'sa tranche, cote entree de puissance. Emprise {ESC_W} x '
              f'{ESC_T} mm, {ESC_H} mm de haut. Les deux fils d alimentation '
              f'se soudent dans deux percages {D_HOLE} mm au pas de {PITCH}, '
              'pastilles sur les deux faces ; deux trous de collier bridnt le '
              'corps. Broche 1 = +VBAT, broche 2 = GND. Le signal PWM part '
              'sur une broche coudee separee.',
              'through_hole exclude_from_pos_files')
s += text('reference', 'REF**', 0, -4.6, 'F.SilkS', 0.8)
s += text('value', 'ESC_Multistar_10A', 0, 4.8, 'F.Fab', 0.8)
s += pad_tht(1, -PITCH / 2, 0, D_PAD, D_HOLE)
s += pad_tht(2, PITCH / 2, 0, D_PAD, D_HOLE)
for sx in (-1, 1):                       # collier de bridage du corps
    s += npth(sx * (ESC_W / 2 + 1.6), 0, 2.0)
s += text('user', '+', -PITCH / 2, -3.0, 'F.SilkS', 1.0)
s += text('user', '-', PITCH / 2, -3.0, 'F.SilkS', 1.0)
s += text('user', 'ESC 10A', 0, 3.2, 'F.SilkS', 0.8)
s += circle(-PITCH / 2, 0, D_PAD / 2 + 0.25, 'F.SilkS')
s += rect(-ESC_W / 2, -ESC_T / 2, ESC_W / 2, ESC_T / 2, 'F.SilkS')
s += rect(-ESC_W / 2, -ESC_T / 2, ESC_W / 2, ESC_T / 2, 'F.Fab', 0.1)
# hauteur du variateur debout, en tirets : ce qui passe au-dessus
s += rect(-ESC_W / 2, -ESC_T / 2 - 0.6, ESC_W / 2, ESC_T / 2 + 0.6,
          'Dwgs.User', 0.1)
s += text('user', f'debout, h {ESC_H:.0f}', 0, -ESC_T / 2 - 1.4, 'Dwgs.User', 0.7)
s += rect(-ESC_W / 2 - 2.9, -ESC_T / 2 - 0.3, ESC_W / 2 + 2.9, ESC_T / 2 + 0.3,
          'F.CrtYd', 0.05)
s += ('\t(model "${KIPRJMOD}/kicad-lib/3d/ESC_Multistar_10A.step"\n'
      '\t\t(offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))\n')
write('ESC_Multistar_10A', s)

print('empreintes generees dans', os.path.relpath(OUT, HERE))
