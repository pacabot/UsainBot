# Vérification mécanique de l'assemblage final

**Résultat : aucune intersection volumique entre composants de références différentes, ni entre composants et FR4, dans le STEP corrigé.** Cette conclusion porte sur les géométries modélisées. Les cotes photo de l'ESC, le support proposé, les fils et le futur collier de turbine restent à qualifier physiquement.

Assemblage contrôlé : `final-assembly-s17-mated.step`, export natif KiCad après correction du boîtier des 12 capteurs, avec prise batterie accouplée et tous les modèles activés. Export sans modèle manquant. Rapport reproductible : `final-s17-3d-collisions.json`, généré avec FreeCAD/OpenCascade par `audit_step_collisions.py` à partir de `final-3d-manifest.json`.

## Portée de l'audit

- 355 instances de modèle associées à leur référence ; zéro modèle non identifié et zéro référence munie d'un modèle absente de l'export.
- Tous les couples de références différentes examinés par leurs boîtes englobantes ; 160 couples candidats contrôlés par intersection exacte des solides.
- Zéro volume d'intersection positif. Les composants d'une même référence peuvent se toucher volontairement : pièces d'un moteur, broches dans plastique, support de module, etc. Ils ne sont pas comptés comme conflits inter-composants.
- Contrôle complémentaire des distances exactes autour de J102/J103, des trois ensembles moteurs/turbine, et des 12 associations capteur Bottom / LED Top.

## Dégagements nominaux mesurés

| Ensemble | Obstacle | Distance minimale |
|---|---|---:|
| ESC J103 + berceau | Composant le plus proche R112 | 1,150 mm |
| ESC J103 + berceau | Moteur M1 complet | 4,826 mm |
| ESC J103 + berceau | Moteur M2 complet | 19,986 mm |
| ESC J103 + berceau | Turbine M3 actuelle | 7,300 mm |
| ESC J103 + berceau | USB J101 | 3,750 mm |
| ESC J103 + berceau | Réserve conservative de futur collier | 0,844 mm |
| Batterie J102 accouplée | Composant le plus proche C354 | 2,680 mm |
| Batterie J102 accouplée | Moteur M2 complet | 4,387 mm |
| Batterie J102 accouplée | Turbine M3 actuelle | 11,198 mm |
| Batterie J102 accouplée | Réserve conservative de futur collier | 4,301 mm |
| Moteur M1 complet | Turbine M3 actuelle | 1,710 mm |
| Moteur M2 complet | Turbine M3 actuelle | 1,710 mm |
| Moteur M1 complet | Moteur M2 complet | 26,400 mm |

Le STEP turbine actuel ne contient **pas de collier séparé**. Le générateur d'empreinte décrit ce collier comme restant à concevoir. L'obstacle ajouté à l'audit est un anneau conservateur, rayons 18,35..23,75 mm, sur toute la hauteur de l'ESC de Z=0..17 mm au-dessus du datum Top. Il sert à anticiper l'encombrement ; le résultat de 0,844 mm ne qualifie ni la forme, ni la rigidité, ni la visserie future. Les têtes de vis héritées qui produisent deux remarques 2D ne sont pas des solides du STEP actuel ; leur réservation 2D demeure à respecter et vérifier.

L'OLED et ses entretoises, les trois télémétries, les composants Top et les capteurs Bottom sont inclus dans l'examen global. Des boîtes englobantes peuvent se recouvrir alors que leurs solides restent séparés ; ce cas ne constitue pas une collision mécanique.

## Capteurs de ligne : défaut hérité corrigé

L'audit initial avait trouvé **12 intersections de 2,682225 mm³** entre les anciens modèles ITR8307 et le FR4. Le modèle et les pastilles correspondaient à une variante à longue portée et fenêtre, tandis que la BOM spécifie déjà ITR8307/S17/TR8(B), C81632. La correction utilise la fiche constructeur exacte et conserve les centres, angles, faces Bottom et verrous.

Avec les nouveaux S17, chacun des douze capteurs présente dans l'export :

- corps plastique → FR4 : **0,205 mm** ;
- pieds → FR4 : **0,085 mm**, égal au datum de modèle Bottom utilisé par l'export ;
- séparation nominale corps / plan des pieds : **0,120 mm**, selon la fiche Everlight ;
- capteur → LED associée au même XY sur Top : **1,800 mm**, avec la carte entre les deux ;
- aucun volume de capteur dans le FR4, ni dans la LED.

La face optique occupe Z=−1,705 mm dans cet export (datum Bottom Z=−0,085 mm). Le boîtier nominal atteint 1,62 mm depuis le plan de soudure ; sa hauteur maximale calculée avec tolérances est 1,87 mm. Les sources, détails de boîtier et limites des simplifications sont dans `sensor-sources/README.md`.

## ESC vertical : pins, pastilles et puissance

Le modèle ESC est déjà vertical à 90° ; le bord inférieur du PCB de l'ESC est situé à 2 mm au-dessus du datum de montage Top. Le STEP définit le PCB ESC dans un plan XZ, hauteur 15 mm, largeur 11 mm. Le berceau isolant maintient cette hauteur tout en laissant accessibles les pastilles et les trois sorties moteur au bord supérieur. Sa profondeur de pieds a été réduite de 0,75 mm pour dégager la réserve du collier.

`esc-internal-3d-check.json` confirme que les trois pins sont tangentes à leurs pastilles ESC modélisées, sans pénétrer le FR4 ESC (distance au substrat 0,05 mm). Cette tangence géométrique requiert un vrai congé de soudure ; elle n'est pas une validation de sa résistance mécanique. Les pins occupent Z=−2,2..4,15 mm dans le repère du modèle. Elles traversent les vrais perçages de la carte sans collision dans l'export final.

| Pad | Fonction | Pin cuivre plein | Perçage | Cuivre PCB | Couronne nominale |
|---|---|---:|---:|---:|---:|
| 1 | GND puissance | Ø1,2 mm | Ø1,4 mm | 3,0 mm carré | 0,8 mm minimum |
| 2 | SIGNAL | Ø0,6 mm | Ø0,8 mm | Ø1,6 mm | 0,4 mm |
| 3 | +BATT brut / VPACK | Ø1,2 mm | Ø1,4 mm | Ø3,0 mm | 0,8 mm |

Le jeu radial pin/perçage est nominalement 0,1 mm ; les tolérances de fabrication et métallisation doivent être indiquées à l'assembleur. Les deux locateurs isolants Ø1,5 passent dans des NPTH Ø1,7. `final-pad-drill-readback.json` relit les valeurs réellement présentes sur la carte et confirme les nets GND, ESC_SIG et VPACK.

Une pin de cuivre Ø1,2 mm offre **1,131 mm²**. Pour 6,35 mm de longueur, sa résistance calculée à 20 °C est **0,0968 mΩ**, soit environ **14 mW à 12 A** et **22 mW à 15 A**, par pin. Ce calcul ne qualifie pas les contacts soudés, l'adhésion des pads, le réchauffement ambiant ni le cuivre de la carte. Les plans et liaisons de puissance ne sont pas routés à ce stade ; aucune capacité en courant du routage n'est déclarée validée.

Les positions de pastilles ESC, épaisseur de son PCB et composants dépassants restent des **estimations explicites**. Vérifier sur exemplaire réel le brochage, la continuité entre les deux pads GND, les cotes, la gaine retirée, les congés de soudure, l'échauffement en charge, la rétention du support et les dégagements des fils moteur. Le rapport `esc-research.md` détaille les sources et incertitudes.
