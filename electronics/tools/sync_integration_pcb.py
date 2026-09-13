#!/usr/bin/env python3
"""Apply the exported, reviewed schematic netlist to the current KiCad PCB.

Only obsolete battery/ESC interfaces may be removed or replaced. Original
UUIDs, locks and positions remain for all other locked footprints. No routing.
Run using KiCad's bundled Python after exporting after-netlist.xml.
"""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
SHARE = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
# KiCad 10 macOS SWIG: immediately destroying a removed FOOTPRINT wrapper
# invalidates type wrappers used by other board objects. Retain it until exit.
REMOVED_WRAPPERS = []
SENSOR_CORRECTIONS = {'U%d' % i for i in range(401, 413)}

def state(f):
    return (f.m_Uuid.AsString(), f.GetPosition().x, f.GetPosition().y,
            f.GetOrientationDegrees(), f.IsFlipped(), f.IsLocked())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--positions', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    board = pcbnew.LoadBoard(str(ROOT / 'UsainBot.kicad_pcb'))
    assert not list(board.GetTracks()) and not list(board.Zones())
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    before = {r: state(f) for r, f in fps.items()}
    positions = json.loads(args.positions.read_text())
    positions = positions.get('placements', positions)
    tree = ET.parse(ROOT / 'integration-review/after-netlist.xml').getroot()
    components = {c.get('ref'): c for c in tree.find('components')
                  if not any(p.get('name') == 'exclude_from_board' for p in c.findall('property'))}
    for ref in ('J104', 'J702'):
        assert ref not in components
        if ref in fps:
            removed = fps.pop(ref)
            REMOVED_WRAPPERS.append(removed)
            board.Remove(removed)
    replacements = []
    for ref, comp in components.items():
        fp_id = comp.findtext('footprint')
        if not fp_id:
            raise ValueError('Missing footprint: ' + ref)
        nick, item = fp_id.split(':', 1)
        old = fps.get(ref)
        if old is None or old.GetFPIDAsString() != fp_id:
            assert ref in {'J102', 'J103'} | SENSOR_CORRECTIONS, 'Unexpected replacement: ' + ref
            lib = ROOT / 'kicad-lib' / (nick + '.pretty') if nick == 'Pacabot' else SHARE / (nick + '.pretty')
            f = pcbnew.FootprintLoad(str(lib), item)
            assert f
            board.Add(f)  # Flip() requires a parent board in KiCad 10.
            if old:
                if old.IsFlipped():
                    f.Flip(f.GetPosition(), False)
                f.SetPosition(old.GetPosition())
                f.SetOrientationDegrees(old.GetOrientationDegrees())
                f.Reference().SetLayer(old.Reference().GetLayer())
                f.Reference().SetPosition(old.Reference().GetPosition())
                f.Reference().SetTextAngle(old.Reference().GetTextAngle())
                f.Reference().SetTextSize(old.Reference().GetTextSize())
                f.Value().SetVisible(old.Value().IsVisible())
                REMOVED_WRAPPERS.append(old)
                board.Remove(old)
            f.SetReference(ref)
            f.SetLocked(before[ref][-1] if ref in SENSOR_CORRECTIONS else False)
            fps[ref] = f
            replacements.append(ref)
        f = fps[ref]
        f.SetFPID(pcbnew.LIB_ID(nick, item))
        f.SetPath(pcbnew.KIID_PATH(comp.find('sheetpath').get('tstamps') + comp.findtext('tstamps').split()[0]))
        f.SetValue(comp.findtext('value'))
        props = {p.get('name') for p in comp.findall('property')}
        f.SetDNP('dnp' in props)
        f.SetExcludedFromBOM('exclude_from_bom' in props)
        for field in comp.findall('fields/field'):
            name = field.get('name')
            if name in ('Footprint', 'Reference', 'Value', 'Description'):
                continue
            try:
                f.SetField(name, field.text or '')
            except Exception:
                print('Field update failed:', ref, name, type(f), flush=True)
                raise
            fld = f.GetField(name)
            fld.SetVisible(False)
            fld.SetLayer(pcbnew.B_Fab if f.IsFlipped() else pcbnew.F_Fab)
            fld.SetMirrored(f.IsFlipped())
            fld.SetPosition(f.GetPosition())

    nets = {n.GetNetname(): n for n in board.GetNetsByNetcode().values()}
    assigned = {}
    for net in tree.find('nets'):
        name = net.get('name')
        nodes = [n for n in net.findall('node') if n.get('ref') in components]
        if not nodes:
            continue  # Motor phases exist only on the external module/wires.
        if name not in nets:
            ni = pcbnew.NETINFO_ITEM(board, name)
            board.Add(ni)
            nets[name] = ni
        for node in nodes:
            ref, number = node.get('ref'), node.get('pin')
            pads = [p for p in fps[ref].Pads() if p.GetNumber() == number]
            assert pads, 'Schematic pin has no physical PCB pad: ' + ref + '.' + number
            for pad in pads:
                pad.SetNet(nets[name])
            assigned[(ref, number)] = name

    for ref, position in positions.items():
        f = fps[ref]
        assert not f.IsLocked(), 'Cannot move locked ' + ref
        if isinstance(position, dict):
            x, y = position['position']
            angle = position['angle']
        else:
            x, y, angle = position[:3]
        assert not f.IsFlipped()
        f.SetPosition(pcbnew.VECTOR2I(round(x * 1e6), round(y * 1e6)))
        f.SetOrientationDegrees(angle)
        f.Reference().SetLayer(pcbnew.F_Fab)
        f.Reference().SetPosition(f.GetPosition())
        f.Reference().SetTextAngle(pcbnew.EDA_ANGLE(0, pcbnew.DEGREES_T))
        f.Value().SetVisible(False)
    assert all(r in positions or r in SENSOR_CORRECTIONS for r in replacements)
    for ref, original in before.items():
        if ref in ('J102', 'J103', 'J104', 'J702'):
            continue
        f = fps[ref]
        if ref not in replacements:
            assert f.m_Uuid.AsString() == original[0]
        if original[-1]:
            assert state(f)[1:] == original[1:], 'Locked placement changed: ' + ref
    for ref, f in fps.items():
        for pad in f.Pads():
            if ref in components and pad.GetNumber():
                assert (ref, pad.GetNumber()) in assigned or not pad.GetNetname(), ref
    pcbnew.SaveBoard(str(args.output), board)
    # m_Uuid is read-only in this Python build. Preserve the replaced assembly
    # identities in the serialized board and then have KiCad load it again.
    serialized = args.output.read_text()
    for ref in replacements:
        serialized = serialized.replace('"' + fps[ref].m_Uuid.AsString() + '"',
                                        '"' + before[ref][0] + '"')
    args.output.write_text(serialized)
    check = pcbnew.LoadBoard(str(args.output))
    assert len(list(check.GetFootprints())) == len(components) + 3
    assert not list(check.GetTracks()) and not list(check.Zones())
    print('Updated from schematic XML: %d board components; %d footprints replaced; %d positions.' %
          (len(components), len(replacements), len(positions)))
    print('All remaining locked positions/UUIDs intact; no routing.')

if __name__ == '__main__':
    main()
