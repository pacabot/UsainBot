#!/usr/bin/env python3
"""Read-only figure from the final board's actual courtyard polygons."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Patch,Circle
from shapely.geometry import shape
ROOT=Path(__file__).resolve().parent
j=json.loads((ROOT/'geometry-final.json').read_text());p=json.loads((ROOT/'rear-integration-positions.json').read_text());fig,ax=plt.subplots(figsize=(15,8))
def draw(g,color,alpha=1,edge=None,lw=.5):
 if g.is_empty:return
 if g.geom_type=='Polygon':ax.add_patch(Polygon(list(g.exterior.coords),facecolor=color,edgecolor=edge or color,alpha=alpha,lw=lw))
 else:
  for q in g.geoms:draw(q,color,alpha,edge,lw)
draw(shape(j['board_polygon']),'#edf2ed',1,'#496449',.6)
for ref,f in j['footprints'].items():
 x,y=f['position']
 if not(90<x<220 and y<162):continue
 color=('#476fa7' if ref in p['placements'] else '#e4a1a1' if f['locked'] else '#bbc7bd')
 draw(shape(f['courtyards']['F']),color,.45)
 for pad in f['pads']:
  if 'F' in pad['copper_faces']:draw(shape(pad['geometry']),'#af8844',.7)
 if ref in p['placements'] or ref in ['M1','M2','M3','U102','J101']:
  ax.text(x,y,ref,ha='center',va='center',fontsize=9,color='#10212e')
ax.add_patch(Circle((155,159),23.75,facecolor='none',edgecolor='#b66b13',lw=1.2,ls='--'))
ax.text(154,145,'Cercle de collier indicatif Ø47,5\nDistinct des volumes solides du modèle',ha='center',fontsize=9,color='#955208')
ax.set_xlim(112,205);ax.set_ylim(150,118.5);ax.set_aspect('equal');ax.set_xlabel('x (mm)');ax.set_ylabel('y (mm)');ax.grid(alpha=.12)
ax.set_title('Intégration arrière — nouveaux connecteurs et quatre composants mobiles\nCourtyards disjoints ; intrusion du courtyard ESC dans le cercle indicatif conservée explicitement',fontsize=12)
ax.legend(handles=[Patch(facecolor='#476fa7',alpha=.45,label='Nouveau / déplacé'),Patch(facecolor='#e4a1a1',alpha=.45,label='Verrou conservé'),Patch(facecolor='#bbc7bd',alpha=.45,label='Placement conservé')],loc='lower right',fontsize=8)
fig.tight_layout();fig.savefig(ROOT/'rear-integration-placement.png',dpi=170);fig.savefig(ROOT/'rear-integration-placement.pdf')
