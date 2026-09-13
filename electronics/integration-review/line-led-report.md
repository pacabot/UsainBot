# Alignement des 12 LED de ligne

> Rapport de préparation conservé pour traçabilité. L'intégration est
> maintenant appliquée au projet principal : consulter [le rapport final](README.md).
> La correction ultérieure des capteurs S17, les résultats ERC/DRC et
> l'audit 3D final remplacent les métriques intermédiaires ci-dessous.


Les LED D401–D412 sont placées en Top **exactement à l’aplomb** de U401–U412 en Bottom. Le centre XY est strictement identique, sans déplacement des capteurs verrouillés. L’angle KiCad de chaque LED vaut l’angle du capteur + 90° : les axes longs des deux boîtiers coïncident. Les anodes regardent toutes vers l’intérieur du PCB. Les douze couples conservent la symétrie existante autour de x = 155 mm ; le résidu de 0,000001 mm vient de l’arrondi initial des capteurs et n’est pas corrigé en déplaçant ceux-ci.

Les résistances de LED R445–R456 sont sur le même axe radial, à 2,80 mm vers l’intérieur, avec leur pad 2 près de l’anode. Les douze cellules reproduisent aussi exactement les positions locales des résistances IR, charges de phototransistor et capacités de filtrage. Ce réagencement libère les LED sans sacrifier les connexions analogiques : centre du pad capteur 4 → pad C1 = 1,325 mm ; capteur 4 → Rcharge1 = 1,018 mm ; capteur 2 → RIR2 = 0,190 mm en projection XY entre Top et Bottom. Il ne s’agit pas de pistes déjà routées. Les vias seront à placer hors pads CMS sauf procédé adapté.

D606 (LED bleue IHM) est recentrée entre les capteurs 05/06, et R615 la suit. Q602 et R619/R620 sont déplacés dans l’espace disponible derrière la rangée pour libérer D408. Le témoin bleu garde son rôle distinct des témoins verts de ligne. Total : **65 composants mobiles**, aucun verrou modifié, aucun net modifié, aucune piste ni via ajouté.

## Correspondance électrique vérifiée

Les feuilles 04-line-array et 08-line-leds et la netlist exportée sont cohérentes avec tous les pads concernés du PCB. Les LED sont pilotées par le PCA9685 U105 : il n’existe pas de connexion analogique directe entre LINE_i et LGNi. L’association fonctionnelle capteur → PWM du témoin est donc à respecter aussi dans le firmware (canal i vers témoin i). Le schéma est déjà correctement indexé et ne nécessite aucune correction de connexion sur cette partie.

| Index | Capteur / net ADC | STM32 pin | LED | PCA9685 pin / canal | Résistance |
|---|---|---:|---|---|---|
| 00 | U401 / LINE_00 | 34 | D401 | 6 / 0 | R445 |
| 01 | U402 / LINE_01 | 35 | D402 | 7 / 1 | R446 |
| 02 | U403 / LINE_02 | 36 | D403 | 8 / 2 | R447 |
| 03 | U404 / LINE_03 | 37 | D404 | 9 / 3 | R448 |
| 04 | U405 / LINE_04 | 40 | D405 | 10 / 4 | R449 |
| 05 | U406 / LINE_05 | 41 | D406 | 11 / 5 | R450 |
| 06 | U407 / LINE_06 | 42 | D407 | 12 / 6 | R451 |
| 07 | U408 / LINE_07 | 43 | D408 | 13 / 7 | R452 |
| 08 | U409 / LINE_08 | 46 | D409 | 15 / 8 | R453 |
| 09 | U410 / LINE_09 | 47 | D410 | 16 / 9 | R454 |
| 10 | U411 / LINE_10 | 44 | D411 | 17 / 10 | R455 |
| 11 | U412 / LINE_11 | 45 | D412 | 18 / 11 | R456 |

Chaque LED : pad 1 = cathode LGNi, pad 2 = anode LGNi_A ; R445+i.2 = LGNi_A, R445+i.1 = +3V3. Les douze capteurs utilisent leur pad 4 pour LINE_i. Aucun échange d’index n’a été détecté.

## Contrôles

Application testée par pcbnew 10 sur `/tmp/usainbot-ledcheck/UsainBot.kicad_pcb`, sans toucher au PCB principal. Les courtyards réels ont été réexportés **après** transformation KiCad et analysés avec Shapely, en tenant compte des faces, du contour et des perçages. Tous les composants déplacés sont exempts de conflit. Le minimum entre leurs courtyards et un autre courtyard Top est **0,210 mm** (Q602/R619). Les courtyards LED restent à **2,420 mm minimum du bord PCB**.

DRC natif sur le projet temporaire, avec les règles existantes : **aucune nouvelle erreur cuivre/courtyard, aucune divergence schéma–PCB**. Il subsiste uniquement les deux erreurs initiales J103/J702 (deux verrous de la zone ESC), que l’intégration ESC pourra traiter séparément. 499 connexions restent non routées. Les 149 avertissements sont de sérigraphie, hauteur de texte et correspondance bibliothèque ; cette sous-tâche ne déclare pas la carte complète prête à fabriquer. Les huit débords initiaux de courtyards verrouillés, dont les capteurs extrêmes Bottom, et les réserves mécaniques initiales sont conservés et documentés par l’audit global. La géométrie de la rangée a été inspectée dans la figure Top/Bottom superposée. La vue 3D de l’assemblage fusionné reste à contrôler lors de l’intégration générale.

## Fichiers à intégrer

- `line-led-positions.json` : positions **figées**, géométrie locale, 12 associations et métriques. Les LED ne doivent pas être déplacées par un solveur généraliste après application.
- `apply_line_led_positions.py` : application contrôlée sur une copie ou via `apply_positions(board, data)` ; vérification des positions initiales, verrous, nets, pistes et zones.
- `line-led-geometry-validated.json`, `line-led-drc-validated.json` : preuves de contrôle sur la copie réellement écrite par KiCad.
- `line-led-alignment.png` et `.pdf` : revue géométrique ; `render_line_led_alignment.py` produit ces vues depuis la géométrie validée.

Le PCB principal et les schémas n’ont pas été modifiés par cette sous-tâche. La table doit être appliquée par l’intégration générale, puis les contrôles globaux relancés sur le résultat fusionné.
