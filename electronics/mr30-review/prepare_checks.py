from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'integration-review/verify_final_integration.py').read_text().replace("review = project / 'integration-review'","review = project / 'mr30-review'").replace("initial_zip = review / 'before-integration.zip'","initial_zip = project / 'integration-review/before-integration.zip'")
s=s.replace("([11.4, 0], 'GND', [2.7, 2.7]","([3.5, 0], 'GND', [3, 3]").replace("([5.7, 0], '/Alimentation/PACK_MID', [2.7, 2.7]","([0, 0], '/Alimentation/PACK_MID', [2.5, 2.5]").replace("([0, 0], 'VPACK', [2.7, 2.7]","([-3.5, 0], 'VPACK', [3, 3]").replace("'J102': [(2.85, 1.34, 3), (8.55, 1.34, 3)]","'J102': []")
(R/'mr30-review/verify_mr30_integration.py').write_text(s)
s=(R/'integration-review/build_assembly_review.py').read_text().replace('Molex_2002411133_mated_plug_envelope.step','AMASS_MR30_Mated_Clearance.step')
(R/'mr30-review/build_assembly_review.py').write_text(s)
