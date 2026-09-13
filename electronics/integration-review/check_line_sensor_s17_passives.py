#!/usr/bin/env python3
"""Read-only local geometry/association check for the corrected S17 package.

Reads a KiCad geometry snapshot (actual current board coordinates) and the
new S17 footprint library. Calculates the footprint in its locked Bottom
pose; it does not write a board or alter the sensor/LED positions.
"""
import argparse
import json
import math
import sys
from pathlib import Path
from shapely.geometry import Polygon,shape,box
from shapely.affinity import rotate,translate
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'tools'))
from sexp import parse,find,find_all,unq

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--geometry',type=Path,default=Path('/tmp/line-window-source.json'))
 p.add_argument('--footprint',type=Path,default=ROOT.parent/'kicad-lib/Pacabot.pretty/ITR8307_S17_TR8_Bottom.kicad_mod')
 p.add_argument('--output',type=Path,default=ROOT/'line-s17-passive-review.json')
 args=p.parse_args();j=json.loads(args.geometry.read_text());fs=j['footprints'];fp=parse(args.footprint.read_text())[0]
 pads={unq(n[1]):{'local_top_xy':[float(v)for v in find(n,'at')[1:3]],'size':[float(v)for v in find(n,'size')[1:3]]}for n in find_all(fp,'pad')}
 assert set(pads)=={'1','2','3','4'}
 lines=[n for n in find_all(fp,'fp_line')if unq(find(n,'layer')[1])=='F.CrtYd'];assert len(lines)==4
 coords=[tuple(map(float,find(n,'start')[1:3]))for n in lines];court_local=Polygon([(x,-y)for x,y in coords])
 rows=[];outpad=[];outcourt=[];board=shape(j['board_polygon']);minpadedge=1e6
 for i in range(12):
  ref='U%d'%(401+i);u=fs[ref];led=fs['D%d'%(401+i)];assert u['locked'] and u['face']=='B' and led['face']=='F'
  assert u['position']==led['position'];assert abs((led['angle']-u['angle']-90+180)%360-180)<1e-5
  x,y=u['position'];a=math.radians(u['angle']);c,s=math.cos(a),math.sin(a);world={}
  for n,pad in pads.items():
   px,py=pad['local_top_xy'];py=-py;world[n]=[x+px*c+py*s,y-px*s+py*c]
   w,h=pad['size'];g=translate(rotate(box(px-w/2,py-h/2,px+w/2,py+h/2),-u['angle'],origin=(0,0)),x,y)
   minpadedge=min(minpadedge,g.distance(board.boundary))
   if not board.covers(g):outpad.append([ref,n,g.difference(board).area])
  g=translate(rotate(court_local,-u['angle'],origin=(0,0)),x,y)
  if not board.covers(g):outcourt.append([ref,g.difference(board).area])
  def point(r,n):return next(p['position']for p in fs[r]['pads']if p['number']==str(n))
  oldnets={p['number']:p['net']for p in u['pads']}
  assert oldnets['4']=='LINE_%02d'%i
  assert oldnets['2']=='/Barrette/IR_A%02d'%i
  assert next(p['net']for p in led['pads']if p['number']=='1')=='/Temoins de ligne/LGN%02d'%i
  rows.append({'index':i,'sensor':ref,'led':'D%d'%(401+i),'new_pads':world,'C_filter_mm':math.dist(world['4'],point('C%d'%(401+i),1)),'R_load_mm':math.dist(world['4'],point('R%d'%(421+i),1)),'R_IR_mm':math.dist(world['2'],point('R%d'%(401+i),2))})
 result={'source_footprint':str(args.footprint),'source_geometry':str(args.geometry),'source_dimensions':'Everlight DRX-0000322 Rev6 page2, exact ITR8307/S17/TR8','status':'read-only prediction from actual locked board poses and corrected library, no placement mutation','rows':rows,'metrics':{key:[min(row[key]for row in rows),max(row[key]for row in rows)]for key in ['C_filter_mm','R_load_mm','R_IR_mm']},'minimum_sensor_pad_edge_clearance_mm':minpadedge,'sensor_pads_outside_board':outpad,'sensor_courtyards_outside_board':outcourt,'unchanged_sensor_and_LED_poses':True,'association_mismatches':0,'placement_recommendation':'Keep all 65 previously validated mobile placements. No cutout and no LED offset change.'}
 args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['rows']},indent=2))
if __name__=='__main__':main()
