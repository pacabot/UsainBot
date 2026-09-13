#!/usr/bin/env python3
"""Read-only independent verification of the final MAIN KiCad board.

Run with KiCad's bundled Python. Inputs are the current board, the initial
ZIP, the newly exported schematic netlist, and the final ERC/DRC reports.
Only integration-verification.json is written. No board/schematic is saved.
"""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from sexp import parse, find, find_all, unq

EXCEPTIONS = {'J102', 'J103', 'J104', 'J702'}
SENSORS = {'U%d' % i for i in range(401, 413)}
EPS_MM = 0.000005
EPS_ANGLE = 0.000001


def angle_error(a, b):
    return abs((a - b + 180) % 360 - 180)


def xy(v):
    return [v.x / 1e6, v.y / 1e6]


def close(a, b, eps=EPS_MM):
    return len(a) == len(b) and all(abs(x - y) <= eps for x, y in zip(a, b))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(f):
    return {'uuid': f.m_Uuid.AsString(), 'xy': xy(f.GetPosition()),
            'angle': f.GetOrientationDegrees(), 'side': f.GetLayerName(),
            'locked': f.IsLocked(), 'footprint': f.GetFPIDAsString()}


def local(f, point):
    x, y = xy(point); fx, fy = xy(f.GetPosition())
    a = math.radians(f.GetOrientationDegrees()); c, s = math.cos(a), math.sin(a)
    return [(x - fx) * c - (y - fy) * s, (x - fx) * s + (y - fy) * c]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=ROOT)
    args = parser.parse_args(); project = args.project.resolve(); review = project / 'integration-review'
    board_path = project / 'UsainBot.kicad_pcb'; initial_zip = review / 'before-integration.zip'
    net_path = review / 'after-netlist.xml'; output = review / 'integration-verification.json'
    hashes_before = {str(p): sha(p) for p in [board_path, *sorted(project.glob('*.kicad_sch'))]}
    errors = []

    def check(condition, message, **detail):
        if not condition:
            errors.append({'check': message, **detail})

    board = pcbnew.LoadBoard(str(board_path)); fps = {f.GetReference(): f for f in board.GetFootprints()}
    check(len(fps) == len(list(board.GetFootprints())), 'duplicate footprint reference')
    with zipfile.ZipFile(initial_zip) as archive:
        before_raw = parse(archive.read('UsainBot.kicad_pcb').decode())[0]
    initial = {}
    for node in find_all(before_raw, 'footprint'):
        props = {unq(p[1]): unq(p[2]) for p in find_all(node, 'property')}
        ref = props.get('Reference'); at = find(node, 'at'); lock = find(node, 'locked')
        initial[ref] = {'uuid': unq(find(node, 'uuid')[1]),
                        'xy': [float(at[1]), float(at[2])],
                        'angle': float(at[3]) if len(at) > 3 else 0.0,
                        'side': unq(find(node, 'layer')[1]),
                        'locked': lock is not None and lock[1] == 'yes',
                        'footprint': unq(node[1])}
    original_locks = {r for r, f in initial.items() if f['locked']}
    preserved = sorted(original_locks - EXCEPTIONS); lock_records = []
    check(len(original_locks) == 40, 'original lock count', actual=len(original_locks))
    check(len(preserved) == 36, 'preserved lock count', actual=len(preserved))
    check(EXCEPTIONS.issubset(original_locks), 'authorized interfaces were originally locked')
    for ref in preserved:
        check(ref in fps, 'preserved locked reference missing', reference=ref)
        if ref not in fps:
            continue
        old, now = initial[ref], snapshot(fps[ref])
        equal = {'uuid': old['uuid'] == now['uuid'],
                 'xy_exact_nm': [round(v * 1e6) for v in old['xy']] ==
                                [round(v * 1e6) for v in now['xy']],
                 'angle': angle_error(old['angle'], now['angle']) <= EPS_ANGLE,
                 'side': old['side'] == now['side'], 'locked': now['locked']}
        check(all(equal.values()), 'locked pose/UUID changed', reference=ref, comparison=equal)
        lock_records.append({'reference': ref, 'before': old, 'after': now, 'equal': equal})
    for ref in ['J104', 'J702']:
        check(ref not in fps, 'obsolete interface still on board', reference=ref)
    for ref in ['J102', 'J103']:
        check(ref in fps, 'replacement interface missing', reference=ref)

    # Full net parity in both directions; duplicated thermal pads are all checked.
    tree = ET.parse(net_path).getroot(); components = {c.get('ref'): c for c in tree.find('components')}
    expected = {}; net_nodes = {}
    for net in tree.find('nets'):
        name = net.get('name'); net_nodes[name] = []
        for node in net.findall('node'):
            key = (node.get('ref'), node.get('pin'))
            check(key not in expected or expected[key] == name, 'duplicate schematic pin on different nets', pin=key)
            expected[key] = name; net_nodes[name].append(key)
    pcb_pads = collections.defaultdict(list); net_mismatches = []; numbered_count = 0
    for ref, f in fps.items():
        for pad in f.Pads():
            number = pad.GetNumber()
            if not number:
                check(not pad.GetNetname(), 'unnumbered pad carries unexpected net', reference=ref)
                continue
            numbered_count += 1; key = (ref, number); pcb_pads[key].append(pad)
            net = pad.GetNetname()
            if expected.get(key) != net:
                net_mismatches.append({'reference': ref, 'pad': number, 'pcb': net, 'schematic': expected.get(key)})
    excluded_board_components = sorted(ref for ref, c in components.items()
                                       if any(p.get('name') == 'exclude_from_board' for p in c.findall('property')))
    missing_connected_pads = []
    for key, name in expected.items():
        ref, pin = key
        if ref in excluded_board_components:
            continue
        if key not in pcb_pads:
            missing_connected_pads.append({'reference': ref, 'pin': pin, 'net': name})
    check(not net_mismatches, 'PCB pad net differs from schematic', mismatches=net_mismatches)
    check(not missing_connected_pads, 'schematic pin missing from PCB', missing=missing_connected_pads)
    footprint_mismatches = []
    for ref, c in components.items():
        if ref in excluded_board_components:
            continue
        if ref not in fps or c.findtext('footprint') != fps[ref].GetFPIDAsString():
            footprint_mismatches.append(ref)
    check(not footprint_mismatches, 'schematic footprint assignment mismatch', references=footprint_mismatches)
    mechanical_board_only = sorted(set(fps) - set(components))
    check(mechanical_board_only == ['M1', 'M2', 'M3'], 'unexpected PCB-only component', actual=mechanical_board_only)

    def pad(ref, number):
        ps = pcb_pads.get((ref, str(number)), [])
        check(len(ps) == 1, 'expected unique pad', reference=ref, number=str(number), count=len(ps))
        return ps[0]

    # Exact LED centres; inward anodes; same-index ADC/PCA9685 mapping.
    led_rows = []; sensor_rows = []
    s17_expected = {'1': [-.9, -2.11], '2': [-.9, 2.11],
                    '3': [.9, -2.11], '4': [.9, 2.11]}
    for index in range(12):
        sr, dr, rr = 'U%d' % (401 + index), 'D%d' % (401 + index), 'R%d' % (445 + index)
        sensor, led = fps[sr], fps[dr]; cathode, anode = pad(dr, 1), pad(dr, 2)
        a_local, k_local = local(sensor, anode.GetPosition()), local(sensor, cathode.GetPosition())
        lgn, line = '/Temoins de ligne/LGN%02d' % index, 'LINE_%02d' % index
        same_xy = sensor.GetPosition() == led.GetPosition()
        same_angle = angle_error(led.GetOrientationDegrees(), sensor.GetOrientationDegrees() + 90) <= EPS_ANGLE
        check(same_xy and same_angle and not led.IsFlipped(), 'LED alignment/orientation mismatch', reference=dr)
        check(close(a_local, [0, -.7875]) and close(k_local, [0, .7875]), 'LED anode is not radially inward', reference=dr)
        check(cathode.GetNetname() == lgn and anode.GetNetname() == lgn + '_A', 'LED polarity/net mismatch', reference=dr)
        check(pad(rr, 1).GetNetname() == '+3V3' and pad(rr, 2).GetNetname() == lgn + '_A', 'LED series resistor mapping', reference=rr)
        driver_pin = str(index + 6 if index < 8 else index + 7)
        check(pad('U105', driver_pin).GetNetname() == lgn, 'PCA9685 channel mapping', index=index)
        check(pad(sr, 4).GetNetname() == line, 'sensor ADC net mapping', reference=sr)
        check(sensor.GetFPIDAsString() == 'Pacabot:ITR8307_S17_TR8_Bottom', 'wrong S17 footprint', reference=sr)
        check(sensor.IsFlipped() and sensor.IsLocked(), 'sensor Bottom/lock mismatch', reference=sr)
        check('S17/TR8' in sensor.GetValue(), 'sensor value mismatch', reference=sr, value=sensor.GetValue())
        sensed = {}
        for number, wanted in s17_expected.items():
            p = pad(sr, number); actual = local(sensor, p.GetPosition())
            check(close(actual, wanted) and close(xy(p.GetSize()), [1.2, 1.4]) and close(xy(p.GetDrillSize()), [0, 0]),
                  'S17 pad geometry mismatch', reference=sr, pad=number, local_xy=actual)
            sensed[number] = {'net': p.GetNetname(), 'local_bottom_xy': actual, 'xy': xy(p.GetPosition()), 'size': xy(p.GetSize())}
        edge_items = [g for g in sensor.GraphicalItems() if g.GetLayer() == pcbnew.Edge_Cuts]
        check(not edge_items, 'S17 must not add a board window', reference=sr)
        distances = {'C_filter_mm': math.dist(xy(pad(sr, 4).GetPosition()), xy(pad('C%d' % (401 + index), 1).GetPosition())),
                     'R_load_mm': math.dist(xy(pad(sr, 4).GetPosition()), xy(pad('R%d' % (421 + index), 1).GetPosition())),
                     'R_IR_mm': math.dist(xy(pad(sr, 2).GetPosition()), xy(pad('R%d' % (401 + index), 2).GetPosition()))}
        check(max(distances.values()) < 1.34, 'sensor passive connection unexpectedly long', reference=sr, distances=distances)
        led_rows.append({'index': index, 'sensor': sr, 'led': dr, 'xy_exact': same_xy, 'angle_exact_within_tolerance': same_angle,
                         'anode_local': a_local, 'cathode_local': k_local, 'driver_pin': driver_pin, 'line_net': line})
        sensor_rows.append({'reference': sr, 'footprint': sensor.GetFPIDAsString(), 'value': sensor.GetValue(), 'pads': sensed, **distances})

    # New input interfaces: check real main-board pad maps, sizes, drills, and polarity.
    pinmaps = {}; connector_local = {
        'J102': {'1': ([11.4, 0], 'GND', [2.7, 2.7], [1.8, 1.8]),
                 '2': ([5.7, 0], '/Alimentation/PACK_MID', [2.7, 2.7], [1.8, 1.8]),
                 '3': ([0, 0], 'VPACK', [2.7, 2.7], [1.8, 1.8])},
        'J103': {'1': ([-4.3, 0], 'GND', [3, 3], [1.4, 1.4]),
                 '2': ([.8, .3], '/Traces et turbine/ESC_SIG', [1.6, 1.6], [.8, .8]),
                 '3': ([4.42, 0], 'VPACK', [3, 3], [1.4, 1.4])}}
    mechanical_holes = {}; expected_holes = {'J102': [(2.85, 1.34, 3), (8.55, 1.34, 3)],
                                             'J103': [(-7, 1.2, 1.7), (7, 1.2, 1.7)]}
    for ref, pins in connector_local.items():
        f = fps[ref]; pinmaps[ref] = {}
        check(not f.IsFlipped(), 'new connector not on Top', reference=ref)
        for number, (where, net, size, drill) in pins.items():
            p = pad(ref, number); at = local(f, p.GetPosition())
            record = {'net': p.GetNetname(), 'xy': xy(p.GetPosition()), 'local_xy': at,
                      'drill': xy(p.GetDrillSize()), 'size': xy(p.GetSize()),
                      'annular_ring_mm': min((s - h) / 2 for s, h in zip(xy(p.GetSize()), xy(p.GetDrillSize()))),
                      'zone_connection': int(p.GetLocalZoneConnection())}
            pinmaps[ref][number] = record
            check(close(at, where) and p.GetNetname() == net and close(record['size'], size) and close(record['drill'], drill),
                  'connector pinmap/geometry mismatch', reference=ref, pad=number, actual=record)
            check(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH, 'connector pin not plated through hole', reference=ref, pad=number)
            if number in ('1', '3'):
                check(int(p.GetLocalZoneConnection()) == 2, 'power pad not set to solid zone connection', reference=ref, pad=number)
        actual_holes = []
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                at = local(f, p.GetPosition()); actual_holes.append([*at, p.GetDrillSize().x / 1e6])
        actual_holes.sort(); expected_sorted = sorted(expected_holes[ref])
        check(len(actual_holes) == len(expected_sorted) and all(close(a, e) for a, e in zip(actual_holes, expected_sorted)),
              'connector mechanical holes mismatch', reference=ref, actual=actual_holes)
        mechanical_holes[ref] = actual_holes
    for ref in ['C704', 'C705']:
        check(pad(ref, 1).GetNetname() == 'VPACK' and pad(ref, 2).GetNetname() == 'GND', 'ESC capacitors must use raw battery', reference=ref)
    check(pad('R707', 1).GetNetname() == 'ESC_PWM' and pad('R707', 2).GetNetname() == '/Traces et turbine/ESC_SIG', 'ESC signal resistor path')
    check(pad('U201', 139).GetNetname() == 'ESC_PWM', 'MCU ESC output pin')

    bottom = sorted(r for r, f in fps.items() if f.IsFlipped()); tracks = list(board.GetTracks())
    vias = [t for t in tracks if isinstance(t, pcbnew.PCB_VIA)]; zones = list(board.Zones())
    counts = {'footprints': len(fps), 'top': len(fps) - len(bottom), 'bottom': len(bottom),
              'tracks': len(tracks) - len(vias), 'vias': len(vias), 'tracks_and_vias': len(tracks), 'zones': len(zones)}
    check(counts == {'footprints': 340, 'top': 328, 'bottom': 12, 'tracks': 0, 'vias': 0, 'tracks_and_vias': 0, 'zones': 0},
          'board totals/routing', actual=counts)
    check(set(bottom) == SENSORS, 'unexpected Bottom components', actual=bottom)
    native = {}
    for key, name in [('drc', 'drc-final.json'), ('erc', 'erc-final.json')]:
        path = review / name; report = json.loads(path.read_text())
        violations = report.get('violations', []) if key == 'drc' else [v for s in report['sheets'] for v in s['violations']]
        totals = collections.Counter(v['severity'] for v in violations)
        native[key] = {'report': str(path), 'sha256': sha(path), 'errors': totals.get('error', 0),
                       'warnings': totals.get('warning', 0), 'source': report.get('source'), 'date': report.get('date'),
                       'report_mtime_utc_epoch': path.stat().st_mtime}
        if key == 'drc':
            native[key]['unconnected_items'] = len(report['unconnected_items'])
            native[key]['schematic_parity_issues'] = len(report['schematic_parity'])
            check(totals.get('error', 0) == 0 and len(report['unconnected_items']) == 499 and len(report['schematic_parity']) == 0,
                  'native DRC result differs from final state', actual=native[key])
        else:
            check(len(violations) == 0, 'native ERC is not clean', actual=native[key])

    hashes_after = {name: sha(Path(name)) for name in hashes_before}
    check(hashes_after == hashes_before, 'board or schematic changed during read-only verification')
    result = {'schema': 'usainbot-final-integration-verification-v2', 'status': 'passed' if not errors else 'failed',
              'kicad_version': pcbnew.GetBuildVersion(), 'board': str(board_path), 'board_sha256': sha(board_path),
              'board_mtime_utc_epoch': board_path.stat().st_mtime, 'baseline_zip_sha256': sha(initial_zip),
              'netlist_sha256': sha(net_path), 'tolerances': {'pad_mm': EPS_MM, 'locked_angle_deg': EPS_ANGLE,
                                                           'locked_xy': 'exact integer nanometres'},
              **counts, 'original_locked_count': len(original_locks), 'preserved_locked_count': len(preserved),
              'preserved_locked_references': preserved, 'locked_checks': lock_records,
              'replaced_obsolete_locked_interfaces': sorted(EXCEPTIONS), 'removed_interfaces': ['J104', 'J702'],
              'led_alignment_exact': all(r['xy_exact'] and r['angle_exact_within_tolerance'] for r in led_rows),
              'led_checks': led_rows, 's17_sensor_checks': sensor_rows,
              'pad_net_checks': {'numbered_physical_pads_checked': numbered_count, 'unique_ref_pin_pairs': len(pcb_pads),
                                 'net_mismatches': net_mismatches, 'missing_connected_pads': missing_connected_pads,
                                 'footprint_assignment_mismatches': footprint_mismatches,
                                 'schematic_only_components': excluded_board_components,
                                 'mechanical_board_only_components': mechanical_board_only},
              'pinmaps': pinmaps, 'connector_npth_holes': mechanical_holes, 'native_reports': native,
              'input_board_and_schematics_unchanged': hashes_after == hashes_before, 'errors': errors,
              'scope_limit': 'This verifies board/schematic data and reads native reports; 3D collision, physical ESC metrology, current/thermal capability and harness identification remain separate engineering validations.'}
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'output': str(output), 'status': result['status'], **counts,
                      'preserved_locked_count': len(preserved), 'numbered_pads_checked': numbered_count,
                      'pad_net_mismatches': len(net_mismatches), 'errors': errors}, indent=2))
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())
