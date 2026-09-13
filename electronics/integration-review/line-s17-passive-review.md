# Vérification des passifs après correction du boîtier ITR8307/S17/TR8(B)

**Conserver tous les placements de LED et passifs déjà validés.** La nouvelle empreinte `Pacabot:ITR8307_S17_TR8_Bottom` correspond à la variante S17 à pattes gull-wing. Elle ne nécessite aucune fenêtre dans le PCB. La fiche Everlight DRX-0000322 Rev.6 page 2 confirme le brochage 1 cathode, 2 anode, 3 collecteur, 4 émetteur ; voir la revue indépendante dans `sensor-sources` pour les dimensions et les choix de lands.

Les quatre pads se rapprochent du centre du capteur : y local ±2,11 mm au lieu de ±2,80 mm. Après retournement Bottom, le numéro de pad, le miroir et l’angle de chacun des douze capteurs restent cohérents. Le centre XY, l’angle et le verrou restent inchangés ; chaque LED Top demeure exactement à son aplomb avec angle = angle capteur + 90°.

| Liaison (centres des pads, projection XY) | Distance avec S17 |
|---|---:|
| Émetteur capteur .4 → C401+i .1 | 1,016 mm |
| Émetteur capteur .4 → R421+i .1 | 1,332 mm |
| Anode IR capteur .2 → R401+i .2 | 0,880 mm |

Ces distances sont identiques sur les douze voies à moins de 0,000002 mm d’arrondi. Les résistances IR restent près de l’anode ; le filtre et la charge restent groupés du côté émetteur/ADC. Aucune nouvelle translation de passif ne se justifie.

L’évaluation en lecture seule combine l’empreinte effectivement créée et les poses verrouillées du PCB courant. Les douze associations capteur LINE_i / LED LGNi restent correctes. Les nouveaux courtyards Bottom restent tous à l’intérieur du contour. Les nouvelles pastilles restent à au moins **0,965 mm** du bord extérieur en utilisant une enveloppe rectangulaire conservatrice des pads arrondis. Aucun nouveau perçage ni aucune fenêtre n’est nécessaire.

Preuve : `line-s17-passive-review.json`, produite par `check_line_sensor_s17_passives.py`. Aucun PCB ni aucune position de composant n’ont été modifiés par cette vérification. Le contrôle natif DRC et l’audit 3D de l’assemblage après remplacement sont à exécuter par l’intégration principale.

Source constructeur : https://www.everlighteurope.com/custom/files/datasheets/DRX-0000322.pdf
