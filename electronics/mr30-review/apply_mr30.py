from pathlib import Path
import sys,json,copy,shutil
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from sexp import parse,find,find_all,unq,dump
fp='Pacabot:AMASS_MR30PB-M_1x03_P3.50mm_Vertical'
fields={'Manufacturer':'AMASS','MPN':'MR30PB-M30.G.Y','Mating_connector':'MR30-F.G.Y; optional cover 98023.PG','Harness':'Project pinout: 1 GND / 2 PACK_MID / 3 VPACK; AWG16 power, AWG24 MID; 5cm power leads each assumed','Rated_current':'20 A per manufacturer at deltaT 85K with AWG16; thermal validation required at 15.5A continuous /18.5A peak','Mechanical_revision':'AMASS MR30PB-M 2021V1: 11.9x5.3x10.4mm; 3mm tails; pitch3.50; drill1.80+0.20/0','Operating_budget':'ESC 12A continuous /15A peak + 2 DC motors x1A + electronics provisional1.5A'}
p=ROOT/'01-power.kicad_sch';root=parse(p.read_text())[0]
j=next(s for s in find_all(root,'symbol') if any(unq(x[1])=='Reference' and unq(x[2])=='J102' for x in find_all(s,'property')))
props={unq(x[1]):x for x in find_all(j,'property')}
for key in ['Mating_housing','Mating_contacts','Mating_TPA']:
 if key in props:j.remove(props[key])
updates={'Value':'Pack 2S - AMASS MR30','Footprint':fp,'Datasheet':'https://lucidar.me/en/electronics/files/mr30pb-m.pdf',**fields}
for k,v in updates.items():
 if k not in props:
  n=copy.deepcopy(props['Manufacturer']);n[1]=json.dumps(k);j.append(n);props[k]=n
 props[k][2]=json.dumps(v)
p.write_text(dump(root)+'\n')
p.write_text(p.read_text().replace('J102 Mega-Fit 3 contacts','J102 MR30 3 contacts'))
p=ROOT/'tools/integration_blocks.py';s=p.read_text();start=s.index("    j = sh.place",s.index('def build_battery'));end=s.index("    api['cx']",start)
s=s[:start]+"    j = sh.place('Connector_Generic:Conn_01x03', 'J102', 'Pack 2S - AMASS MR30',\n                  254, 46, fp=footprint, ref_at=(254, 33), val_at=(254, 61),\n                  datasheet='https://lucidar.me/en/electronics/files/mr30pb-m.pdf',\n                  fields="+repr(fields)+")\n"+s[end:];p.write_text(s)
p=ROOT/'tools/design.py';s=p.read_text().replace('Pacabot:Molex_Mega-Fit_200241-1133_1x03_P5.70mm_Vertical',fp).replace('Mega-Fit 3 contacts','MR30 3 contacts');p.write_text(s)
shutil.copy2(ROOT/'integration-review/after-netlist.xml',ROOT/'mr30-review/before-netlist.xml')
(ROOT/'mr30-review/positions.json').write_text(json.dumps({'J102':{'position':[174.7,129.1],'angle':0}}))
print('J102 schematic and generators updated; unchanged symbol UUID and wiring')
