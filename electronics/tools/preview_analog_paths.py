#!/usr/bin/env python3
"""Read-only corridor preview; never writes PCB tracks or vias.

Grid A* around actual Top pads and holes, with a 0.15 mm hypothetical track,
0.20 mm pad gap, 0.25 mm hole gap and 0.5 mm board-edge gap. This is evidence
of an available corridor, not a routed board or signal-integrity validation.
"""
import json,pathlib,math,heapq
import numpy as np
import shapely as S
from shapely.geometry import shape,Point,LineString
ROOT=pathlib.Path(__file__).resolve().parents[1]/'placement-review'
g=json.loads((ROOT/'geometry-after.json').read_text());fp=g['footprints']
STEP=.1;WIDTH=.15
def pad(r,n):return next(p for p in fp[r]['pads'] if p['number']==str(n))
out=[]
for tm,u in [('TM501','U501'),('TM521','U502'),('TM541','U504')]:
    start,end=pad(tm,4),pad(u,2);net=start['net'];assert end['net']==net
    obs=[]
    for f in fp.values():
        for p in f['pads']:
            if 'F' in p['copper_faces'] and p['net']!=net:obs.append(shape(p['geometry']).buffer(.20+WIDTH/2))
    for h in g['drills']:
        if h['pad'] and any(p['number']==h['pad'] and p['net']==net for p in fp[h['ref']]['pads']):continue
        obs.append(shape(h['geometry']).buffer(.25+WIDTH/2))
    obstacles=S.union_all(obs);board=shape(g['board_polygon']).buffer(-.5-WIDTH/2)
    a=np.array(start['position']);b=np.array(end['position']);lo=np.minimum(a,b)-5;hi=np.maximum(a,b)+5
    xs=np.arange(lo[0],hi[0],STEP);ys=np.arange(lo[1],hi[1],STEP);xx,yy=np.meshgrid(xs,ys)
    pts=S.points(np.stack((xx,yy),axis=-1));free=S.covered_by(pts,board)&~S.intersects(pts,obstacles)
    def cell(p):return (int(round((p[1]-lo[1])/STEP)),int(round((p[0]-lo[0])/STEP)))
    origin,dest=cell(a),cell(b);assert free[origin] and free[dest],tm
    heap=[(0,0,origin)];cost={origin:0};prev={};found=False
    while heap:
        _,d,v=heapq.heappop(heap)
        if d>cost[v]+1e-9:continue
        if v==dest:found=True;break
        for dy,dx in [(-1,0),(1,0),(0,1),(0,-1),(-1,-1),(-1,1),(1,-1),(1,1)]:
            w=(v[0]+dy,v[1]+dx)
            if not (0<=w[0]<len(ys) and 0<=w[1]<len(xs)) or not free[w]:continue
            if dx and dy and (not free[v[0]+dy,v[1]] or not free[v[0],v[1]+dx]):continue
            nd=d+math.hypot(dx,dy)*STEP
            if nd<cost.get(w,1e99):
                cost[w]=nd;prev[w]=v;heapq.heappush(heap,(nd+math.dist(w,dest)*STEP,nd,w))
    assert found,tm+' no Top corridor'
    cells=[dest]
    while cells[-1]!=origin:cells.append(prev[cells[-1]])
    raw=[a.tolist()]+[[float(xs[v[1]]),float(ys[v[0]])] for v in reversed(cells)]+[b.tolist()]
    # Greedy visibility simplification, checked against exact polygons.
    route=[raw[0]];i=0
    while i<len(raw)-1:
        j=len(raw)-1
        while j>i+1 and (LineString([raw[i],raw[j]]).intersects(obstacles) or not board.covers(LineString([raw[i],raw[j]]))):j-=1
        route.append(raw[j]);i=j
    length=sum(math.dist(x,y) for x,y in zip(route,route[1:]))
    out.append({'station':tm,'amplifier':u,'net':net,'length_mm':round(length,3),'points_mm':route,'track_width_mm':WIDTH,'pad_clearance_mm':.20,'hole_clearance_mm':.25,'board_edge_clearance_mm':.5})
(ROOT/'analog-path-preview.json').write_text(json.dumps({'read_only':True,'tracks_added':0,'paths':out},indent=2)+'\n')
print([(p['station'],p['length_mm']) for p in out])
