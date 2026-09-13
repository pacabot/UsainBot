"""Read a COMPLETE KiCad STEP and audit all distinct-reference solid intersections.
FreeCAD Python: audit_step_collisions.py assembly.step pcb_manifest.json output.json
Export with unshifted KiCad origin, models enabled; no fuse-shapes. Include board.
STEP collisions are model-envelope checks, not validation of physical estimates.
"""
import sys,re,json,math
from pathlib import Path
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App, Part, Import
step=Path(sys.argv[1]);manifest=json.loads(Path(sys.argv[2]).read_text());output=Path(sys.argv[3])
Import.open(str(step));doc=App.ActiveDocument
roots=[o for o in doc.Objects if o.TypeId=='App::Part' and not any(p.TypeId=='App::Part' for p in o.InList)]
if len(roots)!=1:raise RuntimeError('Expected one exported assembly root, got '+str([(r.Name,r.Label) for r in roots]))
root=roots[0]
items=[]
for o in root.Group:
 if not hasattr(o,'Shape') or o.Shape.isNull():continue
 s=o.Shape
 if not s.Solids:continue
 v=o.Placement.Base
 # KiCad attaches component instance location as the top-level node placement.
 best=[]
 for f in manifest['footprints']:
  d=math.hypot(v.x-f['xy'][0],v.y+f['xy'][1])
  if d<.05:best.append((f,d))
 if len(best)>1:
  named=[p for p in best if any(Path(m['filename']).stem in o.Label for m in p[0]['models'])]
  if len(named)==1:best=named
  elif all(all(abs(m['offset'][2])<1e-6 for m in p[0]['models']) for p in best):
   side='B.Cu' if v.z<0 else 'F.Cu'
   sided=[p for p in best if p[0]['layer']==side]
   if len(sided)==1:best=sided
 f=best[0][0] if len(best)==1 else None
 ref=f['reference'] if f else ('PCB_BODY' if 'PCB' in o.Label else 'UNMAPPED')
 items.append({'object':o,'shape':s,'ref':ref,'label':o.Label,'locked':f.get('locked') if f else None,'position':[v.x,v.y,v.z]})
def bb_dict(s):
 b=s.BoundBox
 return {k:round(getattr(b,k),6) for k in ['XMin','XMax','YMin','YMax','ZMin','ZMax']}
def lower(a,b):
 a=a.BoundBox;b=b.BoundBox
 return math.sqrt(sum(max(0,getattr(a,k+'Min')-getattr(b,k+'Max'),getattr(b,k+'Min')-getattr(a,k+'Max'))**2 for k in 'XYZ'))
def descriptor(o):return {'reference':o['ref'],'model_label':o['label'],'locked':o['locked'],'position':o['position'],'bbox':bb_dict(o['shape'])}
report={'step':str(step),'board':manifest['board'],'status':'Model-based audit only; ESC dimensions estimated, physical assembly unqualified','model_count':len(items),'footprints_with_models_missing_from_step':[f['reference'] for f in manifest['footprints'] if f['reference'] not in {o['ref'] for o in items}],'unmapped':[descriptor(o) for o in items if o['ref']=='UNMAPPED'],'targets':{}}
# Conservative future-collar reservation: no separate collar exists in current turbine STEP.
reserved=[]
for f in manifest['footprints']:
 if f['reference']=='M3':
  x,y=f['xy']; z=next(o['position'][2] for o in items if o['ref']=='J103')
  c=Part.makeCylinder(23.75,17,App.Vector(x,-y,z)).cut(Part.makeCylinder(18.35,17,App.Vector(x,-y,z)))
  reserved.append({'shape':c,'ref':'M3_FUTURE_COLLAR','label':'UNVALIDATED RESERVED ANNULUS R18.35..23.75 Z0..17','locked':True,'position':[x,-y,z]})
report['reserved_obstacles']=[descriptor(o) for o in reserved]
for targetref in ['J102','J103']:
 targets=[o for o in items if o['ref']==targetref]
 if not targets:raise RuntimeError('Missing target '+targetref+' or cannot map location. '+str([(o['label'],o['position']) for o in items]))
 target=Part.makeCompound([o['shape'] for o in targets]);others=[o for o in items if o['ref']!=targetref]+reserved
 collisions=[];nearest=(float('inf'),None);computed=[]
 for o in sorted(others,key=lambda k:lower(target,k['shape'])):
  lo=lower(target,o['shape']);must=(lo<=1e-6 or o['ref'] in ['M1','M2','M3','J102','J103','J101','C704','C705','U101','Q101','PCB_BODY','M3_FUTURE_COLLAR'])
  if lo<nearest[0] or must:
   distance=target.distToShape(o['shape'])[0]
   volume=target.common(o['shape']).Volume if lo<=1e-6 else 0
   result={**descriptor(o),'distance_mm':round(distance,6),'intersection_mm3':round(volume,8)}
   computed.append(result)
   # PCB contacts/support faces touching are expected; nonzero intersection is not.
   if o['ref'] not in ['PCB_BODY','M3_FUTURE_COLLAR'] and distance<nearest[0]:nearest=(distance,result)
   if volume>1e-5:collisions.append(result)
 report['targets'][targetref]={'models':[descriptor(o) for o in targets],'bbox':bb_dict(target),'nearest_component':nearest[1],'computed_exact_pairs':computed,'collisions':collisions,'bbox_disjoint_pairs_proven_clear':len(others)-len(computed)}
report['all_target_intersections_zero']=all(not x['collisions'] for x in report['targets'].values())
# Full-board pair audit. Same reference can intentionally contain touching assembly parts.
import itertools,time
start=time.monotonic();candidates=0;collisions=[];touches=[]
for a,b in itertools.combinations(items,2):
 if a['ref']==b['ref'] and a['ref']!='UNMAPPED':continue
 if lower(a['shape'],b['shape'])>1e-6:continue
 candidates+=1
 volume=a['shape'].common(b['shape']).Volume
 row={'a':descriptor(a),'b':descriptor(b),'intersection_mm3':round(volume,8)}
 if volume>1e-5:collisions.append(row)
 else:touches.append({'a_ref':a['ref'],'b_ref':b['ref'],'a_model':a['label'],'b_model':b['label']})
 if candidates%40==0:print('Progress',candidates,'AABB candidate pairs;',len(collisions),'positive intersections',flush=True)
report['global_pairs']={'aabb_candidate_pairs_checked':candidates,'positive_intersections':collisions,'aabb_overlaps_without_volume':touches,'elapsed_seconds':round(time.monotonic()-start,2),'note':'Intersections involving board body may be model lead/board-origin artifacts; not automatically component-body collisions. Same-reference internals intentionally excluded.'}
# Bottom sensor proof: distinguish body-to-board from the solder-foot datum.
report['line_sensors']=[]
board_shapes=[o['shape'] for o in items if o['ref']=='PCB_BODY']
if board_shapes:
 board=Part.makeCompound(board_shapes)
 for o in items:
  if re.fullmatch(r'U4(?:0[1-9]|1[0-2])',o['ref']):
   solids=o['shape'].Solids
   body=max(solids,key=lambda s:s.Volume)
   leds=[v for v in items if re.fullmatch(r'D4(?:0[1-9]|1[0-2])',v['ref']) and math.hypot(v['position'][0]-o['position'][0],v['position'][1]-o['position'][1])<.01]
   report['line_sensors'].append({'reference':o['ref'],'model':o['label'],
    'whole_model_bbox':bb_dict(o['shape']),'body_bbox':bb_dict(body),
    'model_solder_origin_z_mm':o['position'][2],
    'body_to_fr4_distance_mm':round(body.distToShape(board)[0],6),
    'whole_model_to_fr4_distance_mm':round(o['shape'].distToShape(board)[0],6),
    'whole_model_fr4_intersection_mm3':round(o['shape'].common(board).Volume,8),
    'paired_top_leds':[{'reference':v['ref'],'distance_mm':round(o['shape'].distToShape(v['shape'])[0],6),'intersection_mm3':round(o['shape'].common(v['shape']).Volume,8)} for v in leds]})
report['mechanical_assembly_pairs']=[]
for ar,br in [('M1','M3'),('M2','M3'),('M1','M2')]:
 aa=Part.makeCompound([o['shape'] for o in items if o['ref']==ar]);bb=Part.makeCompound([o['shape'] for o in items if o['ref']==br])
 report['mechanical_assembly_pairs'].append({'a':ar,'b':br,'distance_mm':aa.distToShape(bb)[0],'intersection_mm3':aa.common(bb).Volume})
output.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
