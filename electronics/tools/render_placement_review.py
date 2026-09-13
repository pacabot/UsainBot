#!/usr/bin/env python3
"""Review figures from actual KiCad geometry, including selected airwires."""
import json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
from shapely.geometry import shape
ROOT=pathlib.Path(__file__).resolve().parents[1]/'placement-review'
g=json.loads((ROOT/'geometry-after.json').read_text())
def rings(ax,geo,color,alpha=.25):
    if geo.is_empty:return
    if geo.geom_type=='Polygon':
        ax.add_patch(Patch(list(geo.exterior.coords),facecolor=color,edgecolor=color,alpha=alpha,lw=.4))
        for h in geo.interiors:ax.add_patch(Patch(list(h.coords),facecolor='white',edgecolor='#343434',lw=.5))
    else:
        for z in geo.geoms:rings(ax,z,color,alpha)
def point(r,p):return next(v['position'] for v in g['footprints'][r]['pads'] if v['number']==str(p))
for name,bounds,size in [('placement-top',(73,238,118,286),(12,14)),('laser-lateral',(159,204,157,204),(13,13)),('laser-front',(131,170,241,279),(13,13)),('mcu',(128,182,193,239),(14,12)),('power',(91,219,119,179),(18,9))]:
    fig,ax=plt.subplots(figsize=size)
    rings(ax,shape(g['board_polygon']),'#dbe5e9',.5)
    for r,f in g['footprints'].items():
        color='#bc3e3e' if f['locked'] else ('#337fa8' if r.startswith('U') else '#428565')
        for side in ['F','B']:
            geo=shape(f['courtyards'][side]);rings(ax,geo,color,.25 if side=='F' else .08)
        x,y=f['position']
        if bounds[0]<x<bounds[1] and bounds[2]<y<bounds[3]:
            ax.text(x,y,r,fontsize=5 if name=='placement-top' else 7,ha='center',va='center',color='#152126')
        for pad in f['pads']:
            if 'F' in pad['copper_faces']:rings(ax,shape(pad['geometry']),'#ae8521',.7)
    if name.startswith('laser'):
        for b,u in [(500,'U501'),(520,'U502'),(540,'U504')]:
            for r,p,rr,pp in [(f'TM{b+1}',4,u,2),(u,1,f'R{b+4}',2),(u,2,f'R{b+4}',1),(u,1,f'C{b+1}',2),(u,2,f'C{b+1}',1),(u,7,f'R{b+6}',1),(u,6,f'R{b+6}',2)]:
                a=point(r,p);z=point(rr,pp);ax.plot([a[0],z[0]],[a[1],z[1]],color='#983fba',lw=.7,ls='--')
        if (ROOT/'analog-path-preview.json').exists():
            for route in json.loads((ROOT/'analog-path-preview.json').read_text())['paths']:
                pts=route['points_mm'];ax.plot([p[0] for p in pts],[p[1] for p in pts],color='#d87910',lw=1.1)
    ax.set_xlim(bounds[:2]);ax.set_ylim(bounds[3],bounds[2]);ax.set_aspect('equal');ax.set_xlabel('x (mm)');ax.set_ylabel('y (mm)');ax.grid(alpha=.2)
    ax.set_title('Placement Top — rouge : verrouillé ; pointillés : liaisons critiques, sans routage'+('\nOrange : exemple de couloir libre, aucune piste dans le PCB' if name.startswith('laser') else ''))
    fig.tight_layout();fig.savefig(ROOT/(name+'.png'),dpi=170);fig.savefig(ROOT/(name+'.pdf'));plt.close(fig)
