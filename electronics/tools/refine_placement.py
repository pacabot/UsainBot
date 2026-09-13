#!/usr/bin/env python3
"""Placement par contraintes électriques explicites, sans routage.

Exécuter dans un environnement avec numpy et shapely. Les fichiers avant
restent immuables; le résultat est une table à appliquer avec pcbnew.
"""
import json, math, pathlib, collections
import numpy as np
import shapely as S
from shapely.geometry import Polygon, Point, box
from shapely.affinity import rotate, translate

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'placement-review'
data = json.loads((OUT/'before.json').read_text())
if (OUT/'additional.json').exists(): data.update(json.loads((OUT/'additional.json').read_text()))
netdata = json.loads((OUT/'net-components.json').read_text())
for r,f in data.items():
    for p in f['local_pads']:
        if r in netdata and p['pin'] in netdata[r]['pins']: p['net']=netdata[r]['pins'][p['pin']]['net']
outlines=json.loads((OUT/'board-outline.json').read_text())
board=S.union_all([Polygon(p['outer'],p['holes']) for p in outlines]).buffer(-.5)
constraints=json.loads((OUT/'functional-constraints.json').read_text())
P={}; polys={}; notes={}; groups={}; links={}
for r,f in data.items():
    ps=f['courtyard']
    if not ps: ps=[[[f['bbox'][0],f['bbox'][1]],[f['bbox'][2],f['bbox'][1]],[f['bbox'][2],f['bbox'][3]],[f['bbox'][0],f['bbox'][3]]]]
    f['shape']=S.union_all([Polygon(p) for p in ps])

def shape(r,x,y,a): return translate(rotate(data[r]['shape'],-a,origin=(0,0)),x,y)
def pad(r,p):
    if data[r]['locked'] and data[r]['side']=='B.Cu':
        return np.array(next(v['xy'] for v in data[r]['pads'] if v['pin']==str(p)))
    x,y,a,_=P[r]; t=next(v['xy'] for v in data[r]['local_pads'] if v['pin']==str(p)); a=math.radians(a)
    return np.array([x+t[0]*math.cos(a)+t[1]*math.sin(a), y-t[0]*math.sin(a)+t[1]*math.cos(a)])
def put(r,x,y,a,reason):
    P[r]=[round(float(x),4),round(float(y),4),round(float(a),4),'B' if data[r]['side']=='B.Cu' and data[r]['locked'] else 'F']
    polys[r]=shape(r,x,y,a);notes[r]=reason
for r,f in data.items():
    if f['locked']:put(r,*f['xy'],f['angle'],'Position verrouillée conservée')
# Angle choisi à centre fixe; enveloppe identique à celle d'origine.
put('U201',155,217,45,'Rotation seule : entrées analogiques et lignes vers avant; USB vers arrière')

# Réserves physiques des perçages; les courtyards des ensembles mécaniques
# sont déjà des obstacles, y compris les cinq îlots du module sur entretoises.
holes=[]
for r,f in data.items():
    if not f['locked']: continue
    for p in f['pads']:
        if not p['pin'] and max(p['drill'])>0: holes.append(Point(p['xy']).buffer(max(p['drill'])/2+.5))
hole_union=S.union_all(holes)
# Le collier de turbine indicatif reste libre pour les nouveaux composants.
hole_union=S.union_all([hole_union,Point(155,159).buffer(23.75)])
power={'GND','+3V3','+3V3A','VBAT','VPACK','/Alimentation/VBUS_IN'}

def nearest(r,xy,reason,anchors=(),angles=(0,90,180,270),radius=12,weight=.2):
    """Minimise les distances entre broches sous contraintes exactes des cours."""
    anchors=list(anchors)
    occupied=S.union_all([g.buffer(.12) for q,g in polys.items() if q!=r and P[q][3]=='F']+[hole_union])
    tx_refs={f'{prefix}{base+n}' for base in (500,520,540) for prefix,nn in [('Q',[1]),('R',[1,2,3]),('C',[5]),('D',[3,4])] for n in nn}
    if r in tx_refs:
        occupied=S.union_all([occupied]+[polys[u].buffer(2) for u in ('U501','U502','U504') if u in polys])
    coords=np.array(data[r]['shape'].exterior.coords) if data[r]['shape'].geom_type=='Polygon' else None
    assert coords is not None, r
    local={p['pin']:np.array(p['xy']) for p in data[r]['local_pads']}
    # Nets locaux seulement; les ancres explicites dominent les raccordements
    # distants MCU, et les rails ne servent jamais de centre de gravité.
    implicit=[]
    for pp in data[r]['local_pads']:
        if not pp['net'] or pp['net'] in power or pp['net'].startswith('unconnected'): continue
        near=[]
        for rr in P:
            if rr==r:continue
            for q in data[rr]['local_pads']:
                if q['net']==pp['net']:near.append((rr,q['pin']))
        if len(near)<=8:
            for rr,pn in near:
                dist=np.linalg.norm(pad(rr,pn)-np.array(xy))
                if dist<20:implicit.append((pp['pin'],rr,pn,.25))
    anchors+=implicit
    for reach in [radius,radius*1.8,radius*3,radius*5]:
        v=np.arange(-reach,reach+.01,.4)
        xx,yy=np.meshgrid(v+xy[0],v+xy[1]);pos=np.column_stack((xx.ravel(),yy.ravel()))
        scores=[];positions=[];rotations=[]
        for a in angles:
            t=math.radians(a);mat=np.array([[math.cos(t),math.sin(t)],[-math.sin(t),math.cos(t)]])
            score=weight*np.linalg.norm(pos-np.array(xy),axis=1)
            for pin,rr,pn,w in anchors:
                if rr in P and str(pin) in local:score+=w*np.linalg.norm(pos+mat@local[str(pin)]-pad(rr,pn),axis=1)
            scores.append(score);positions.append(pos);rotations.append(np.full(len(pos),a))
        scores=np.concatenate(scores);positions=np.concatenate(positions);rotations=np.concatenate(rotations)
        order=np.argsort(scores)
        for start in range(0,len(order),400):
            ids=order[start:start+400];aa=np.deg2rad(rotations[ids]);c=np.cos(aa);s=np.sin(aa)
            vs=np.empty((len(ids),len(coords),2))
            vs[:,:,0]=positions[ids,0,None]+c[:,None]*coords[:,0]+s[:,None]*coords[:,1]
            vs[:,:,1]=positions[ids,1,None]-s[:,None]*coords[:,0]+c[:,None]*coords[:,1]
            gs=S.polygons(vs);valid=S.covered_by(gs,board)&~S.intersects(gs,occupied)
            if valid.any():
                k=ids[np.flatnonzero(valid)[0]];put(r,*positions[k],rotations[k],reason)
                return
    raise RuntimeError('Pas de placement : '+r)

def bind(r,rr,pn,pin='1',priority=8,reason=''):
    constraints[r]={'anchor_ref':rr,'anchor_pin':str(pn),'pin':str(pin),'priority':priority,'note':reason}

# Les boîtiers analogiques utilisent A=TIA, B=gain. La broche inverseuse
# regarde la photodiode; les autres composants sont placés dans cette poche.
for r,tm,b in [('U504','TM541',540),('U502','TM521',520),('U501','TM501',500)]:
    if r not in data:continue
    xy=pad(tm,'4')
    # Recherche conjointe boîtier + Rf/Cf. Un emplacement libre pour le
    # seul AOP peut être inutilisable pour sa contre-réaction.
    native=data[r]['shape']
    template=[(f'C{b+1}',-4.6,-1.3,90),(f'R{b+4}',-6,-1.3,90)]
    data[r]['shape']=S.union_all([native]+[shape(rr,x,y,a) for rr,x,y,a in template]).convex_hull
    nearest(r,xy,'TIA et gain avec poche de contre-réaction auprès de '+tm,[('2',tm,'4',10)],tuple(range(0,360,15)),12)
    data[r]['shape']=native;polys[r]=shape(r,*P[r][:3])
    x,y,a,_=P[r];t=math.radians(a);co,si=math.cos(t),math.sin(t)
    for rr,lx,ly,la in template:
        put(rr,x+lx*co+ly*si,y-lx*si+ly*co,(a+la)%360,'Contre-réaction TIA placée conjointement avec '+r)
    print(r,'PD input mm',round(float(np.linalg.norm(pad(r,2)-xy)),2),flush=True)

# Étage puissance et interfaces : positions de travail justifiées par domaine.
seeds={'U102':(126,126.5,0),'U103':(124,163,0),'U101':(150,130,180),
       'U701':(145,196,0),'U105':(162,244,90),'J701':(114,174,90),
       'BZ601':(110,163,0),'SW101':(138,121.5,0),'F101':(191,121.8,0),
       'C109':(130,170,0),'C354':(190,127.3,0),'D102':(205,159,0),'C704':(142,127,0),
       'Q101':(137,129,0),'Q104':(192.8,132,0),'Q401':(127,275,0),
       'Q402':(183,275,0),'Q601':(116,162,0),'Q602':(165,278,0),
       'Q701':(119,175,0),'Q702':(123,177,0)}
for r,(x,y,a) in seeds.items():
    nearest(r,(x,y),'Organisation par fonction : '+r,angles=(a,(a+90)%360,(a+180)%360,(a+270)%360),radius=8,weight=4)

# Priorité aux boucles TIA puis alimentation, avant les passifs de commande.
for base,amp,tm in [(500,'U501','TM501'),(520,'U502','TM521'),(540,'U504','TM541')]:
    bind('R'+str(base+4),amp,2,priority=10,reason='Résistance de transimpédance, boucle entrée-sortie A')
    bind('C'+str(base+1),amp,2,priority=10,reason='Compensation 22 pF parallèle au retour TIA')
    bind('C'+str(base+2),amp,1,priority=8,reason='Liaison AC à la sortie TIA')
    bind('R'+str(base+5),amp,5,priority=8,reason='Polarisation de l’entrée du gain B')
    bind('R'+str(base+6),amp,6,pin='2',priority=9,reason='Contre-réaction du gain B')
    bind('R'+str(base+7),amp,6,priority=9,reason='Branche de gain vers référence médiane')
    bind('C'+str(base+3),'R'+str(base+7),2,priority=7,reason='Retour AC du gain vers masse')
    # Filtre ADC : C placé côté MCU pour que le réservoir reste à l'ADC.
    bind('C'+str(base+4),'U201',27+(base-500)//20,priority=10,reason='Réservoir ADC laser, côté broche STM32')
    bind('R'+str(base+8),'C'+str(base+4),1,pin='2',priority=7,reason='Résistance série du filtre ADC au pied du condensateur')
    nearest('Q'+str(base+1),pad(tm,1),'Commande laser, côté émetteur de '+tm,[('3',tm,1,8)],radius=10)
    bind('R'+str(base+1),tm,2,pin='2',priority=7,reason='Limitation du courant émetteur')
    bind('R'+str(base+2),'Q'+str(base+1),1,pin='2',priority=7,reason='Résistance série de grille')
    bind('R'+str(base+3),'Q'+str(base+1),1,priority=6,reason='Rappel de grille')
    bind('C'+str(base+5),'R'+str(base+2),1,pin='2',priority=7,reason='Couplage AC de la modulation : condensateur série avant résistance de grille')
    bind('D'+str(base+3),tm,1,priority=6,reason='Protection ESD sur cathode laser')
    bind('D'+str(base+4),'C'+str(base+5),2,priority=6,reason='Écrêtage négatif du signal de grille après couplage AC')
for r,a in [('C563','U501'),('C564','U502'),('C568','U504')]:bind(r,a,4,priority=10,reason='Découplage local AOP')
for r,a in [('C569','U502'),('C570','U504')]:bind(r,a,3,priority=9,reason='Filtrage local de VREF_RX après séparation physique des TIA')
for r,rr,pn in [('C223','U201',6),('C224','U201',6),('C351','U351',5)]:
    bind(r,rr,pn,priority=10,reason='Découplage ajouté sur alimentation locale distante')
bind('C206','U201',17,priority=9,reason='Réservoir VDD près de l’arrivée alimentation')
for r in ('C209','C211','C224'):constraints[r]['priority']=9
bind('C566','U503',8,priority=10,reason='Découplage VDD de la centrale inertielle verrouillée')
bind('C567','U503',5,priority=10,reason='Découplage VDDIO de la centrale inertielle verrouillée')
bind('C124','U105',28,priority=10,reason='Découplage VDD du contrôleur PWM de témoins')
for r,rr,pin in [('R441','Q401','2'),('R442','Q401','1'),('R443','Q402','2'),('R444','Q402','1')]:
    bind(r,rr,1,pin=pin,priority=7,reason='Commande de grille et rappel du banc IR')
for r,pin,ap in [('R561','2',3),('R562','1',3),('C561','1',3),('R563','2',12),('R564','1',12),('C562','1',12),('C565','1',4)]:
    bind(r,'U501',ap,pin=pin,priority=6,reason='Références analogiques et réservoir du groupe avant')

# Passifs de ligne remontés au-dessus des capteurs, autour de la pastille
# traversante concernée; lecture RC conservée au récepteur.
for i in range(12):
    u=f'U{401+i}'
    bind(f'R{401+i}',u,2,pin='2',priority=7,reason='Courant LED IR, Top au droit du capteur')
    bind(f'R{421+i}',u,4,pin='1',priority=8,reason='Charge phototransistor près du capteur')
    bind(f'C{401+i}',u,4,priority=8,reason='Filtre signal ligne près du phototransistor')
    bind(f'R{445+i}',f'D{401+i}',2,pin='2',priority=5,reason='Résistance témoin associé')
    constraints[f'D{401+i}']={'priority':3,'note':f'Témoin aligné sur le capteur U{401+i}, face visible'}
constraints['D606']={'priority':3,'note':'Témoin bleu de suivi caméra, au nez de la carte'}

# Les retours des boucles critiques ont le même poids que leur entrée.
extra={}
for base,amp in [(500,'U501'),(520,'U502'),(540,'U504')]:
    for r in [f'R{base+4}',f'C{base+1}']:extra[r]=[('2',amp,'1',8)]
    extra[f'R{base+6}']=[('1',amp,'7',8)]
for off,u in [(300,'U301'),(350,'U351')]:
    extra[f'C{off+3}']=[('2',u,'9',4)]
    extra[f'C{off+5}']=[('2',u,'11',8)]
    extra[f'C{off+6}']=[('2',u,'14',8)]
extra['C104']=[('2','U102','17',8)]
extra['C114']=[('2','U103','5',8)]

remaining=set(data)-set(P)
while remaining:
    ready=[r for r in remaining if constraints.get(r,{}).get('anchor_ref') not in remaining]
    if not ready:raise RuntimeError('Ancres cycliques '+str(remaining))
    def priority(r):
        k=constraints.get(r,{})
        return (k.get('priority',2),data[r]['shape'].area,r)
    r=max(ready,key=priority); k=constraints.get(r,{})
    rr=k.get('anchor_ref');pn=k.get('anchor_pin');anchors=[]
    if rr in P:
        xy=pad(rr,pn) if pn is not None else np.array(P[rr][:2])
        if pn is not None:anchors=[(str(k.get('pin','1')),rr,str(pn),8)]
        reason=k.get('note','Groupe fonctionnel auprès de '+rr)
        if rr=='U201': angles=tuple(range(0,360,45))
        elif rr.startswith('TM'):angles=tuple(range(0,360,15))
        else:angles=tuple(dict.fromkeys([0,90,180,270,P[rr][2],(P[rr][2]+90)%360,(P[rr][2]+180)%360,(P[rr][2]+270)%360]))
    else:
        xy=data[r]['xy'];reason=k.get('note','Nets locaux et espace de routage');angles=(0,90,180,270,data[r]['angle'])
    anchors+=extra.get(r,[])
    nearest(r,xy,reason,anchors,angles,radius=8,weight=.3 if anchors else 1)
    remaining.remove(r)
    if len(remaining)%25==0:print('Reste',len(remaining),flush=True)
(OUT/'placement.json').write_text(json.dumps(P,indent=2)+'\n')
(OUT/'placement-rationale.json').write_text(json.dumps({r:{'reason':notes[r],'constraint':constraints.get(r,{})} for r in P},indent=2,ensure_ascii=False)+'\n')
print('Table écrite',len(P))
