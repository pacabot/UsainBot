"""Normalize existing MR30PB STEP; create footprint from AMASS 2021V1 layout.
Source geometry is archived, never silently scaled. FreeCAD Python.
"""
from pathlib import Path
import sys,json
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App, Part, Import
HERE=Path(__file__).parent;ROOT=HERE.parent
src=Part.Shape();src.read(str(HERE/'sources/mr30pb-m.step'))
src.rotate(App.Vector(),App.Vector(1,0,0),-90);src.translate(App.Vector(0,5.85,-.75))
assert src.isValid()
assert abs(src.BoundBox.ZMin+3)<.001 and abs(src.BoundBox.ZMax-10.4)<.001
name='AMASS_MR30PB_M_Vertical'
# Couleurs du MR30PB-M30.G.Y : corps nylon jaune, contacts dores. Memes teintes
# que le XT30U-M du projet (gen_3d_models.py), c est le meme fabricant.
JAUNE=(.95,.78,.10);LAITON=(.83,.68,.21)
# Le STEP Lucidar est UN seul solide : plastique et contacts y sont fusionnes,
# donc incolorables separement tels quels. Les contacts sont isoles par
# geometrie, sur les seules zones ou ils sont seuls dans le rayon decoupe :
# sous le PCB les queues r0.8 de z-3 a z0, et au-dessus du plancher de cavite
# (z3.4) l epaulement r1.25 puis la balle r0.95. La paroi plastique la plus
# proche est le fut r1.75, d ou un outil r1.30 qui ne mord jamais dedans.
# Le troncon noye de z0 a z3.4 reste dans le corps : invisible, et le laisser
# la garde le corps en un solide unique.
outil=Part.makeCompound([c for x in (-3.5,0,3.5) for c in
 (Part.makeCylinder(1.3,3.05,App.Vector(x,0,-3.05)),
  Part.makeCylinder(1.3,7.1,App.Vector(x,0,3.4)))])
contacts=src.common(outil);corps=src.cut(outil)
assert len(contacts.Solids)==6 and len(corps.Solids)==1
# La decoupe ne doit rien ajouter ni retrancher : meme volume, meme enveloppe.
assert abs(corps.Volume+contacts.Volume-src.Volume)<1e-4*src.Volume
reunion=Part.makeCompound([corps,contacts]).BoundBox
for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax'):
 assert abs(getattr(reunion,k)-getattr(src.BoundBox,k))<1e-6,k
doc0=App.newDocument('MR30PB_M')
pieces=[]
for label,forme in [('Corps',corps),('Contacts',contacts)]:
 o=doc0.addObject('Part::Feature',label);o.Shape=forme;o.Label=label;pieces.append(o)
doc0.recompute()
Import.export(pieces,str(ROOT/'kicad-lib/3d'/(name+'.step')))
sys.path.insert(0,str(ROOT/'kicad-lib'))
from step_colors import injecter_couleurs_step
styles=injecter_couleurs_step(str(ROOT/'kicad-lib/3d'/(name+'.step')),
 {'Corps':JAUNE,'Contacts':LAITON})
assert styles==7,'STEP couleurs : %d styles pour 7 solides'%styles
# Conservative plugged assembly envelope. Includes the complete female+cover
# on top of the header with ZERO assumed insertion overlap. This bounds the
# unknown mated seating depth without presenting a false exact assembly pose.
doc=App.newDocument('MR30_Mating_Clearance')
b=doc.addObject('PartDesign::Body','MatedClearance');p=b.newObject('PartDesign::AdditiveBox','Envelope')
p.Length=12.6;p.Width=5.7;p.Height=14.5;p.Placement.Base=App.Vector(-6.3,-2.85,10.4)
b.addProperty('App::PropertyString','Basis').Basis='Female STEP overall12.465x5.515x14.5 incl cover; conservative full depth above header without insertion overlap. Bounding volume, not physical seated connector. Actual height <=24.9mm subject source revision.'
doc.recompute();b.Shape.exportStep(str(ROOT/'kicad-lib/3d/AMASS_MR30_Mated_Clearance.step'))
doc.saveAs(str(HERE/'MR30_Mating_Clearance.FCStd'))
# Header geometry and repeated tail sections in the model coordinate system.
bb=src.BoundBox
proof={'source':'sources/mr30pb-m.step; Lucidar mirror, CAD origin not certified manufacturer',
 'transform':'Rx=-90deg then translate(0,+5.85,-0.75)mm',
 'header_bbox':{k:getattr(bb,k) for k in ['XMin','XMax','YMin','YMax','ZMin','ZMax']},
 'manufacturer_body_mm':[11.9,5.3,10.4],'cad_flange_width_mm':12.3,
 'pad_numbering':'Project convention: Top board 1 GND at x+3.5 /2 MID x0 /3 VPACK x-3.5. Marked explicitly; not a universal battery pinout.',
 'tails':[],'mated_clearance_mm':[12.6,5.7,24.9]}
for x in [-3.5,0,3.5]:
 tail=src.common(Part.makeCylinder(.9,2.5,App.Vector(x,0,-2.8)))
 assert tail.Volume>0
 proof['tails'].append({'xy':[x,0],'metal_volume_within_hole_mm3':tail.Volume,'nominal_drill_mm':1.8})
(HERE/'model-dimensions.json').write_text(json.dumps(proof,indent=2))
fpname='AMASS_MR30PB-M_1x03_P3.50mm_Vertical'
lines=[f'(footprint "{fpname}" (version 20240108) (generator "pcbnew") (layer "F.Cu")',
 '(descr "AMASS MR30PB-M, vertical, 3mm tails. AMASS 2021V1 drawing: body11.9x5.3 h10.4; holes1.80+0.20/0, pitch3.50. Project pins Top left3=VPACK/mid2=MID/right1=GND. See mr30-review/README.md.")',
 '(tags "AMASS MR30PB MR30 battery 3 contacts 20A AWG16") (attr through_hole)',
 '(fp_text reference "REF**" (at 0 -4.6) (layer "F.SilkS") (effects (font (size 1 1) (thickness .15))))',
 '(fp_text value "MR30PB-M" (at 0 4.6) (layer "F.Fab") (effects (font (size 1 1) (thickness .15))))']
def rect(x,y,layer,width):
 for a,b in [((-x,-y),(x,-y)),((x,-y),(x,y)),((x,y),(-x,y)),((-x,y),(-x,-y))]:
  lines.append(f'(fp_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width {width}) (type solid)) (layer "{layer}"))')
rect(6.15,2.65,'F.Fab',.1);rect(6.3,2.8,'F.SilkS',.12);rect(6.8,3.5,'F.CrtYd',.05)
for n,x,net in [(3,-3.5,'+'),(2,0,'MID'),(1,3.5,'GND')]:
 size=3 if n!=2 else 2.5
 shape='rect' if n==1 else 'circle'
 lines.append(f'(pad "{n}" thru_hole {shape} (at {x} 0) (size {size} {size}) (drill 1.8) (layers "*.Cu" "*.Mask") (zone_connect 2))')
 lines.append(f'(fp_text user "{n}:{net}" (at {x} -3.4) (layer "F.SilkS") (effects (font (size .8 .8) (thickness .11))))')
lines.append('(fp_text user "PACK 2S" (at 0 3.4) (layer "F.SilkS") (effects (font (size .8 .8) (thickness .11))))')
lines.append(f'(model "${{KIPRJMOD}}/kicad-lib/3d/{name}.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
lines.append(')')
(ROOT/'kicad-lib/Pacabot.pretty'/(fpname+'.kicad_mod')).write_text('\n'.join(lines)+'\n')
print('MR30 footprint/model generated',proof,flush=True)
