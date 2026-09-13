from pathlib import Path
import sys,zipfile,json,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from sexp import parse,find,find_all,unq
with zipfile.ZipFile(R/'mr30-review/before-mr30.zip') as z:
 old=parse(z.read('UsainBot.kicad_pcb').decode())[0]
new=parse((R/'UsainBot.kicad_pcb').read_text())[0]
def refs(root):
 return {next(unq(p[2]) for p in find_all(f,'property') if unq(p[1])=='Reference'):f for f in find_all(root,'footprint')}
a,b=refs(old),refs(new);assert a.keys()==b.keys()
def pose(f):return [find(f,k) for k in ['at','layer','locked','uuid']]
def pins(f):
 return sorted((unq(p[1]),unq(find(p,'net')[-1]) if find(p,'net') else '') for p in find_all(f,'pad') if unq(p[1]))
assert all(pose(a[r])==pose(b[r]) and a[r][1]==b[r][1] for r in a if r!='J102')
assert all(pins(a[r])==pins(b[r]) for r in a)
def nets(p):
 t=ET.parse(p).getroot();return {n.get('name'):sorted((v.get('ref'),v.get('pin')) for v in n.findall('node')) for n in t.find('nets')}
assert nets(R/'mr30-review/before-netlist.xml')==nets(R/'mr30-review/after-netlist.xml')
d={'status':'passed','other_footprints_unchanged_pose_uuid_lock_type':len(a)-1,'all_footprint_pad_nets_unchanged':len(a),'schematic_net_nodes_unchanged':True,'locked_count':sum(find(f,'locked')==['locked','yes'] for f in b.values()),'J102_before':pose(a['J102']),'J102_after':pose(b['J102'])}
(R/'mr30-review/revision-diff.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
