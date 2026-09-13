from pathlib import Path
import pcbnew
R=Path(__file__).resolve().parents[1]
p=R/'kicad-lib/Pacabot.pretty/AMASS_MR30PB-M_1x03_P3.50mm_Vertical.kicad_mod'
p.write_text(p.read_text().replace('(size .7 .7)','(size .8 .8)'))
b=pcbnew.LoadBoard(str(R/'UsainBot.kicad_pcb'))
f=next(f for f in b.GetFootprints() if f.GetReference()=='J102')
for g in f.GraphicalItems():
 if isinstance(g,pcbnew.PCB_TEXT):g.SetTextSize(pcbnew.VECTOR2I(800000,800000))
pcbnew.SaveBoard(str(R/'UsainBot.kicad_pcb'),b)
p=R/'mr30-review/build_mr30.py';p.write_text(p.read_text().replace('(size .7 .7)','(size .8 .8)'))
