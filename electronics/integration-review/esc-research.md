# EMAX Bullet 12A EMX-SC-1873 — recherche et montage vertical provisoire

Le modèle retenu est strictement l’**EMAX D-SHOT Bullet Series 12A BLHeli-S, EMX-SC-1873**. Aucun modèle d’un autre courant n’a servi aux mesures ou à la CAO. Le montage proposé reste un **prototype à vérifier sur un ESC réel** : aucune source trouvée ne fournit le dessin coté des pads, leurs tolérances, l’épaisseur du PCB ou l’enveloppe complète.

## Sources et fichiers

1. [EMAX Model, produit 12A BLHeli-S](https://emaxmodel.com/products/emax-d-shot-bullet-series-12a-2-4s-blheli_s-esc-2-4g-support-onshot42-multishot). Source constructeur ; photos `emaxmodel-img_6289.jpg` (emballage), `emaxmodel-img_6290.jpg` / `emaxmodel-img_6291.jpg` (face logique), `emaxmodel-img_6293.jpg` (face MOSFETs/capacités), 800 × 800 px, vues obliques. La brochure constructeur `emaxmodel-__06.jpg` donne pour la ligne **12A** : 11 × 15 mm, 12 A continu, 15 A crête, 2–4S, 2,4 g sans fils et sans BEC. Les autres images de brochure montrent surtout les 6/35 A et **sont exclues des mesures**.
2. [EMAX USA, page portant EMX-SC-1873](https://emax-usa.com/products/d-shot-bullet-series-12a-esc-blheli-s). Confirme la référence commerciale et présente les mêmes photos historiques. Attention : la page actuelle redirige vers `shop.emax-usa.com` et parle désormais d’AM32 malgré l’URL BLHeli-S et des photos étiquetées BLHeli-S. La page EMAX Model et la brochure restent les références du matériel demandé ; ne pas présumer qu’une nouvelle révision commerciale possède le même PCB.
3. [Joe Earlam / IrregularJoe, prise de vue personnelle d’un Emax Bullet 12A](https://forum.bristolbotbuilders.com/t/guide-how-to-solder-robots-good/725/2), 4 juin 2026. **Source primaire indépendante** : l’auteur photographie l’ESC qu’il soude et l’identifie comme Bullet 12A ; sa disposition correspond aux photos EMAX. `bbb-DSCF9865.jpeg`, **1920 × 1579 px**, montre la face puissance presque perpendiculairement avec une règle. [Original](https://forum.bristolbotbuilders.com/uploads/default/original/2X/3/3e05c80167257fcc27fb402b9c36b51d05a24e8c.jpeg). `bbb-DSCF9866.jpeg` montre la gaine ; `bbb-tinning-0.webp` et `-1.webp` sont ses clips de soudure. La source constate aussi le risque d’arrachement des pads CMS lorsqu’ils reprennent les efforts des fils.
4. [TME, EMX-SC-1873](https://www.tme.eu/en/details/esc-bullet-12a/controllers/emax/emx-sc-1873/) confirme l’identité ; son lien « Documentation » conduit uniquement au [manuel générique du firmware BLHeli](https://www.tme.eu/Document/565a6d126189bb1b31b17819c38dcc5c/Bullet%2Bfirmware%2Binstruction.pdf), sans plan mécanique du 12A. Il ne constitue pas une cote de fabrication.
5. [NIST, Copper Wire Tables](https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook100.pdf), résistivité cuivre recuit à 20 °C : 1,7241 × 10⁻⁸ Ω·m, employée seulement au calcul ohmique ci-dessous.

Les téléchargements et captures HTML se trouvent dans `integration-review/esc-sources/`. Les recherches constructeur, documentation, GrabCAD et recherches exactes « EMAX Bullet 12A / EMX-SC-1873 STEP STP CAD » n’ont pas identifié de modèle STEP exact fiable. Elles n’établissent pas qu’aucun modèle privé n’existe.

## Brochage visible et limites

Sur la face MOSFETs/capacités, le bord d’entrée porte **quatre pads CMS** : gros GND puissance, petit GND de référence du signal, SIGNAL, gros +BATT. Cette identification est une **interprétation des fils constructeur visibles** (gros noir, petit noir de la paire torsadée, blanc, rouge) ; aucun dessin de brochage coté EMAX n’a été trouvé.

Le montage trois pins emploie exclusivement le **gros GND**, le SIGNAL et le +BATT. La continuité entre petit GND et gros GND n’a pas pu être mesurée : **la vérifier physiquement avant d’omettre le petit fil de masse**. Si ces points ne sont pas communs, trois connexions ne suffisent pas ; ajouter le retour logique séparé ou un petit adaptateur. Le petit pad de masse logique ne doit pas porter 12 A.

Les trois pads moteur sont sur le bord opposé. Les noms MOTOR_A/B/C sont une convention du projet : aucune sérigraphie constructeur A/B/C n’est documentée. Vérifier le sens du moteur lors de sa configuration.

## Mesure géométrique

L’homographie de `esc-sources/measurement-photo-estimates.json` transforme quatre coins sélectionnés manuellement sur `bbb-DSCF9865.jpeg` vers le rectangle constructeur **11 × 15 mm**. Repère vu de face MOSFETs : x traverse la largeur du gros GND vers +BATT ; z parcourt les 15 mm depuis le bord d’entrée vers le bord moteur ; x=0 au milieu du bord d’entrée. La règle visible permet un contrôle qualitatif de l’échelle, sans servir d’étalon métrologique.

| Point | x mesuré, mm | Distance au bord d’entrée, mm |
|---|---:|---:|
| Gros GND | −4,303 | 1,154 |
| Petit GND logique | −0,826 | 1,114 |
| SIGNAL | +0,803 | 1,078 |
| +BATT | +4,419 | 1,038 |
| Moteur côté GND | −4,096 | 14,594 |
| Moteur central | +0,232 | 14,318 |
| Moteur côté +BATT | +4,496 | 14,136 |

**Ces nombres sont des résultats intermédiaires de calcul, pas des cotes à trois décimales garanties.** L’incertitude indicative conservatrice retenue est **±0,4 mm**, sans statut de tolérance ni d’intervalle statistique. Causes : cuivre couvert d’étain, sélection des coins et centres, perspective résiduelle et déformation optique, différence entre contour physique et dimensions nominales sans tolérances. Les trois entrées utiles sont compatibles avec une ligne commune à environ 1,1 mm du bord ; leur écart longitudinal de 0,116 mm est inférieur à l’incertitude.

Pour le prototype : x = **−4,30 / +0,80 / +4,42 mm** ; entraxes projetés **5,10 / 3,62 mm**, aucun pas 2,54 mm supposé. Les pads de puissance sont modélisés **2,0 × 1,7 mm**, le signal **1,0 × 1,0 mm**, dimensions **estimées** de la zone de soudure ; contours de cuivre réels masqués.

## Empreinte créée et pins

`Pacabot:EMAX_Bullet_12A_Vertical_3Pin_PROTOTYPE`

| N° | Fonction | x/y empreinte, mm | Pin cuivre plein | Trou fini | Pad PCB principal |
|---|---|---|---|---|---|
| 1 | GND puissance | −4,30 / 0 | Ø1,2 mm | Ø1,4 mm | 3 × 3 mm carré |
| 2 | SIGNAL | +0,80 / +0,30 | Ø0,6 mm | Ø0,8 mm | Ø1,6 mm |
| 3 | +BATT | +4,42 / 0 | Ø1,2 mm | Ø1,4 mm | Ø3,0 mm |

Le décalage **y=+0,30 mm** du signal est une décision d’assemblage explicitée : les rayons 0,6/0,3/0,6 mm demandent des axes différents pour être tangents à **la même face verticale**. Il ne représente pas un décalage arbitraire des pads ESC. Les trois pins métalliques se soudent en recouvrement sur les pads CMS ; l’ESC ne possède pas les trous correspondants.

Les 0,2 mm de jeu diamétral sont des choix de perçage **fini**, à confirmer avec les tolérances de fil, placage et fabrication. Anneau puissance nominal 0,8 mm. Connexion directe aux zones, `zone_connect 2`, sans étranglement de relief thermique. Aucun via ni routage ajouté. Le futur cuivre doit être dimensionné et raccordé aux deux faces ; les trous métallisés ne dispensent pas du calcul du chemin complet.

Deux NPTH Ø1,7 mm, x=±7 mm, y=+1,2 mm, reçoivent des tétons isolants Ø1,5 mm du support proposé. Courtyard **16,8 × 7,6 mm**, contour ESC/support sur F.Fab, repères GND/SIG/+BAT et flèche vers la face accessible sur F.SilkS.

## Courant : vérification limitée, pas qualification thermique

Les deux pins de puissance sont du **cuivre plein étamé**, pas des broches de barrette en laiton. Section Ø1,2 mm : **1,131 mm²**. Pour 6,35 mm de longueur métallique, R=ρL/A ≈ **0,097 mΩ** à 20 °C. P≈**14 mW à 12 A** et **22 mW à 15 A par pin** (hors soudures, interfaces, cuivre du PCB et échauffement provenant de l’ESC).

Ce calcul confirme que la résistance du corps de la tige est faible ; **il n’attribue pas un courant admissible certifié au montage**. Il manque la surface réelle mouillée, la qualité des soudures, les propriétés mécaniques après brasage, l’empilage cuivre de la carte et la température ambiante/refroidissement. Le prototype exige un essai thermique à 12 A continu et au régime réel des pointes 15 A, avec mesure sur les soudures et pads. Ne pas remplacer silencieusement le cuivre plein par un matériau de broche différent.

## CAO FreeCAD Part Design

Fichiers créés :

- `kicad-lib/3d/EMAX_Bullet_12A_Vertical_PROTOTYPE.FCStd`
- `kicad-lib/3d/EMAX_Bullet_12A_Vertical_PROTOTYPE.step`
- `integration-review/build_emax_bullet12a.py`
- `integration-review/esc-dimensions-prototype.json`

Le document comprend **27 solides Part Design** à base de primitives additives ; chaque corps porte des propriétés `DimensionalEvidence` et `ManufacturingStatus`. Le STEP est **déjà vertical à 90°** ; transformation d’empreinte (0,0,0), sans appliquer une seconde rotation. Convention KiCad : Y du STEP = −Y de l’empreinte, Z=0 au dessus du PCB principal. Le bord d’entrée de l’ESC est à **Z=2,0 mm**, le sommet à **Z=17,0 mm**. Les pins descendent à −2,2 mm ; tétons du support à −2,5 mm.

Cotes documentées : 11 × 15 mm. **Estimées** : épaisseur PCB 1,0 mm ; dépassement frontal maximal 1,8 mm, arrière 1,0 mm ; enveloppe électronique totale environ 3,85 mm ; positions et hauteurs simplifiées des CMS, dimensions des pads. Support isolant, garde de 2 mm, géométrie des tiges et tétons sont des **choix de conception**, pas des dimensions du produit EMAX.

La gaine d’origine est **retirée** pour cet assemblage soudé ; elle n’est pas incluse dans l’enveloppe. La remettre demande de réviser les jeux et le refroidissement. Les sorties moteur restent au sommet, sans obstacle au brasage ; la trajectoire et le rayon de courbure des fils devront être contrôlés sur le robot.

Les trois soudures sur pads CMS ne constituent pas à elles seules un maintien robuste sous vibrations : le modèle inclut un **petit berceau isolant**, appui sous la tranche, rail arrière et deux pieds/repères traversants. Retenue par adhésif qualifié ou sertissage thermique des tétons à définir physiquement, matériau résistant à la température à choisir. Ce berceau est une proposition mécanique du projet ; ses dimensions ne sont pas validées sur pièce.

Contrôles effectués ici : import de l’empreinte par pcbnew réussi ; dimensions/nombres de pads contrôlés ; export puis réimport STEP valide, **27 solides**, sommet 17 mm ; intersections volumiques pin ↔ berceau **nulles**. L’ERC, le DRC du PCB intégré et la collision avec les turbines relèvent de la revue de l’assemblage effectuée par l’agent principal. Cette recherche et cette CAO seules ne les déclarent pas validés.

## Vérifications physiques encore nécessaires

Mesurer au pied à coulisse/microscope les contours nus, centres, surfaces de pads, épaisseur FR4 et composants hauts ; contrôler la continuité des masses, les polarités et la correspondance du lot réel au BLHeli-S photographié ; réaliser un essai de soudure avec les tiges retenues ; qualifier thermiquement les deux liaisons de puissance ; vérifier le maintien sous vibrations, le matériau du berceau, l’accessibilité du fer, les fils moteur et leur dégagement réel avec turbines et châssis. **Ne pas lancer la fabrication à partir des seules cotes photographiques.**

## Complément : contrôle interne et candidats de montage

Contrôle FreeCAD après correction du modèle : les trois pins sont tangents à leurs pastilles (distance minimale 0 mm), aucun ne pénètre le FR4 de l’ESC (volume d’intersection 0 mm³). Les pads moteur du modèle sont, de GND vers +BATT, A=(−4,10 ; Z16,40), B=(+0,23 ; Z16,30), C=(+4,50 ; Z16,15), Z rapporté au dessus de la carte principale ; ils mesurent 1,7 × 1,2 mm estimés. Les positions restent dans ±0,4 mm des mesures photographiques et les rectangles restent dans le contour de l’ESC. A/B/C restent des noms de projet, pas une identification de phases imprimée par EMAX.

Le support isolant a été raccourci de **0,75 mm sur l’avant des deux pieds**, désormais de profondeur 2,85 mm. Les jeux ci-dessous incluent ce support compact. Le contour F.Fab a été actualisé ; le courtyard conserve son dégagement de brasage et d’accès.

Le STEP existant de la turbine M3 comprend `Fut`, `Redresseur`, `Rotor`, `Faisceau`, **aucun collier séparé**. Le générateur du projet décrit le collier comme une pièce restant à dessiner. Le contrôle de sa réserve utilise donc un **obstacle conservateur provisoire** : anneau extérieur R23,75, intérieur R18,35, hauteur Z0 à 17 mm au-dessus de la carte. Cette hauteur couvre tout le montage ESC pour un audit conservateur ; ce n’est pas une cote documentée de collier. Un futur collier ou ses vis plus hauts/plus grands nécessitera un nouvel audit.

| ESC x/y/angle KiCad | M1 complet | M2 complet | Turbine M3 | USB J101 | Réserve de collier |
|---|---:|---:|---:|---:|---:|
| 144 / 135 / 180° | 4,565 | 19,837 | 6,818 | 4,250 | 0,361 |
| 144 / 134,5 / 180° | 4,826 | 19,986 | 7,300 | 3,750 | 0,844 |
| 144 / 134 / 180° | 5,122 | 20,147 | 7,782 | 3,250 | 1,328 |

Toutes les valeurs sont des **distances minimales entre solides, en mm** ; toutes les intersections de ces paires valent 0 mm³. Ces positions sont des candidats : le rapport global indique celle effectivement intégrée et tient compte de C704 et des autres composants. Résultats reproductibles enregistrés dans `esc-candidate-3d-clearances.json`. La validation porte sur les enveloppes CAO disponibles ; les dimensions estimées du support, de l’ESC et du futur collier ne sont pas pour autant qualifiées pour fabrication.
