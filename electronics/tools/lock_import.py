#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Relit dans le PCB les empreintes verrouillees et les fige dans locked.json.

Une empreinte verrouillee dans pcbnew est une decision prise a l ecran, sur
la piece reelle - un connecteur qu on veut a cet endroit du bord, un pont en H
colle a son moteur. Elle prime sur la table de `layout.py`, qui doit s y
plier : ce script fait le pont dans ce sens-la, et `layout.py` applique
`locked.json` par-dessus ses propres coordonnees.

A relancer chaque fois qu on verrouille (ou deverrouille) quelque chose :

    "$KPY" lock_import.py        # KPY = python de KiCad

Sans pcbnew sous la main, le fichier se relit aussi tel quel : c est du JSON
{ref: [x, y, rot, face]}.
"""
import json
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, '..', 'UsainBot.kicad_pcb')
OUT = os.path.join(HERE, 'locked.json')

board = pcbnew.LoadBoard(BOARD)
table = {}
for f in board.GetFootprints():
    if not f.IsLocked():
        continue
    p = f.GetPosition()
    table[f.GetReference()] = [round(pcbnew.ToMM(p.x), 3), round(pcbnew.ToMM(p.y), 3),
                               round(f.GetOrientationDegrees(), 3),
                               'B' if f.IsFlipped() else 'F']
json.dump(table, open(OUT, 'w'), indent=0, sort_keys=True)
print(f'{len(table)} empreintes verrouillees relevees -> {os.path.relpath(OUT, HERE)}')
for ref in sorted(table):
    x, y, rot, side = table[ref]
    print(f'  {ref:6s} {x:8.2f} {y:8.2f} {rot:7.1f} {side}')
