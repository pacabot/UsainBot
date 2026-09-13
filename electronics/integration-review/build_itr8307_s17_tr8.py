"""Exact chosen BOM variant ITR8307/S17/TR8, simplified mechanical model.
FreeCAD PartDesign, source Everlight DRX-0000322 Rev6 p2.
Coordinate convention: TOP footprint, model Y=-footprint Y, solder datum Z=0.
No artificial model offset; footprints mounted on B.Cu are flipped by KiCad.
Only creates new explicitly S17-named files, never replaces plain ITR8307.
"""
import sys,json,math
from pathlib import Path
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App, Part, Sketcher
ROOT=Path(__file__).resolve().parents[1]
NAME='Everlight_ITR8307_S17_TR8'
DOC=App.newDocument(NAME)
DOC.Label='Everlight ITR8307/S17/TR8 — nominal datasheet envelope'
parts=[];colors={}
def evidence(obj,text):
    obj.addProperty('App::PropertyString','DimensionalEvidence','Evidence')
    obj.DimensionalEvidence=text

def box(name,xyz,size,note,color):
    b=DOC.addObject('PartDesign::Body',name)
    p=b.newObject('PartDesign::AdditiveBox',name+'_Box')
    p.Length,p.Width,p.Height=size;p.Placement.Base=App.Vector(*xyz)
    evidence(b,note);evidence(p,note);DOC.recompute()
    parts.append(b);colors[b.Label]=color
    return b
# Datasheet nominal body 3.4 x 2.7 x 1.5; underside is .12 above solder plane.
# .12 +/-.05 is the documented body underside-to-foot datum separation.
body=box('S17_PackageBody_3p4x2p7x1p5',(-1.7,-1.35,.12),(3.4,2.7,1.5),
 'Everlight DRX-0000322 Rev6 p2: body3.4+/-0.2 x2.7+/-0.2 x1.5+0.2/-0 mm. Body underside .12+/-0.05 above foot solder plane. Nominal envelope model, not maximum-tolerance envelope.',(.055,.055,.06))
# Foot centre1.8 spacing, .5 width; total lead span4.6; toe length.38.
# Root lead datum .65 from body underside per side view. Bends are polygonal,
# conservatively inside the nominal lead envelope; undocumented profile simplified.
# The detailed bend radii R.10/.25/.35 are NOT reproduced; no pad/bend is moved
# to match the old incompatible footprint. The distal flat foot is exactly .38.
rootz=.12+.65
profile=[(1.25,rootz-.06),(1.51,rootz-.06),(1.92,.12),(1.92,0),
         (2.30,0),(2.30,.12),(1.99,.12),(1.58,rootz+.06),(1.25,rootz+.06)]
# Index: pad1 cathode at footprint(-.9,+2.11); model coordinates flip y.
pins=[(1,'CATHODE',-.9,-1),(2,'ANODE',-.9,1),
      (3,'COLLECTOR',.9,-1),(4,'EMITTER',.9,1)]
for n,function,x,side in pins:
    b=DOC.addObject('PartDesign::Body',f'Pin{n}_{function}')
    sk=b.newObject('Sketcher::SketchObject',f'Pin{n}_YZ_Profile')
    # Sketch local x,y -> world y,z; sketch normal -> world+x.
    sk.Placement=App.Placement(App.Vector(x-.25,0,0),App.Rotation(App.Vector(1,1,1),120))
    pts=[App.Vector(side*y,z,0) for y,z in profile]
    if side<0:pts.reverse()
    for a,c in zip(pts,pts[1:]+pts[:1]): sk.addGeometry(Part.LineSegment(a,c),False)
    pad=b.newObject('PartDesign::Pad',f'Pin{n}_LeadWidth_0p5')
    pad.Profile=sk;pad.Length=.5;DOC.recompute()
    evidence(b,'Everlight Rev6 nominal: leadwidth.5, totalspan4.6, distaltoe.38, rowpitch1.8; .65 leadroot datum. Metal nominalthickness.12 inferred from documented .12 foot/body datum; exact bend profile/radii are simplified and not a manufacturing tool model.')
    evidence(sk,'Bend profile approximation within nominal envelope. Does not reproduce stamped lead radii R.10/.25/.35 or +/-3 degree toe coplanarity tolerance.')
    parts.append(b);colors[b.Label]=(.62,.64,.66)
# Flush optical windows are visual identification only; outlines are not critical
# dimensions and are explicitly estimated inside the documented package envelope.
for x,n,col in [(-.9,'IR_LED',(.20,.045,.035)),(.9,'Phototransistor',(.045,.05,.065))]:
    box(n+'_VisualWindow_EST',(x-.55,-1.01,1.618),(1.1,1.85,.002),
        'Visual-only simplified optical window. Position and window outline estimated from manufacturer package illustration; all inside exact nominal body envelope.',col)
DOC.recompute()
for o in parts:
    assert o.Shape.isValid(),o.Name
    assert len(o.Shape.Solids)==1,(o.Name,len(o.Shape.Solids))
DOC.saveAs(str(ROOT/'kicad-lib/3d'/f'{NAME}.FCStd'))
Part.export(parts,str(ROOT/'kicad-lib/3d'/f'{NAME}.step'))
sys.path.insert(0,str(ROOT/'kicad-lib'))
from step_colors import injecter_couleurs_step
injecter_couleurs_step(str(ROOT/'kicad-lib/3d'/f'{NAME}.step'),colors)
compound=Part.makeCompound([o.Shape for o in parts]);bb=compound.BoundBox
flatfeet=[]
for n,fn,x,s in pins:
    # Inspect exactly the distal flat .38mm toe at solder plane.
    ymin,ymax=(1.92,2.3) if s>0 else(-2.3,-1.92)
    sh=next(o.Shape for o in parts if o.Name==f'Pin{n}_{fn}')
    section=sh.common(Part.makeBox(1,abs(ymax-ymin)-.0002,.0001,App.Vector(x-.5,ymin+.0001,0)))
    flatfeet.append({'pin':n,'function':fn,'model_xyz_mm':[x,s*2.11,0],
       'footprint_xy_mm':[x,-s*2.11],'distal_flat_toe_mm':[.5,.38],
       'solder_plane_intersection_area_mm2':round(section.Volume/.0001,6)})
summary={'reference':'ITR8307/S17/TR8(B), LCSC C81632, existing project BOM',
 'source':'https://www.everlighteurope.com/custom/files/datasheets/DRX-0000322.pdf',
 'datasheet':'DRX-0000322 Rev6, package dimensions p2',
 'model_name':NAME,'model_status':'Nominal manufacturer package dimensions; detailed bends and opticalwindows simplified, not supplier CAD',
 'manufacturer_step_available':False,'units':'mm',
 'body_nominal':[3.4,2.7,1.5],'body_dimensions_tolerance':['+/-0.2','+/-0.2','+0.2/-0'],
 'overall_nominal':[3.4,4.6,1.62],'overall_span_tolerance':.2,
 'body_bottom_to_solder_plane':.12,'body_bottom_to_solder_plane_tolerance':.05,
 'maximum_height_from_solder_plane':1.87,
 'coordinate_convention':'Model Y=-footprintY; Z=0 solder plane; Top default, KiCad flip for Bottom',
 'bbox':{k:getattr(bb,k) for k in ['XMin','XMax','YMin','YMax','ZMin','ZMax']},
 'pins':flatfeet,'solid_count':len(compound.Solids),'all_shapes_valid':True,
 'cutout_required':False,
 'incompatible_previous_model':'Plain Everlight_ITR8307.step spans6.7mm, bodyZ-.4..1.0; required footprint cutout was removed. It is NOT the chosen formed-lead S17/TR8 variant.',
 'simplifications':['Body corner chamfer beside pin2 is omitted: conservative rectangular package envelope; electrical pin numbers remain explicit in solid names.','Lead bend shape polygonal; specified corner radii not reproduced. Physical toe width, toe length, overallspan and solderdatum retained.','Metal nominalthickness .12 from shown foot/body datum; cross-section should not be used to produce leadforming tooling.','Optical window outlines visual estimates within body envelope.','Nominal CAD; tolerance envelope must be allowed separately.']}
(ROOT/'integration-review/sensor-sources/s17-mechanical-model.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
