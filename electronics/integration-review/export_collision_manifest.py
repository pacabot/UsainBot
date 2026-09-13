"""Run with KiCad Python: PCB [output.json]. Read-only board manifest for 3D audit."""
import sys,json
from pathlib import Path
import pcbnew
p=Path(sys.argv[1]).resolve();b=pcbnew.LoadBoard(str(p));out=[]
for f in b.GetFootprints():
 models=[]
 for m in f.Models():
  models.append({'filename':m.m_Filename,'offset':[m.m_Offset.x,m.m_Offset.y,m.m_Offset.z], 'rotation':[m.m_Rotation.x,m.m_Rotation.y,m.m_Rotation.z]})
 if models:
  out.append({'reference':f.GetReference(),'xy':[pcbnew.ToMM(f.GetPosition().x),pcbnew.ToMM(f.GetPosition().y)],'rotation':f.GetOrientationDegrees(),'locked':f.IsLocked(),'layer':f.GetLayerName(),'models':models})
payload={'board':str(p),'footprints':out}
if len(sys.argv)>2:Path(sys.argv[2]).write_text(json.dumps(payload,indent=2))
else:print(json.dumps(payload,indent=2))
