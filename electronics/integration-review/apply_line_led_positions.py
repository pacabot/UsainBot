#!/usr/bin/env python3
"""Apply the fixed LED geometry with KiCad's bundled Python, without routing.

The output is mandatory, so this script cannot overwrite the source board
accidentally. Existing locked footprints, all nets and routing are preserved.
The main integration script may instead call apply_positions(board, data).
"""

import argparse
import json
from pathlib import Path

import pcbnew


def snapshot(footprint):
    p = footprint.GetPosition()
    return (p.x, p.y, footprint.GetOrientationDegrees(),
            footprint.IsFlipped(), footprint.IsLocked())


def apply_positions(board, data):
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    locked = {r: snapshot(f) for r, f in footprints.items() if f.IsLocked()}
    nets = {(r, p.GetNumber()): p.GetNetname()
            for r, f in footprints.items() for p in f.Pads()}
    routing = (len(list(board.GetTracks())), len(list(board.Zones())))
    for ref, item in data['placements'].items():
        f = footprints[ref]
        if f.IsLocked():
            raise ValueError('Refusing to move locked footprint ' + ref)
        if f.IsFlipped():
            raise ValueError('Expected Top footprint ' + ref)
        old = item['before']
        p = f.GetPosition()
        if (abs(p.x / 1e6 - old['position'][0]) > 0.00001 or
                abs(p.y / 1e6 - old['position'][1]) > 0.00001 or
                abs(f.GetOrientationDegrees() - old['angle']) > 0.00001):
            raise ValueError('Footprint changed since analysis: ' + ref)
    for ref, item in data['placements'].items():
        f = footprints[ref]
        f.SetPosition(pcbnew.VECTOR2I(*(round(v * 1e6)
                                      for v in item['position'])))
        f.SetOrientationDegrees(item['angle'])
        f.Reference().SetLayer(pcbnew.F_Fab)
        f.Reference().SetPosition(f.GetPosition())
        f.Reference().SetTextAngle(pcbnew.EDA_ANGLE(0, pcbnew.DEGREES_T))
    for item in data['associations']:
        sensor, led = footprints[item['sensor']], footprints[item['led']]
        assert sensor.GetPosition() == led.GetPosition()
        assert sensor.IsFlipped() and not led.IsFlipped()
        assert abs((led.GetOrientationDegrees() -
                    sensor.GetOrientationDegrees() - 90) % 360) < 1e-7
    assert locked == {r: snapshot(footprints[r]) for r in locked}
    assert nets == {(r, p.GetNumber()): p.GetNetname()
                    for r, f in footprints.items() for p in f.Pads()}
    assert routing == (len(list(board.GetTracks())), len(list(board.Zones())))
    return board


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--positions', type=Path,
                        default=Path(__file__).with_name('line-led-positions.json'))
    args = parser.parse_args()
    if args.board.resolve() == args.output.resolve():
        raise ValueError('Use a different output path, inspect, then integrate.')
    data = json.loads(args.positions.read_text())
    board = apply_positions(pcbnew.LoadBoard(str(args.board)), data)
    pcbnew.SaveBoard(str(args.output), board)
    print('Saved %s; %s placements; locked components and nets preserved.' %
          (args.output, len(data['placements'])))


if __name__ == '__main__':
    main()
