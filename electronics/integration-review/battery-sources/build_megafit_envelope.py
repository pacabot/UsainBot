# Run with /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd this_file.py
# Mechanical envelope from Molex drawing 2002411000, rev C/C5; no original vendor STEP obtained.
from pathlib import Path
import sys
import FreeCAD as App
import Part,Sketcher,Import
P=Path(__file__).resolve().parents[2]
OUT=P/'kicad-lib'/'3d'
DOCOUT=Path(__file__).parent
sys.path.insert(0,str(P/'kicad-lib'))
from step_colors import injecter_couleurs_step
V=App.Vector
doc=App.newDocument('Molex_2002411133_Envelope')
objects=[]
def block(name,label,x,y,z,dx,dy,dz,color,assumption):
 body=doc.addObject('PartDesign::Body',name);body.Label=label
 body.addProperty('App::PropertyString','DimensionBasis').DimensionBasis=assumption
 sk=doc.addObject('Sketcher::SketchObject',name+'Sketch');body.addObject(sk);sk.Placement.Base=V(x,y,z)
 points=[(0,0),(dx,0),(dx,dy),(0,dy)]
 for a,b in zip(points,points[1:]+points[:1]):sk.addGeometry(Part.LineSegment(V(*a,0),V(*b,0)),False)
 doc.recompute();pad=body.newObject('PartDesign::Pad',name+'Pad');pad.Profile=sk;pad.Length=dz;doc.recompute();sk.Visibility=False
 objects.append((body,color));return body
# KiCad STEP coordinate Y = -footprint Y. Z=0 at main PCB top.
block('Housing','Header envelope: 17.75 x 6.79 x 15.30 mm',-3.18,-3.32,0,17.75,6.79,15.30,(.08,.08,.09),'Molex drawing 2002411000: A=17.75; outer contact offset3.18; base depth6.79; yrear3.32; mating face15.30. Internal cavities omitted.')
block('Latch','Conservative latch envelope (full housing width)',-3.18,3.47,0,17.75,3.81,17.50,(.15,.15,.16),'Molex overall depth10.60 and latch height17.50. Latch width/startZ not dimensioned: deliberately entire body width17.75 and startsZ0; overestimates occupied volume, never used as exact latch CAD.')
# Manufacturer molded numbering, male mating face with latch north: 3,2,1 left-to-right.
for n,x in ((3,0),(2,5.7),(1,11.4)):
 block('Contact%d'%n,'Contact %d - section estimated 1.14 square'%n,x-.57,-.57,-3.23,1.14,1.14,16.5,(.8,.68,.25),'Pin axis/pitch5.70 and PCB tail3.23 documented; square1.14mm and upper tipZ13.27 estimated solely visual. Drill follows maker1.80mm, not this estimated section.')
for n,x in enumerate((2.85,8.55),1):
 body=doc.addObject('PartDesign::Body','Peg%d'%n);body.Label='Retention peg %d - estimated diameter2.90 length2.00'%n
 body.addProperty('App::PropertyString','DimensionBasis').DimensionBasis='Axes from manufacturer PCB layout: x2.85/8.55,yfootprint1.34. Peg diameter2.90,length2.00 estimated; manufacturer hole3.00mm.'
 sk=doc.addObject('Sketcher::SketchObject','PegSketch%d'%n);body.addObject(sk);sk.Placement.Base=V(x,-1.34,-2)
 sk.addGeometry(Part.Circle(V(0,0,0),V(0,0,1),1.45),False);doc.recompute()
 pad=body.newObject('PartDesign::Pad','PegPad%d'%n);pad.Profile=sk;pad.Length=2;doc.recompute();sk.Visibility=False;objects.append((body,(.08,.08,.09)))
for o,c in objects:
 try:o.ViewObject.ShapeColor=c
 except:pass
filename=OUT/'Molex_2002411133_simplified.step'
Import.export([x[0] for x in objects],str(filename));injecter_couleurs_step(str(filename),[x[1] for x in objects])
doc.saveAs(str(DOCOUT/'Molex_2002411133_simplified.FCStd'))
# Separate conservative mated plug envelope for clash review, in same coordinates.
# 30.90 overall mated height documented; lateral registration of 11.30 mated width not fully dimensioned.
# Extend 0.70 on BOTH sides of male10.60 depth -> 12.00 envelope, intentionally conservative.
for o,c in objects:o.Visibility=False
plug=block('MatedPlugEnvelope','MATED PLUG ENVELOPE - 30.90mm total height',-3.18,-4.02,15.30,17.75,12.00,15.60,(.25,.36,.58),'Molex mated height30.90 and width11.30. Exact lateral registration not dimensioned: conservative12.00 depth, extra0.70 on each side of male10.60. Upper wire bend space not included; keep19.1mm free wire before ties.')
filename=OUT/'Molex_2002411133_mated_plug_envelope.step';Import.export([plug],str(filename));injecter_couleurs_step(str(filename),[(.25,.36,.58)])
doc.saveAs(str(DOCOUT/'Molex_2002411133_with_mated_envelope.FCStd'))
print('ENVELOPE MODELS EXPORTED',OUT)
