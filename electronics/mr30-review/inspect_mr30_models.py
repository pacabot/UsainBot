import sys,json
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App,Part
from pathlib import Path
H=Path(__file__).parent
m=Part.Shape();m.read(str(H/'sources/mr30pb-m.step'));m.rotate(App.Vector(),App.Vector(1,0,0),-90);m.translate(App.Vector(0,5.85,-.75))
f=Part.Shape();f.read(str(H/'sources/mr30-f.step'))
# Map source y into +Z, z into -Y, source contact z=1.25 -> newY0.
f.rotate(App.Vector(),App.Vector(1,0,0),90);f.translate(App.Vector(0,1.25,0))
for angle in [0,180]:
 g=f.copy();g.rotate(App.Vector(),App.Vector(0,0,1),angle)
 for off in [10.4,10.75,11,11.4,12,12.4,13,14,15,16,17,18]:
  k=g.copy();k.translate(App.Vector(0,0,off))
  print(angle,off,'intersect',round(m.common(k).Volume,5),'distance',round(m.distToShape(k)[0],5),flush=True)
m.exportStep(str(H/'male-aligned.step'))
print('male',m.BoundBox)
# XY sections expose polarity/key orientation and PCB tail axes.
for z in [-1,1,5,9]:
 section=m.section(Part.makePlane(30,20,App.Vector(-15,-10,z)))
 print('section',z,[(round(e.Length,3),str(e.BoundBox)) for e in section.Edges][:35])
