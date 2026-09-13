# Correction mécanique des ITR8307/S17/TR8

La nomenclature et les valeurs schématiques du projet désignent déjà **ITR8307/S17/TR8**, code LCSC **C81632 = ITR8307/S17/TR8(B)**. Le remplacement du modèle et du dessin des pastilles corrige le boîtier de cette référence ; il ne sélectionne pas un autre capteur.

## Sources

- [Everlight Europe, fiche produit exacte S17/TR8](https://www.everlighteurope.com/product-details?category=Optical+Sensors&id=4043&name=ITR8307%2FS17%2FTR8). Les liens IGS et STEP sont désactivés, avec les attributs « No IGS file available » et « No STEP file available ».
- [Everlight DRX-0000322 rév.6, page 2](https://www.everlighteurope.com/custom/files/datasheets/DRX-0000322.pdf), copie locale `ITR8307-S17-TR8.pdf` et rendu `ITR8307-S17-TR8-drawing.png`. Source dimensionnelle retenue.
- [JLCPCB C81632](https://jlcpcb.com/partdetail/EverlightElec-ITR8307_S17_TR8_B/C81632), pour l'association code de nomenclature ↔ référence fabricant.
- Les fiches TR8 sans S17 et S18/TR8 sont conservées comme documents de comparaison ; elles ne sont pas la source du modèle S17.

## Défaut hérité identifié dans l'assemblage initial

L'ancienne empreinte `Pacabot:ITR8307_dessous` était une copie de `OptoDevice:Everlight_ITR8307` avec suppression du rectangle `Edge.Cuts`. L'original indique explicitement « with PCB cutout » et comporte une ouverture de 3,7 × 3,6 mm. Son modèle `Everlight_ITR8307.step` a une portée de pattes de **6,7 mm**, incompatible avec les **4,6 mm** du S17. Le corps est intentionnellement en partie sous son plan de soudure (`z=-0,4 mm`). Retirer le contour sans changer de boîtier produit un véritable défaut d'assemblage dans le modèle.

L'audit du STEP initial a mesuré une intersection corps/FR4 de **2,682225 mm³ pour chacun des 12 capteurs U401–U412**. La pénétration vaut 0,315 mm avec le datum de l'export KiCad ; une section interne correspond au corps plastique continu (environ 8,515 mm²), pas aux quatre pattes. Il ne fallait pas résoudre ce défaut par un décalage Z artificiel : les broches du mauvais modèle auraient quitté le plan de soudure.

La bonne référence S17 possède des pattes CMS formées, et **ne demande pas de fenêtre sous le corps**, sur Top comme sur Bottom. Ses anciennes pastilles y=±2,8 mm devaient également être corrigées ; changer uniquement l'enveloppe 3D aurait caché une erreur d'empreinte.

## Modèle corrigé

`../../kicad-lib/3d/Everlight_ITR8307_S17_TR8.FCStd` et `.step` sont générés par `../build_itr8307_s17_tr8.py` avec FreeCAD Part Design. Aucun déplacement ni rotation supplémentaire dans le champ modèle KiCad n'est nécessaire.

| Élément | Dimension nominale retenue | Origine |
|---|---:|---|
| Corps X × Y × hauteur | 3,4 × 2,7 × 1,5 mm | Fiche rév.6 ; ±0,2 en X/Y, +0,2/−0 en hauteur |
| Portée extérieure des pattes Y | 4,6 mm | Fiche, ±0,2 |
| Entraxe des deux lignes X | 1,8 mm | Fiche |
| Largeur de pied | 0,5 mm | Fiche ; tolérance générale ±0,15 |
| Longueur du pied distal | 0,38 mm | Fiche ; tolérance générale ±0,15 |
| Dessous corps / plan de soudure | 0,12 mm | Fiche, ±0,05 |
| Hauteur depuis plan de soudure | 1,62 mm nominal ; 1,87 mm max | Somme des deux cotes précédentes |
| Centres des pieds Y | ±2,11 mm | Déduction géométrique : 4,6/2 − 0,38/2 |

Le repère conserve les numéros de la variante déjà schématisée : **1 cathode, 2 anode, 3 collecteur, 4 émetteur**. Sur l'empreinte native Top, les centres sont 1=(-0,9;+2,11), 2=(-0,9;−2,11), 3=(+0,9;+2,11), 4=(+0,9;−2,11). Dans le STEP, Y change de signe. Le plan de soudure est Z=0 et le corps occupe Z=0,12..1,62 mm ; KiCad effectue le retournement Bottom.

Les quatre pieds offrent chacun une surface plate nominale de **0,5 × 0,38 mm = 0,19 mm²** au plan Z=0. Leur enveloppe et leur contact au plan de soudure sont vérifiés dans `s17-mechanical-model.json`.

**Simplifications explicites :** le chanfrein du corps situé près de la broche 2 est omis, ce qui conserve une enveloppe rectangulaire prudente pour les collisions ; le dessin Fab de l’empreinte porte le vrai chanfrein. Ensuite, les rayons de cintrage R0,10/R0,25/R0,35 sont remplacés par un profil polygonal à l'intérieur de l'enveloppe nominale. L'épaisseur métallique nominale de 0,12 mm est une interprétation simplifiée du dessin et ne doit pas servir à produire un outillage de formage. Les fenêtres optiques sont des repères visuels estimés, affleurants à l'intérieur du corps. Le STEP représente les dimensions nominales ; ce n'est pas un modèle des tolérances maximales ni un fichier fabricant.

Les pastilles cuivre de la nouvelle empreinte sont une proposition de land pattern du projet, calculée autour des pieds réels ; la fiche Everlight ne fournit pas de land pattern recommandé. Il faut les faire accepter par l'assembleur, particulièrement avec les tolérances générales élevées de la fiche et l'assemblage Bottom.
