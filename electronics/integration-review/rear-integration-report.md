# Placement arrière : ESC et batterie

> Rapport de préparation conservé pour traçabilité. L'intégration est
> maintenant appliquée au projet principal : consulter [le rapport final](README.md).
> La correction ultérieure des capteurs S17, les résultats ERC/DRC et
> l'audit 3D final remplacent les métriques intermédiaires ci-dessous.


Le plan retenu remplace les connecteurs J102/J103 et supprime J104/J702. Il déplace seulement quatre composants déjà mobiles : C704, C705, U101 (protection USB) et Q101 (commande logique du chargeur). Le BQ25887, sa boucle de commutation, son shunt, ses condensateurs C101–C108, tous les moteurs, la turbine, l’USB et les autres verrous sont conservés. La rangée de LED déjà validée reste inchangée.

| Référence | X (mm) | Y (mm) | Angle KiCad |
|---|---:|---:|---:|
| J102 MegaFit | 169,00 | 129,10 | 0° |
| J103 ESC | 144,00 | 134,50 | 180° |
| C704 220 µF | 144,20 | 125,60 | 0° |
| C705 100 nF | 144,20 | 129,80 | 0° |
| U101 USBLC6 | 154,70 | 133,35 | 180° |
| Q101 AO3400A | 136,45 | 128,60 | 0° |

Le MegaFit regarde le bord arrière avec son verrou. L’origine géométrique à gauche est bien **la broche 3 fabricant VPACK**, et non la broche 1 : pad 2 au centre = point milieu ; pad 1 à droite = GND. La correction de numérotation fabricant est indépendante de la position mécanique, qui ne change pas.

C704 reste à 9,105 mm du pad +BATT de l’ESC et 9,009 mm de son pad GND (centres de pads). C705 se trouve entre le réservoir et les deux pads puissance : respectivement 6,263 et 5,932 mm. Le courtyard de montage vertical et ses pieds imposent ce retrait. Le futur bus VPACK/GND doit conserver un trajet large et direct dans ce petit ensemble ; ces distances ne constituent pas une validation thermique ou de chute de tension. Les nets finaux C704/C705 doivent être VPACK/GND, conformément au schéma mis à jour par l’intégration principale.

U101 reste entre les pads USB et le chemin vers le MCU. Q101 ne fait que piloter la commande logique CD du chargeur ; sa légère translation évite de réorganiser les condensateurs, la self et le shunt du chargeur. Une alternative strictement hors cercle indicatif avec ESC tourné de 90° a été examinée : elle exigeait de déplacer douze auxiliaires du chargeur et allongeait notamment le découplage VBUS. Cette alternative a été écartée au profit d’un berceau neuf compact et vérifié en 3D.

## Contrôles de placement

Les positions ont été appliquées sur une **copie temporaire** du PCB, puis les courtyards et trous réexportés par KiCad. Aucun nouveau conflit de courtyard, de perçage ou de contour ; aucune pastille hors carte. Clearance minimale entre courtyards pour les pièces modifiées : **0,200 mm**. MegaFit → M2 : **0,290 mm** ; MegaFit → C354 : **0,270 mm**. Les deux réserves NPTH restantes concernent les vis initiales de turbine contre les courtyards M1/M2 verrouillés ; les huit débords initiaux de courtyards verrouillés restent inchangés.

Le **courtyard** de l’ESC pénètre de 14,358 mm² dans le cercle indicatif de collier de rayon 23,75 mm. Ce cercle n’est pas supprimé ni assimilé au STEP de turbine. L’agent de contrôle mécanique a testé séparément les **solides** du nouveau berceau compact contre les moteurs, l’USB, la turbine et un anneau conservateur R18,35–23,75 mm / Z0–5,5 mm. Pour J103=(144;134,5;180°), les jeux communiqués sont : M1 4,826 mm ; M2 19,986 mm ; M3 7,300 mm ; USB 3,750 mm ; anneau conservateur 0,844 mm. Aucun volume d’intersection. Voir `esc-candidate-3d-clearances.json` pour la preuve de l’agent mécanique. La géométrie du futur collier reste à confirmer physiquement ; il serait incorrect de déclarer cette réserve entièrement validée par le DRC.

`rear-integration-positions.json` est le plan à fusionner. `rear-integration-geometry-validated.json` démontre les courtyards/perçages après écriture KiCad de la copie. La figure PNG/PDF montre les réserves. Les connecteurs et nets finaux doivent être synchronisés depuis le schéma par le parent, puis ERC, DRC et contrôle 3D de l’assemblage fusionné exécutés. Cette sous-tâche n’a pas modifié le PCB principal.
