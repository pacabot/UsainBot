#!/usr/bin/env python3
"""Apply reviewed positions/netlist with KiCad Python; preserve locked geometry.

The authoritative input is the current PCB, never the old layout generator.
All existing footprint UUIDs survive. No traces, vias, zones or outlines are
created or removed. The baseline is checked before and after saving.
"""
import json, pathlib, xml.etree.ElementTree as ET
import pcbnew

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'placement-review'
before=json.loads((OUT/'before.json').read_text())
positions=json.loads((OUT/'placement.json').read_text())
netfile=OUT/'final-netlist.xml'
root=ET.parse(netfile).getroot()
board=pcbnew.LoadBoard(str(ROOT/'UsainBot.kicad_pcb'))
fps={f.GetReference():f for f in board.GetFootprints()}
assert not list(board.GetTracks()), 'Unexpected routing: stop for review'
assert not list(board.Zones()), 'Unexpected copper zones: stop for review'
def xy(f):return [pcbnew.ToMM(f.GetPosition().x),pcbnew.ToMM(f.GetPosition().y)]
for r,d in before.items():
    f=fps[r]
    assert f.m_Uuid.AsString()==d['uuid'],r+' UUID changed'
    if d['locked']:
        assert xy(f)==d['xy'],r+' locked position changed'
        if r!='U201':assert abs(f.GetOrientationDegrees()-d['angle'])<1e-6,r
        assert f.GetLayerName()==d['side'] and f.IsLocked(),r

components={c.attrib['ref']:c for c in root.find('components')}
for r,c in components.items():
    fpid=c.findtext('footprint');nick,item=fpid.split(':',1)
    if r not in fps:
        library=ROOT/'kicad-lib'/f'{nick}.pretty' if nick=='Pacabot' else pathlib.Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')/f'{nick}.pretty'
        f=pcbnew.FootprintLoad(str(library),item)
        assert f,r
        board.Add(f);f.SetReference(r);f.SetValue(c.findtext('value'));fps[r]=f
        f.SetPath(pcbnew.KIID_PATH(c.find('sheetpath').get('tstamps')+c.findtext('tstamps').split()[0]))
    f=fps[r]
    f.SetFPID(pcbnew.LIB_ID(nick,item))
    f.SetValue(c.findtext('value'))
    properties={p.get('name') for p in c.findall('property')}
    f.SetDNP('dnp' in properties)
    if r=='J201':f.SetExcludedFromBOM(False)
    # Preserve footprint geometry and custom models; fill the metadata that
    # the old board generator omitted, allowing meaningful schematic parity.
    for field in c.findall('fields/field'):
        name=field.get('name')
        if name in ('Footprint','Reference','Value','Description'):continue
        value=field.text or ''
        f.SetField(name,value)
        nf=f.GetField(name)
        nf.SetVisible(False);nf.SetLayer(pcbnew.B_Fab if f.IsFlipped() else pcbnew.F_Fab)
        nf.SetMirrored(f.IsFlipped());nf.SetPosition(f.GetPosition())

nets={n.GetNetname():n for n in board.GetNetsByNetcode().values()}
for r in ('M1','M2','M3'):
    # These are deliberately mechanical footprints without schematic symbols.
    fps[r].SetBoardOnly(True)
for n in root.find('nets'):
    name=n.get('name')
    if name not in nets:
        ni=pcbnew.NETINFO_ITEM(board,name);board.Add(ni);nets[name]=ni
    for node in n.findall('node'):
        f=fps[node.get('ref')]
        for pad in f.Pads():
            if pad.GetNumber()==node.get('pin'):pad.SetNet(nets[name])

for r,(x,y,angle,side) in positions.items():
    f=fps[r];target=pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
    if before.get(r,{}).get('locked'):
        if r=='U201':f.SetOrientationDegrees(angle)
        continue
    if f.IsFlipped()!=(side=='B'):f.Flip(f.GetPosition(),False)
    f.SetOrientationDegrees(angle);f.SetPosition(target)
    # Values remain available on Fab; references are retained for visual
    # placement review and will be assessed separately from copper clearance.
    f.Value().SetVisible(False)
    ref=f.Reference()
    ref.SetLayer(pcbnew.F_Fab if side=='F' else pcbnew.B_Fab)
    ref.SetPosition(target);ref.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(.8),pcbnew.FromMM(.8)))
    ref.SetTextThickness(pcbnew.FromMM(.12));ref.SetTextAngle(pcbnew.EDA_ANGLE(0,pcbnew.DEGREES_T));ref.SetMirrored(side=='B')
    for drawing in f.GraphicalItems():
        if isinstance(drawing,pcbnew.PCB_TEXT) and drawing.GetText()=='${REFERENCE}':drawing.SetVisible(False)

pcbnew.SaveBoard(str(ROOT/'UsainBot.kicad_pcb'),board)
check=pcbnew.LoadBoard(str(ROOT/'UsainBot.kicad_pcb'))
for f in check.GetFootprints():
    r=f.GetReference()
    if r not in before:continue
    d=before[r]
    assert f.m_Uuid.AsString()==d['uuid'],r
    if d['locked']:
        assert xy(f)==d['xy'] and f.IsLocked() and f.GetLayerName()==d['side'],r
        if r!='U201':assert abs(f.GetOrientationDegrees()-d['angle'])<1e-6,r
assert not list(check.GetTracks()) and not list(check.Zones())
print('Applied',len(positions),'footprints; all original locks/UUIDs preserved; no routing.')
