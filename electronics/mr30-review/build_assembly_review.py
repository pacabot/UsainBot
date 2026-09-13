"""Read the final PCB and create a plugged 3D inspection copy. KiCad Python."""
from pathlib import Path
import pcbnew

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
board = pcbnew.LoadBoard(str(ROOT / 'UsainBot.kicad_pcb'))
for footprint in board.GetFootprints():
    if footprint.GetReference() == 'J102':
        model = pcbnew.FP_3DMODEL()
        model.m_Filename = '${KIPRJMOD}/kicad-lib/3d/AMASS_MR30_Mated_Clearance.step'
        footprint.Models().push_back(model)
out = HERE / 'assembly-mated.kicad_pcb'
pcbnew.SaveBoard(str(out), board)
# Models() yields values, so changing members inside a Python for-loop does
# not update the vector. Resolve project paths in the serialized review copy.
out.write_text(out.read_text().replace('${KIPRJMOD}/kicad-lib',
                                      '${KIPRJMOD}/../kicad-lib'))
print(out)
