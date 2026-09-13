#!/usr/bin/env python3
"""Physical pad-to-pad evidence and net/lock invariants, without routing."""
import csv,json,math,pathlib,collections
ROOT=pathlib.Path(__file__).resolve().parents[1]/'placement-review'
before=json.loads((ROOT/'before.json').read_text())
after=json.loads((ROOT/'geometry-after.json').read_text())
f=after['footprints'];why=json.loads((ROOT/'placement-rationale.json').read_text())
def p(ref,pin,old=False):
    a=before[ref]['pads'] if old else f[ref]['pads']
    key='pin' if old else 'number';pos='xy' if old else 'position'
    return next(v[pos] for v in a if v[key]==str(pin))
def d(r,pn,rr,pp,old=False):return round(math.dist(p(r,pn,old),p(rr,pp,old)),3)
locked=[]
for r,v in before.items():
    if v['locked']:
        assert f[r]['position']==v['xy'] and f[r]['locked'] and f[r]['face']==v['side'][0],r
        if r!='U201':assert abs(f[r]['angle']-v['angle'])<1e-6,r
        locked.append(r)
n=json.loads((ROOT/'net-components.json').read_text());missing=[];mismatch=[]
for r,comp in n.items():
    for pin,v in comp['pins'].items():
        pads=[a for a in f[r]['pads'] if a['number']==pin]
        if not pads:missing.append([r,pin])
        for a in pads:
            if a['net']!=v['net']:mismatch.append([r,pin,a['net'],v['net']])
assert not missing and not mismatch,(missing,mismatch)
lasers=[]
for base,u,oldin,oldout in [(500,'U501',2,1),(520,'U502',6,7),(540,'U504',9,8)]:
    tm=f'TM{base+1}';rf=f'R{base+4}';cf=f'C{base+1}'
    row={'station':tm,'amplifier':u,'photodiode_input_before_mm':d(tm,4,'U501',oldin,True),'photodiode_input_after_mm':d(tm,4,u,2)}
    for label,r in [('feedback_resistor',rf),('feedback_capacitor',cf)]:
        row[label+'_leads_before_mm']=round(d(r,1,'U501',oldin,True)+d(r,2,'U501',oldout,True),3)
        row[label+'_leads_after_mm']=round(d(r,1,u,2)+d(r,2,u,1),3)
    lasers.append(row)
rows=[]
for r,v in why.items():
    c=v.get('constraint',{});a=c.get('anchor_ref');pn=c.get('anchor_pin');pin=c.get('pin','1')
    if a and pn:
        row={'reference':r,'value':n.get(r,{}).get('value',f[r]['value']),'group':c.get('group',''),'priority':c.get('priority',0),'anchor':f'{a}.{pn}','component_pad':pin,'distance_mm':d(r,pin,a,pn),'role':v['reason']}
        if r in before and a in before:
            try:row['before_mm']=d(r,pin,a,pn,True)
            except StopIteration:pass
        rows.append(row)
with (ROOT/'passive-roles-and-distances.csv').open('w') as out:
    w=csv.DictWriter(out,fieldnames=['reference','value','group','priority','anchor','component_pad','distance_mm','before_mm','role']);w.writeheader();w.writerows(rows)
drc=json.loads((ROOT/'drc-after.json').read_text())
summary={'footprints_before':len(before),'footprints_after':len(f),'locked_positions_preserved':len(locked),'stm32_rotation_before_deg':before['U201']['angle'],'stm32_rotation_after_deg':f['U201']['angle'],
 'flipped_to_top':sorted(r for r,v in before.items() if v['side']=='B.Cu' and f[r]['face']=='F'),
 'remaining_bottom':sorted(r for r,v in f.items() if v['face']=='B'),'added_components':sorted(set(f)-set(before)),
 'net_mismatches':mismatch,'missing_pads':missing,'laser_distances':lasers,
 'drc_counts':dict(collections.Counter(v['type'] for v in drc['violations'])),
 'drc_errors':[v for v in drc['violations'] if v['severity']=='error'],
 'schematic_parity_count':len(drc['schematic_parity']),
 'placement_geometry_violations':after['audit']['issues'],
 'distance_note':'Distances géométriques entre centres des pastilles; aucune longueur routée ni validation de SI/PI.'}
(ROOT/'verification-summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ('flipped_to_top','placement_geometry_violations','drc_errors')},indent=2,ensure_ascii=False))
print('Largest high-priority distances:',sorted([r for r in rows if r['priority']>=9],key=lambda x:x['distance_mm'],reverse=True)[:12])
