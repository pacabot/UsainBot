"""Contrôle croisé du .kicad_pro écrit : un net -> une classe, motifs vivants, valeurs >= JLCPCB.
Usage : check_classes.py <dossier du projet> [--md fichier]  (liste exhaustive net -> classe)."""
import json, sys, fnmatch, collections, pathlib, re

D = pathlib.Path(sys.argv[1])
pro = json.load(open(D / "UsainBot.kicad_pro"))
pcb = open(D / "UsainBot.kicad_pcb").read()
nets = sorted(set(re.findall(r'\(net "((?:[^"\\]|\\.)*)"\)', pcb)) - {""})
pats = [(p["pattern"], p["netclass"]) for p in pro["net_settings"]["netclass_patterns"]]
classes = {c["name"]: c for c in pro["net_settings"]["classes"]}
JLC = {"track": 0.10, "clearance": 0.10, "via_drill": 0.3, "via_pad": 0.4, "via_ring": 0.05}
errors = []

assign = {}
for n in nets:
    hits = sorted({cl for p, cl in pats if fnmatch.fnmatchcase(n, p)})
    if len(hits) > 1:
        errors.append(f"net {n} dans plusieurs classes {hits}")
    assign[n] = hits[0] if hits else "Default"
for p, cl in pats:
    if cl not in classes:
        errors.append(f"motif {p} -> classe absente {cl}")
    if not any(fnmatch.fnmatchcase(n, p) for n in nets):
        errors.append(f"motif mort {p}")
for name, c in classes.items():
    if c["track_width"] < JLC["track"]: errors.append(f"{name} piste {c['track_width']} < JLCPCB")
    if c["clearance"] < JLC["clearance"]: errors.append(f"{name} isolement {c['clearance']} < JLCPCB")
    if c["via_drill"] < JLC["via_drill"] or c["via_diameter"] < JLC["via_pad"]:
        errors.append(f"{name} via {c['via_diameter']}/{c['via_drill']} payante")
    if (c["via_diameter"] - c["via_drill"]) / 2 < JLC["via_ring"]:
        errors.append(f"{name} anneau de via trop fin")
    if c["diff_pair_width"] < JLC["track"] or c["diff_pair_gap"] < JLC["clearance"]:
        errors.append(f"{name} paire sous JLCPCB")
r = pro["board"]["design_settings"]["rules"]
for k, v in [("min_track_width", JLC["track"]), ("min_clearance", JLC["clearance"]), ("min_via_diameter", 0.4)]:
    if r[k] < v: errors.append(f"plancher {k} = {r[k]} < {v}")
na = pro["pcbnew"]["native_autorouter"]["netclasses"]
for n in nets:
    if n not in na: errors.append(f"autorouteur : net sans réglage {n}")
for n in na:
    if n not in assign: errors.append(f"autorouteur : réglage d'un net absent {n}")

by = collections.defaultdict(list)
for n, cl in assign.items():
    by[cl].append(n)
print("\n".join(errors) if errors else "aucune erreur")
for cl in classes:
    print(f"{cl:12s} {len(by[cl]):4d} nets")
if "--md" in sys.argv:
    out = open(sys.argv[sys.argv.index("--md") + 1], "w")
    for cl in classes:
        lst = sorted(by[cl])
        conn = [n for n in lst if n.startswith("unconnected-")]
        rest = [n for n in lst if not n.startswith("unconnected-")]
        out.write(f"\n### {cl} — {len(lst)} nets\n\n")
        if rest:
            out.write(", ".join(f"`{n}`" for n in rest) + "\n")
        if conn:
            out.write(f"\nPlus {len(conn)} broches non connectées (`unconnected-…`, une pastille chacune, rien à router).\n")
    out.close()
sys.exit(1 if errors else 0)
