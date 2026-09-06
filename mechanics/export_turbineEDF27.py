# -*- coding: utf-8 -*-
"""Ré-exporte la turbine EDF 27 depuis le document PartDesign, en couleur.

`turbineEDF27.FCStd` se modifie **à la main dans FreeCAD** : c'est lui qui fait
foi, et `turbineEDF27.py` ne doit plus être relancé dessus — il écrirait
par-dessus (les deux visent le même nom de fichier, piège relevé le
3 septembre). Ce script ne fabrique rien : il ouvre le document tel quel et
en sort le STEP que porte l'empreinte KiCad.

**Les couleurs sont relues DANS le document**, pas redéclarées ici : elles
vivent dans `GuiDocument.xml` (quel objet pointe vers quel blob) et dans les
blobs binaires `ShapeAppearanceNN` du même zip. Une palette recopiée dans un
script se serait désynchronisée au premier coup de pinceau dans l'interface.

Format d'un blob `ShapeAppearance` (FreeCAD 1.0) : un compteur uint32, puis
par matériau quatre couleurs empaquetées en uint32 petit-boutiste
(ambiante, **diffuse**, spéculaire, émissive) et deux flottants (brillance,
transparence). L'octet de poids fort porte le rouge.

Pourquoi pas l'interface : un `ViewObject` n'existe que si l'interface est
chargée, mais `QT_QPA_PLATFORM=offscreen` reste bloqué à l'ouverture de ce
document-ci (pas de contexte OpenGL, cf. le piège déjà relevé sur
`saveImage()`). D'où la lecture directe du zip, et `freecadcmd` pour la
géométrie seule.

**Le document n'est jamais sauvegardé.** Une sauvegarde par FreeCAD hors
interface supprime `GuiDocument.xml` — couleurs, transparences et caméra avec.

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd export_turbineEDF27.py

Sorties : `turbineEDF27.step` ici, et la copie que lit l'empreinte dans
`../electronics/kicad-lib/3d/Turbine_EDF27.step`.
"""

import os
import re
import shutil
import struct
import sys
import zipfile

import FreeCAD as App
import Import

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(
    os.path.join(ICI, '..', 'electronics', 'kicad-lib')))
from step_colors import injecter_couleurs_step

DOC = os.path.join(ICI, 'turbineEDF27.FCStd')
SORTIE = os.path.join(ICI, 'turbineEDF27.step')
COPIE = os.path.abspath(os.path.join(
    ICI, '..', 'electronics', 'kicad-lib', '3d', 'Turbine_EDF27.step'))

# Les quatre corps de la turbine ; les trois volumes de référence
# (enveloppe d'interdiction, outils de découpe) restent dehors.
CORPS = ('Fut', 'Redresseur', 'Rotor', 'Faisceau')


def apparences(chemin):
    """{nom d'objet: ((r, g, b), transparence)} relu dans le .FCStd."""
    z = zipfile.ZipFile(chemin)
    gui = z.read('GuiDocument.xml').decode('utf-8', 'replace')
    out = {}
    for m in re.finditer(r'<ViewProvider name="([^"]+)"(.*?)</ViewProvider>',
                         gui, re.S):
        nom, corps = m.group(1), m.group(2)
        fichier = re.search(r'name="ShapeAppearance".*?<MaterialList file="([^"]+)"',
                            corps, re.S)
        if not fichier:
            continue
        d = z.read(fichier.group(1))
        if len(d) < 28:
            continue
        # 0: compteur, 1: ambiante, 2: DIFFUSE, 3: speculaire, 4: emissive,
        # 5: brillance (float), 6: transparence (float)
        champs = struct.unpack('<5I2f', d[:28])
        diffuse = champs[2]
        out[nom] = (((diffuse >> 24) & 255, (diffuse >> 16) & 255,
                     (diffuse >> 8) & 255), champs[6])
    return out


def main():
    vues = apparences(DOC)
    doc = App.openDocument(DOC)
    objets, couleurs, transparences = [], {}, {}
    for nom in CORPS:
        o = doc.getObject(nom)
        if o is None:
            print('CORPS ABSENT :', nom)
            continue
        objets.append(o)
        rgb, transp = vues.get(nom, ((200, 200, 200), 0.0))
        couleurs[o.Label] = tuple(c / 255.0 for c in rgb)
        if transp > 0.001:
            transparences[o.Label] = transp
        print('%-12s vol %7.3f cm3   rgb %-15s transparence %.0f %%'
              % (o.Label, o.Shape.Volume / 1000.0, str(rgb), transp * 100))

    if not objets:
        raise SystemExit('rien a exporter')

    Import.export(objets, SORTIE)
    n = injecter_couleurs_step(SORTIE, couleurs, transparences)
    shutil.copyfile(SORTIE, COPIE)
    bb = objets[0].Shape.BoundBox
    for o in objets[1:]:
        bb = bb.united(o.Shape.BoundBox)
    print('%s : %d octets, %d solides colores'
          % (os.path.basename(SORTIE), os.path.getsize(SORTIE), n))
    print('encombrement x %.2f..%.2f  y %.2f..%.2f  z %.2f..%.2f'
          % (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
    print('copie ->', os.path.relpath(COPIE, ICI))

    # Fermer SANS sauvegarder : une sauvegarde hors interface emporte le
    # GuiDocument.xml, donc toutes les couleurs du document.
    App.closeDocument(doc.Name)


main()
