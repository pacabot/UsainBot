#!/usr/bin/env python3
"""Ramène une carte enregistrée par le fork KiCad 10.99 au format KiCad 10.0 stable.

Le fork (autorouteur) écrit le format 20260901 : position des empreintes en
(transform (translate) (rotate) (scale)) et quelques réglages que 10.0 ne
connaît pas. KiCad 10.0.x refuse alors d'ouvrir la carte. Ce script réécrit
le fichier en place au format 20260206, sans rien toucher d'autre.

    python3 tools/to_kicad10.py UsainBot.kicad_pcb

À relancer après chaque enregistrement depuis le fork.
"""
import re
import sys

VERSION_10 = "20260206"


def num(v):
    f = float(v)
    return str(int(f)) if f == int(f) else v


def transform_to_at(m):
    indent, x, y, rot, scale = m.groups()
    if scale.split() != ["1", "1"]:
        sys.exit("échelle %s non convertible en (at)" % scale)
    rot = num(rot)
    return "%s(at %s %s%s)" % (indent, x, y, "" if rot == "0" else " " + rot)


def convert(s):
    s, n = re.subn(r'\(version \d+\)', "(version %s)" % VERSION_10, s, count=1)
    s = re.sub(r'\(generator_version "[^"]*"\)', '(generator_version "10.0")', s, count=1)
    s, n_fp = re.subn(
        r'(\t*)\(transform\s*\(translate (\S+) (\S+)\)\s*\(rotate (\S+)\)\s*\(scale ([^)]*)\)\s*\)',
        transform_to_at, s)
    # Réglages propres au fork : lignes entières supprimées
    for tok in ("spec_frequency", "dielectric_model", "pngdpi", "pngantialias"):
        s = re.sub(r'\n\t*\(%s [^()]*\)' % tok, "", s)
    s = re.sub(r'\n\t*\(zone_defaults\)', "", s)
    if "(transform" in s:
        sys.exit("transform restant non converti")
    return s, n_fp


def main():
    for path in sys.argv[1:]:
        with open(path, newline="") as f:
            s = f.read()
        s, n_fp = convert(s)
        with open(path, "w", newline="") as f:
            f.write(s)
        print("%s : %d empreintes converties, format %s" % (path, n_fp, VERSION_10))


if __name__ == "__main__":
    main()
