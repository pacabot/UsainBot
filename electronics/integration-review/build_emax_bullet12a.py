"""Reproducible preliminary vertical Bullet 12A assembly.
Run with FreeCAD's Python. All undocumented dimensions are ESTIMATES.
Only new files named EMAX_Bullet_12A_* are written.

Colours: FreeCAD in console mode has no ViewObject, so `step_colors` sews the
AP214 styles on afterwards, recognising each solid by its PRODUCT name — which
is the FreeCAD Label. That only works if the STEP carries one PRODUCT per body:
`Part.export` merges the whole list into a single anonymous product and every
label lookup then misses, so the model reaches KiCad uniformly grey. `Import.export`
keeps the assembly structure and the labels; the count is asserted below.
"""
import sys, json, math
from pathlib import Path
sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App, Import, Part
ROOT=Path(__file__).resolve().parents[1]
MODELS=ROOT/'kicad-lib/3d'; FP=ROOT/'kicad-lib/Pacabot.pretty'
NAME='EMAX_Bullet_12A_Vertical_PROTOTYPE'
DOC=App.newDocument('EMAX_Bullet_12A_Vertical_Prototype')
DOC.Label='EMAX Bullet12A EMX-SC-1873 — PHOTO ESTIMATES / PROTOTYPE'
# Palette relevee sur les photos constructeur et builder de esc-sources/ :
# masque aubergine tres sombre, cuivre etame argente aux pins, pastilles ENIG,
# MOSFETs et ICs noirs, condensateurs beige, berceau imprime blanc casse.
MASQUE_ESC=(0.14,0.05,0.19)
ETAIN=(0.78,0.78,0.80)
ENIG=(0.70,0.59,0.24)
NOIR_BOITIER=(0.13,0.13,0.13)
CERAMIQUE=(0.48,0.40,0.29)
BERCEAU=(0.78,0.78,0.70)
parts=[]
part_colors={}
def annotate(obj, note):
    obj.addProperty('App::PropertyString','DimensionalEvidence','Evidence');obj.DimensionalEvidence=note
    obj.addProperty('App::PropertyString','ManufacturingStatus','Evidence');obj.ManufacturingStatus='PROTOTYPE — MEASURE REAL ESC BEFORE FABRICATION'
def box(name,xyz,size,note,color=NOIR_BOITIER):
    body=DOC.addObject('PartDesign::Body',name)
    feat=body.newObject('PartDesign::AdditiveBox',name+'_Box')
    feat.Length,feat.Width,feat.Height=size
    feat.Placement.Base=App.Vector(*xyz)
    annotate(body,note);annotate(feat,note)
    DOC.recompute()
    if App.GuiUp: body.ViewObject.ShapeColor=color
    part_colors[body.Label]=color
    parts.append(body);return body

def cyl(name,xyz,r,h,note,color=ETAIN):
    body=DOC.addObject('PartDesign::Body',name)
    feat=body.newObject('PartDesign::AdditiveCylinder',name+'_Cylinder')
    feat.Radius=r;feat.Height=h;feat.Placement.Base=App.Vector(*xyz)
    annotate(body,note);annotate(feat,note);DOC.recompute()
    if App.GuiUp: body.ViewObject.ShapeColor=color
    part_colors[body.Label]=color
    parts.append(body);return body
# STEP/KiCad convention: model Y = -footprint Y. Main-board top z=0.
# Exact nominal published footprint dimensions only: x width11, z length15.
box('ESC_PCB_11x15_thickness_EST_1mm',(-5.5,-1.65,2),(11,1,15),
    'EMAX brochure __06: 11x15mm nominal. Thickness1.0mm ESTIMATED, unmeasured. Bottom at2mm is assembly design choice.',MASQUE_ESC)
# Front is capacitor/MOSFET face, y=-0.65. Positive model Y points outwards.
centres=[('GND_POWER',1,-4.30,0,1.2),('SIGNAL',2,0.80,-0.30,0.6),('BATT_PLUS',3,4.42,0,1.2)]
for name,num,x,y,diam in centres:
    cyl('Pin'+str(num)+'_'+name,(x,y,-2.2),diam/2,6.35,
        'DESIGN: solid tinned copper diameter'+str(diam)+'mm; photo-derived x ±0.4mm indicative. Signal Y differs0.30mm due pin radii; all pins tangent to ESC solder face with0.05mm solder gap.')
    width=2.0 if num!=2 else 1.0
    height=1.7 if num!=2 else 1.0
    box('ESC_input_pad'+str(num)+'_'+name,(x-width/2,-0.65,3.1-height/2),(width,0.05,height),
        'PHOTO ESTIMATE: centre x and common longitudinal centre1.1mm from lower input edge. Copper pad outline hidden by solder; approximate size. Not manufacturer land pattern.',ENIG)
# The fourth real pad is the small GND signal-reference pad. It is represented but not strapped in CAD.
box('ESC_small_GND_pad_not_used',(-0.83-0.5,-0.65,2.6),(1,0.05,1),
    'PHOTO ESTIMATE. Small GND pad separate from power GND. Continuity to power GND MUST be physically confirmed before omitting its wire.',ENIG)
# Large component envelopes: locations observed in exact12A photos, heights ESTIMATED.
for i,x in enumerate([-3.6,0,3.6],1):
    box('Front_MOSFET_envelope_'+str(i),(x-1.6,-0.60,12.1),(3.2,0.9,3.0),
        'Approximate placement from exact12A manufacturer and primary builder photographs; package height0.9mm ESTIMATED.',NOIR_BOITIER)
for i,x in enumerate([1.25,2.85,4.45],1):
    box('Front_capacitor_envelope_'+str(i),(x-.65,-0.60,5.1),(1.3,1.8,4.0),
        'Approximate high capacitor positions exact12A photos; protrusion1.8mm ESTIMATED.',CERAMIQUE)
box('Front_regulator_small_parts_envelope',(-4.8,-.60,4.8),(5,1.3,6.5),
    'Simplified component collision envelope. Position/height1.3mm ESTIMATED from exact12A photos.',NOIR_BOITIER)
box('Rear_MCU_and_driver_envelope',(-4.7,-2.65,5.0),(9.4,1.0,10),
    'Simplified rear IC collision envelope. Protrusion1.0mm ESTIMATED. Full detailed component CAD not available.',NOIR_BOITIER)
for i,(x,z) in enumerate([(-4.1,16.4),(0.23,16.3),(4.5,16.15)],4):
    box('Motor_pad_'+str(i),(x-.85,-.65,z-.6),(1.7,.05,1.2),
        'PHOTO ESTIMATE positions/size. z16.40/16.30/16.15 stays within measured+/-0.4mm and board outline. MOTOR_A/B/C are project phase labels from GND side to BATT+ side; no documented EMAX A/B/C order.',ENIG)
# Cradle is our proposed minimal strain-relief accessory, not part of the ESC.
# Main-board adhesive contact and two insulating pegs; no metal near power pads.
box('Cradle_back_rail',(-5.9,-3.1,0),(11.8,1.3,3.9),
    'PROPOSED accessory, dimensions DESIGNED. Nonconductive heat-resistant cradle takes vibration/bending loads; material and retention need physical qualification.',BERCEAU)
box('Cradle_lower_ESC_seat',(-5.35,-1.8,0),(10.7,1.15,2),
    'PROPOSED accessory. Supports lower ESC edge at z2mm. Face solder pads remain accessible.',BERCEAU)
for x,side in [(-7,'L'),(7,'R')]:
    box('Cradle_foot_'+side,(x-.9,-3.1,0),(1.8,2.85,.7),'DESIGNED insulating support foot,2.85mm deep, shortened0.75mm at front for clearance to future turbinecollar reservationR23.75. CAD envelope provisional.',BERCEAU)
    # connection from central rear rail to external foot
    lo=min(x,(-5.9 if x<0 else 5.9))
    box('Cradle_bridge_'+side,(lo,-3.1,0),(1.1,1.3,.7),'DESIGNED bridge; accessory dimension provisional.',BERCEAU)
    cyl('Cradle_alignment_peg_'+side,(x,-1.2,-2.5),.75,2.5,
        'DESIGNED plastic1.5mm locating peg through1.7mm NPTH. Adhesive/stake retention must be validated; not an interference-fit assumption.',BERCEAU)
DOC.recompute()
for obj in parts:
    assert obj.Shape.isValid(),obj.Name
DOC.saveAs(str(MODELS/(NAME+'.FCStd')))
Import.export(parts,str(MODELS/(NAME+'.step')))
sys.path.insert(0,str(ROOT/'kicad-lib'))
from step_colors import injecter_couleurs_step
styles=injecter_couleurs_step(str(MODELS/(NAME+'.step')),part_colors)
assert styles==len(parts),'STEP colours: %d styles for %d bodies'%(styles,len(parts))
summary={'model':NAME,'status':'PROTOTYPE - unpublished dimensions estimated','nominal_pcb_mm':[11,15],'estimated_pcb_thickness_mm':1.0,'esc_bottom_above_main_pcb_mm':2.0,'esc_top_mm':17.0,'coordinate_convention':'STEP y = -footprint y; STEP z=0 is main PCB top; ESC face with capacitors looks towards positive STEP y / negative footprint y.','overall_bbox_mm':{},'pin_mapping':[],'heatshrink':'Removed for direct solder assembly. No heatshrink envelope modelled. Re-fitting heatshrink invalidates present envelope.','cradle':'Proposed electrically insulating accessory. Two locatingpegs plus qualified adhesive/staking required. Not EMAX part.','estimated_envelope_thickness_mm':3.85,'missing_validation':['Real PCB thickness and complete component maxima','Barepad centres, dimensions and tolerances','SmallGND-to-powerGND continuity','Powerpin solder overlap, thermal test12Acontinuous15Aburst','Cradle material, heat/vibration retention','Real motorlead bendradius and routing']}
compound=Part.makeCompound([p.Shape for p in parts]);bb=compound.BoundBox
summary['overall_bbox_mm']={k:getattr(bb,k) for k in ['XMin','XMax','YMin','YMax','ZMin','ZMax']}
for name,num,x,y,d in centres:
    summary['pin_mapping'].append({'pad':num,'function':name,'footprint_xy_mm':[x,-y],'pin_diameter_mm':d,'drill_mm':1.4 if num!=2 else.8,'pad_diameter_mm':3 if num!=2 else 1.6})
summary['cradle_foot_depth_mm']=2.85
summary['cradle_foot_front_shortening_mm']=0.75
summary['solid_count']=len(compound.Solids);summary['all_shapes_valid']=True
(ROOT/'integration-review/esc-dimensions-prototype.json').write_text(json.dumps(summary,indent=2))
# The exported STEP already stands upright; do not rotate90degrees again in KiCad.
lines=['(footprint "EMAX_Bullet_12A_Vertical_3Pin_PROTOTYPE"',' (version 20240108) (generator "pacabot")',' (layer "F.Cu")',' (descr "PROTOTYPE ONLY: exact model EMAX EMX-SC-1873 Bullet12A BLHeli-S. 11x15mm nominal; padcentres photo-derived +/-0.4mm indicative, unpublished outline and1mm thickness estimated. 1=GND POWER,2=SIGNAL,3=+BATT. Pins copper1.2/0.6/1.2mm; two1.7mm NPTH cradle locators. Measure actual ESC before fabrication; no thermal validation. See integration-review/esc-dimensions-prototype.json.")',' (tags "EMAX Bullet12A EMX-SC-1873 vertical PROTOTYPE photo-estimates")',' (attr through_hole)']
def txt(kind,text,x,y,layer,size=.7):
    lines.append(f' (fp_text {kind} "{text}" (at {x} {y}) (layer "{layer}") (effects (font (size {size} {size}) (thickness .12))))')
def rect(x1,y1,x2,y2,layer,width=.1):
    lines.append(f' (fp_rect (start {x1} {y1}) (end {x2} {y2}) (stroke (width {width}) (type solid)) (fill none) (layer "{layer}"))')
def ln(x1,y1,x2,y2,layer='F.SilkS',width=.12):
    lines.append(f' (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {width}) (type solid)) (layer "{layer}"))')
txt('reference','REF**',0,-3.1,'F.SilkS',.75)
txt('value','EMAX_Bullet12A_PROTOTYPE',0,5.1,'F.Fab',.7)
for name,num,x,y,d in centres:
    drill=1.4 if num!=2 else .8; size=3 if num!=2 else 1.6
    shape='rect' if num==1 else'circle'
    lines.append(f' (pad "{num}" thru_hole {shape} (at {x} {-y}) (size {size} {size}) (drill {drill}) (layers "*.Cu" "*.Mask") (remove_unused_layers no) (zone_connect 2))')
    label={1:'GND',2:'SIG',3:'+BAT'}[num]
    txt('user',label,x,-2.15,'F.SilkS',.7)
for x in [-7,7]: lines.append(f' (pad "" np_thru_hole circle (at {x} 1.2) (size 1.7 1.7) (drill 1.7) (layers "*.Cu" "*.Mask"))')
# F.Fab physical plan projection + proposed cradle + drawing annotation of height.
rect(-5.5,.65,5.5,1.65,'F.Fab')
rect(-5.5,-1.2,5.5,2.65,'F.Fab')
rect(-7.9,.25,7.9,3.1,'F.Fab')
txt('user','PCB 11x15; H=17; t=1 EST',0,3.65,'F.Fab',.6)
txt('user','MOTOR A B C UP',0,4.35,'F.Fab',.6)
# Courtyard includes model projection plus solder access; top outputs require3D clearance.
rect(-8.4,-3.6,8.4,4.0,'F.CrtYd',.05)
ln(-5.8,2.95,5.8,2.95);ln(-5.8,2.95,-5.8,2.25);ln(5.8,2.95,5.8,2.25)
txt('user','12A PROTO',0,2.3,'F.SilkS',.7)
# Arrow towards the accessible MOSFET/solder face (negative footprint Y).
ln(-7,-1.35,-7,-2.4);ln(-7,-2.4,-7.35,-2);ln(-7,-2.4,-6.65,-2)
lines.append(f' (model "${{KIPRJMOD}}/kicad-lib/3d/{NAME}.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
lines.append(')')
(FP/'EMAX_Bullet_12A_Vertical_3Pin_PROTOTYPE.kicad_mod').write_text('\n'.join(lines)+'\n')
print(json.dumps(summary,indent=2))
