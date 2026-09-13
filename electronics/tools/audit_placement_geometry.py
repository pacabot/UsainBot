#!/usr/bin/env python3
"""Read-only KiCad placement geometry export and independent Shapely audit.

Run with KiCad's Python (pcbnew), passing the board and output JSON. The
optional --analysis-python argument lets Shapely run in a different Python
environment, avoiding KiCad's bundled-Python ABI dependency. All coordinates
and distances are in millimetres. Polygons are ordinary GeoJSON geometries.

The audit uses KiCad's actual courtyard polygons, including their orientation,
concavities and disconnected islands. OLED's existing courtyard correctly
reserves only its header and mounting spacers, allowing parts below the screen.
Motor/turbine/telemetry courtyard reservations apply to their assembly face;
board cutouts and NPTH drill clearances apply on both faces. This is a placement
audit, not a replacement for KiCad's pad/copper/clearance DRC or a 3D check.
"""

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

DEFAULT_BOARD = Path(__file__).resolve().parent.parent / 'UsainBot.kicad_pcb'
EXCEPTIONS = {frozenset((ref, 'M3')) for ref in ('J102', 'J103', 'J104')}
MECHANICAL = {'M1', 'M2', 'M3', 'J601', 'TM501', 'TM521', 'TM541'}
LINE_SENSORS = {'U%d' % i for i in range(401, 413)}


def export_geometry(board_path):
    import pcbnew

    def xy(point):
        return [round(point.x / 1e6, 7), round(point.y / 1e6, 7)]

    def ring(chain):
        points = [xy(chain.CPoint(j)) for j in range(chain.PointCount())]
        if points and points[-1] != points[0]:
            points.append(points[0])
        return points

    def polyset(poly):
        polygons = []
        for i in range(poly.OutlineCount()):
            rings = [ring(poly.COutline(i))]
            rings += [ring(poly.Hole(i, h)) for h in range(poly.HoleCount(i))]
            if len(rings[0]) >= 4:
                polygons.append(rings)
        return {'type': 'MultiPolygon', 'coordinates': polygons}

    board = pcbnew.LoadBoard(str(board_path))
    outline = pcbnew.SHAPE_POLY_SET()
    outline_ok = board.GetBoardPolygonOutlines(outline, False)
    footprints, drills, auxiliary_envelopes = {}, [], []
    for footprint in board.GetFootprints():
        ref = footprint.GetReference()
        footprint.BuildCourtyardCaches()
        courtyards = {
            'F': polyset(footprint.GetCourtyard(pcbnew.F_CrtYd)),
            'B': polyset(footprint.GetCourtyard(pcbnew.B_CrtYd)),
        }
        pads = []
        for index, pad in enumerate(footprint.Pads()):
            pad_geom = pcbnew.SHAPE_POLY_SET()
            pad.TransformShapeToPolygon(pad_geom, pad.GetLayer(), 0, 5000,
                                        pcbnew.ERROR_OUTSIDE)
            entry = {
                'number': pad.GetNumber(), 'net': pad.GetNetname(),
                'position': xy(pad.GetPosition()), 'size': xy(pad.GetSize()),
                'angle': pad.GetOrientationDegrees(),
                'attribute': int(pad.GetAttribute()), 'geometry': polyset(pad_geom),
                'copper_faces': [face for face, layer in
                                 [('F', pcbnew.F_Cu), ('B', pcbnew.B_Cu)]
                                 if pad.IsOnLayer(layer)],
            }
            pads.append(entry)
            if pad.GetDrillSize().x or pad.GetDrillSize().y:
                hole = pcbnew.SHAPE_POLY_SET()
                pad.TransformHoleToPolygon(hole, 0, 5000, pcbnew.ERROR_OUTSIDE)
                drills.append({
                    'ref': ref, 'pad': pad.GetNumber(), 'index': index,
                    'npth': pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH,
                    'geometry': polyset(hole),
                    # M3's silkscreen reserves an M2 screw/washer radius of
                    # 1.8 mm, outside its principal circular courtyard.
                    'mechanical_radius_mm': 1.8 if ref == 'M3' else None,
                })
        footprints[ref] = {
            'reference': ref, 'value': footprint.GetValue(),
            'footprint': footprint.GetFPIDAsString(),
            'position': xy(footprint.GetPosition()),
            'angle': footprint.GetOrientationDegrees(),
            'face': 'B' if footprint.IsFlipped() else 'F',
            'locked': footprint.IsLocked(),
            'mechanical_reservation': ref in MECHANICAL,
            'courtyards': courtyards, 'pads': pads,
        }
        if ref == 'M3':
            for drawing in footprint.GraphicalItems():
                if (drawing.GetLayer() == pcbnew.Dwgs_User and
                        hasattr(drawing, 'GetShape') and
                        drawing.GetShape() == pcbnew.SHAPE_T_CIRCLE):
                    center, radius = xy(drawing.GetCenter()), drawing.GetRadius() / 1e6
                    points = [[center[0] + radius * math.cos(i * math.tau / 256),
                               center[1] + radius * math.sin(i * math.tau / 256)]
                              for i in range(256)]
                    points.append(points[0])
                    auxiliary_envelopes.append({
                        'ref': ref, 'face': 'F', 'status': 'indicative',
                        'source': 'M3 User.Drawings: collier imprime dia 48 indicatif',
                        'radius_mm': radius,
                        'geometry': {'type': 'Polygon', 'coordinates': [points]},
                    })
    return {
        'schema': 'usainbot-placement-geometry-v1', 'units': 'mm',
        'board': str(board_path.resolve()),
        'sha256': hashlib.sha256(board_path.read_bytes()).hexdigest(),
        'kicad_version': pcbnew.GetBuildVersion(),
        'board_outline_valid': outline_ok,
        'board_polygon': polyset(outline),
        'footprints': footprints, 'drills': drills,
        'auxiliary_mechanical_envelopes': auxiliary_envelopes,
        'allowed_overlap_pairs': [sorted(pair) for pair in EXCEPTIONS],
        'tracks': len(list(board.GetTracks())), 'zones': len(list(board.Zones())),
    }


def audit_geometry(data, npth_clearance=0.25):
    from shapely.geometry import shape, Polygon
    from shapely.ops import unary_union

    fps = data['footprints']
    issues, accepted, geometry_warnings = [], [], []

    def geom(raw, label):
        result = shape(raw)
        if not result.is_valid:
            geometry_warnings.append(label)
            result = result.buffer(0)
        return result

    board = geom(data['board_polygon'], 'board')
    # Courtyards can legitimately overhang the exterior at a connector edge.
    # Such overhang is reported separately from intrusion into a board cutout.
    exterior = unary_union([Polygon(p.exterior)
                            for p in getattr(board, 'geoms', [board])])
    cutouts = exterior.difference(board)
    courtyard = {ref: {face: geom(poly, '%s:%s' % (ref, face))
                       for face, poly in f['courtyards'].items()}
                 for ref, f in fps.items()}

    def add(kind, refs, geometry=None, **extra):
        item = {'kind': kind, 'references': refs,
                'all_locked': all(fps[ref]['locked'] for ref in refs), **extra}
        if geometry is not None:
            item['overlap_mm2'] = round(geometry.area, 6)
            item['position'] = [round(v, 4) for v in geometry.centroid.coords[0]]
        (accepted if frozenset(refs) in EXCEPTIONS else issues).append(item)

    refs = sorted(fps)
    for i, ref in enumerate(refs):
        footprint = fps[ref]
        if footprint['face'] == 'B' and ref not in LINE_SENSORS:
            add('wrong_face', [ref])
        if courtyard[ref][footprint['face']].is_empty:
            add('missing_courtyard', [ref])
        for face in ('F', 'B'):
            body = courtyard[ref][face]
            if body.is_empty:
                continue
            for other in refs[i + 1:]:
                other_body = courtyard[other][face]
                if body.intersects(other_body):
                    overlap = body.intersection(other_body)
                    if overlap.area > 0.00001:
                        kind = ('mechanical_overlap' if
                                ref in MECHANICAL or other in MECHANICAL
                                else 'courtyard_overlap')
                        add(kind, [ref, other], overlap, face=face)
            outside = body.difference(exterior)
            if outside.area > 0.0001:
                add('courtyard_outside_board', [ref], outside, face=face)
            cutout_overlap = body.intersection(cutouts)
            # The turbine footprint intentionally outlines its own cutout.
            if cutout_overlap.area > 0.0001 and ref != 'M3':
                add('board_cutout_overlap', [ref, 'M3'], cutout_overlap, face=face)
            for drill in data['drills']:
                if not drill['npth'] or drill['ref'] == ref:
                    continue
                hole = geom(drill['geometry'], 'drill')
                keepout = hole.buffer(npth_clearance)
                radius = drill.get('mechanical_radius_mm')
                if radius:
                    keepout = keepout.union(hole.centroid.buffer(radius))
                overlap = body.intersection(keepout)
                if overlap.area > 0.00001:
                    add('npth_clearance', [ref, drill['ref']], overlap,
                        face=face, drill_index=drill['index'],
                        clearance_mm=npth_clearance,
                        mechanical_radius_mm=radius)

    # Validate pads independently of courtyard drawings, on both faces.
    pad_outside = []
    for ref in refs:
        for pad in fps[ref]['pads']:
            if pad['attribute'] == 3 or not pad['copper_faces']:
                continue
            outside = geom(pad['geometry'], '%s.%s' % (ref, pad['number'])).difference(board)
            if outside.area > 0.00001:
                pad_outside.append({'reference': ref, 'pad': pad['number'],
                                    'area_mm2': round(outside.area, 6)})
    counts = {}
    for item in issues:
        counts[item['kind']] = counts.get(item['kind'], 0) + 1
    advisory = []
    for envelope in data.get('auxiliary_mechanical_envelopes', []):
        reserved = geom(envelope['geometry'], envelope['source'])
        for ref in refs:
            if ref == envelope['ref']:
                continue
            overlap = courtyard[ref][envelope['face']].intersection(reserved)
            if overlap.area > 0.00001:
                advisory.append({
                    'references': [ref, envelope['ref']],
                    'all_locked': fps[ref]['locked'] and fps[envelope['ref']]['locked'],
                    'overlap_mm2': round(overlap.area, 6),
                    'source': envelope['source'],
                    'accepted_exception': frozenset((ref, envelope['ref'])) in EXCEPTIONS,
                })
    return {
        'npth_clearance_mm': npth_clearance,
        'summary': counts,
        'issues': issues, 'accepted_exceptions': accepted,
        'locked_conflicts': [i for i in issues if i['all_locked']],
        'pads_outside_board': pad_outside,
        'indicative_mechanical_overlaps': advisory,
        'invalid_geometries_repaired_for_analysis': geometry_warnings,
        'limitations': [
            'Exterior courtyard overhangs are reported; connector bodies may intentionally overhang.',
            'No 3D height verification; OLED clearance assumes the existing spacers.',
            'KiCad copper DRC remains necessary; this audit checks placement geometry.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board', type=Path, nargs='?', default=DEFAULT_BOARD)
    parser.add_argument('-o', '--output', type=Path, default=Path('/tmp/usain_geometry.json'))
    parser.add_argument('--analysis-python', type=Path,
                        help='Python with Shapely, when different from pcbnew Python')
    parser.add_argument('--audit-json', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--npth-clearance', type=float, default=0.25)
    args = parser.parse_args()
    if args.audit_json:
        data = json.loads(args.output.read_text())
    else:
        data = export_geometry(args.board)
        args.output.write_text(json.dumps(data, indent=2) + '\n')
    if args.analysis_python and not args.audit_json:
        subprocess.run([str(args.analysis_python), str(Path(__file__).resolve()),
                        '--audit-json', '-o', str(args.output),
                        '--npth-clearance', str(args.npth_clearance)], check=True)
        return
    try:
        data['audit'] = audit_geometry(data, args.npth_clearance)
    except ImportError as error:
        if error.name != 'shapely':
            raise
        print('Geometry exported. Install Shapely or pass --analysis-python to run audit.')
        return
    args.output.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({'output': str(args.output),
                      'footprints': len(data['footprints']),
                      'summary': data['audit']['summary'],
                      'locked_conflicts': len(data['audit']['locked_conflicts']),
                      'accepted_exceptions': len(data['audit']['accepted_exceptions']),
                      'pads_outside_board': len(data['audit']['pads_outside_board'])},
                     indent=2))


if __name__ == '__main__':
    main()
