#!/usr/bin/env python3
"""Read-only placement figure showing the fixed LED-to-sensor geometry."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Patch
from shapely.geometry import shape
ROOT=Path(__file__).resolve().parent
j=json.loads((ROOT/'geometry-final.json').read_text())
fig,ax=plt.subplots(figsize=(18,5.8))
def draw(g,color,alpha=1,edge=None,lw=.5,ls='-'):
 if g.is_empty:return
 if g.geom_type=='Polygon':
  ax.add_patch(Polygon(list(g.exterior.coords),facecolor=color,edgecolor=edge or color,alpha=alpha,lw=lw,ls=ls))
 else:
  for p in g.geoms:draw(p,color,alpha,edge,lw,ls)
draw(shape(j['board_polygon']),'#e9f0e9',1,'#657565',.8)
for ref,f in j['footprints'].items():
 if f['position'][1]<252:continue
 if ref.startswith('U4'):
  draw(shape(f['courtyards']['B']),'none',1,'#bd4f6c',.8,'--')
 elif ref=='TM501':draw(shape(f['courtyards']['F']),'#5c6775',.5)
 elif not ref.startswith('D4'):draw(shape(f['courtyards']['F']),'#99aaa3',.25)
 for p in f['pads']:
  if 'F' in p['copper_faces']:draw(shape(p['geometry']),'#c89e49',.85)
for i in range(12):
 led=j['footprints']['D%d'%(401+i)];sensor=j['footprints']['U%d'%(401+i)]
 x,y=led['position'];a=led['angle']
 draw(shape(led['courtyards']['F']),'#339253',.6,'#0b5326',1)
 ax.plot(x,y,'+',color='#153124',ms=6)
 ax.text(x,y+5.45,'%02d'%i,ha='center',va='center',fontsize=10,color='#173b22',weight='bold')
ax.axvline(155,color='#576777',ls=':',lw=.6)
ax.set_xlim(77,233);ax.set_ylim(286.5,249);ax.set_aspect('equal');ax.set_xlabel('x (mm)');ax.set_ylabel('y (mm)')
ax.set_title('LED Top au droit exact des capteurs Bottom — angle LED = angle capteur + 90°\nLes 12 résistances de LED suivent le même axe radial, 2,80 mm vers l’intérieur',fontsize=12)
ax.legend(handles=[Patch(facecolor='#339253',label='LED Top'),Patch(facecolor='none',edgecolor='#bd4f6c',linestyle='--',label='Courtyard capteur Bottom verrouillé'),Patch(facecolor='#5c6775',label='Réserve laser avant verrouillée')],loc='upper left',fontsize=8)
fig.tight_layout();fig.savefig(ROOT/'line-led-alignment.png',dpi=170);fig.savefig(ROOT/'line-led-alignment.pdf')
