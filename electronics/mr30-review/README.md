# Remplacement du connecteur batterie par AMASS MR30 — 7 septembre 2026

Le projet principal a été modifié : **J102 = AMASS MR30PB-M30.G.Y**, embase verticale mâle à queues de 3 mm ; côté pack **MR30-F.G.Y**, femelle à souder, capot optionnel **98023.PG**. Le pack 2S reste commun à la carte, aux deux moteurs DC et à l'ESC. Aucun routage ajouté.

## Brochage et faisceau

| Pad du projet | Net | Fil proposé | Position locale X sur le PCB vu du dessus |
|---|---|---|---:|
| 1 | GND / BATT− | AWG16 cuivre multibrin | +3,50 mm |
| 2 | PACK_MID / point milieu 1S | AWG24 cuivre multibrin | 0 mm |
| 3 | VPACK / BATT+ | AWG16 cuivre multibrin | −3,50 mm |

Cette numérotation est **une convention du projet**, pas un brochage batterie universel MR30. La sérigraphie repère explicitement `3:+`, `2:MID`, `1:GND`. Identifier les cavités correspondantes de la femelle par accouplement à une embase hors tension et contrôle de continuité ; les vues face d'accouplement et côté fils sont en miroir. Les contacts femelles côté batterie évitent des broches mâles exposées sous tension. La soudure de l'AWG24 dans la terminaison prévue pour un fil plus gros nécessite une retenue mécanique du faisceau.

## Courants et pertes

Budget conservateur retenu : ESC **12 A continus / 15 A pointe**, moteurs DC **2 × 1 A réels** confirmés par l'utilisateur, provision électronique **1,5 A côté batterie**, soit **15,5 A continus / 18,5 A pointe**. Les courants ESC et électronique sont des enveloppes, pas des mesures. Les seuils de limitation des drivers DC restent inchangés ; un blocage moteur peut dépasser le budget réel fourni.

AMASS indique **20 A maximum avec AWG16 et élévation de température jusqu'à 85 K**, pas 30 A continus. Cette condition constructeur est élevée : l'intégration est dimensionnée pour essais, sans qualification thermique du robot à ce stade. La longueur courte réduit les pertes des fils, pas celles des contacts.

Hypothèse explicite : **5 cm par conducteur de puissance**, cuivre à 20 °C, section nominale AWG16 **1,309 mm²**. Avec rho = 0,017241 Ω·mm²/m, la résistance aller-retour vaut **1,317 mΩ**. Pour les contacts, calcul prévisionnel avec **1,5 mΩ par voie accouplée** d'après la fiche MR30 2023V1, à confirmer sur le couple PCB/femelle acheté ; la fiche d'embase indique ≤1,2 mΩ sans détailler ici les conditions de mesure du couple mixte.

| Pertes calculées, hors soudures et cuivre PCB | À 15,5 A | À 18,5 A |
|---|---:|---:|
| Deux fils AWG16, total 10 cm | 0,316 W / 20,4 mV | 0,451 W / 24,4 mV |
| Deux contacts, total 3 mΩ retenus | 0,721 W / 46,5 mV | 1,027 W / 55,5 mV |
| Total prévisionnel | **1,04 W / 66,9 mV** | **1,48 W / 79,9 mV** |

À 10 cm par conducteur, les pertes des fils doublent. Une longueur effective, une isolation et un environnement différents imposent de reprendre cette vérification. Le point milieu ne transporte pas le courant de propulsion ; le réseau de mesure/équilibrage et **R107 = 47 Ω / 1 W** sont conservés. À environ 88 mA, 5 cm AWG24 dissipent moins de 0,04 mW. Le choix des cellules, l'autonomie, les protections du pack et le profil de recharge ne sont pas qualifiés par ce remplacement de connecteur.

## Empreinte et modèle 3D

Empreinte : `Pacabot:AMASS_MR30PB-M_1x03_P3.50mm_Vertical`.

- Dessin mécanique figé : **AMASS MR30PB 2021V1**, dimensions corps **11,9 × 5,3 × 10,4 mm**, queues de 3 mm ; bride de **12,3 mm** mesurée sur le STEP.
- Entraxes : **3,50 mm**, tolérance fabricant ±0,05 mm. Trous finis : **Ø1,80 mm**, dessin +0,20/0. Respecter cette tolérance après métallisation.
- Pastilles puissance : **3 × 3 mm** (GND carrée, VPACK ronde), trou 1,8 mm, anneau nominal 0,6 mm. MID : diamètre 2,5 mm, anneau nominal 0,35 mm. Cuivre résiduel nominal entre pastilles voisines : 0,75 mm.
- Connexion des pads aux futures zones cuivre : pleine, sans freins thermiques. Aucune zone, piste ou via n'a été ajouté. L'épaisseur de cuivre, la métallisation des trous et les futurs chemins de puissance restent à dimensionner au routage ; ces pads seuls ne certifient pas le chemin complet à 20 A.
- F.CrtYd : **13,6 × 7,0 mm**, contre 21,26 × 13,4 mm pour l'ancienne réservation Mega-Fit, soit **66,6 % de surface en moins**.
- J102 est centré en **(174,7 ; 129,1) mm**, orientation 0°, Top. L'origine est maintenant la broche centrale, à la position de l'ancienne broche centrale. Les deux anciens trous de positionnement Mega-Fit sont supprimés.

Le STEP existant du **MR30PB-M exact**, publié par Lucidar, a été contrôlé face au dessin puis transformé sans mise à l'échelle : rotation X −90°, translation (0 ; 5,85 ; −0,75) mm. Origine au plan d'appui sur PCB, haut du corps Z=10,4 mm, extrémités des queues Z=−3 mm. Les trois queues de diamètre 1,6 mm sont centrées dans les trous de 1,8 mm. Le fichier intégré est `kicad-lib/3d/AMASS_MR30PB_M_Vertical.step`. La provenance constructeur du fichier CAO n'est pas certifiée ; ses dimensions ont été comparées au dessin constructeur archivé.

Le STEP Lucidar est un solide unique, plastique et contacts fusionnés, donc gris uniforme dans KiCad. Pour rendre les deux matières, `build_mr30.py` sépare les contacts par géométrie avant l'export : outil cylindrique Ø2,60 mm sur chaque axe, de z −3,05 à 0 (queues Ø1,6) et de z 3,4 à 10,5 (épaulement Ø2,5 puis balle Ø1,9 au-dessus du plancher de cavité). La paroi plastique la plus proche étant le fût Ø3,5, l'outil ne mord jamais dedans. Le tronçon de broche noyé entre z 0 et 3,4 reste dans le corps : il est invisible et le corps demeure un seul solide. Le générateur vérifie que la découpe conserve le volume et l'enveloppe du solide d'origine, puis injecte les couleurs AP214 : corps **jaune (0,95 ; 0,78 ; 0,10)**, contacts **doré (0,83 ; 0,68 ; 0,21)**, mêmes teintes que le XT30U-M du projet, cohérentes avec la référence **MR30PB-M30.G.Y** (contacts dorés, corps jaune). C'est un habillage de rendu : aucune dimension, position ni réservation n'est modifiée, et la teinte réelle de la pièce livrée n'est pas une donnée vérifiée par ce projet. Les images `board-3d.png` et `rear-3d.png` datent d'avant cette mise en couleur et montrent encore l'embase en gris.

Le STEP de la femelle avec capot mesure environ **12,465 × 5,515 × 14,5 mm**. La profondeur exacte d'accouplement n'étant pas documentée, la copie de contrôle ajoute une **réservation conservative de 12,6 × 5,7 mm jusqu'à 24,9 mm au-dessus du PCB**, sans retrancher de profondeur d'insertion. Le bloc gris de `rear-3d.png` est cette réserve, **pas une représentation de la femelle réellement emboîtée**. Le projet principal utilise uniquement le modèle réel de l'embase. Prévoir en plus le dégagement des fils vers le haut ; rayon de courbure et traction ne sont pas simulés.

La page AMASS actuelle présente aussi une révision de corps 11,7 × 5,3 × 10,6 mm. Ne pas confondre les révisions : confirmer le dessin de la pièce livrée avant fabrication. Les entraxes et trous publiés sont identiques, mais l'enveloppe 3D retenue correspond à 2021V1.

## Modifications et contrôles

Schéma `01-power.kicad_sch` : valeur, empreinte, datasheet et champs d'approvisionnement J102 remplacés. Les fils, UUID du symbole et nets sont conservés. Générateurs `tools/integration_blocks.py` et `tools/design.py` mis à jour pour éviter de réintroduire le Mega-Fit. PCB réellement synchronisé depuis la nouvelle netlist KiCad ; seule l'empreinte J102 est remplacée.

- Comparaison avec `before-mr30.zip` : **339 autres empreintes inchangées** en position, angle, face, verrouillage, UUID et type ; les **36 composants verrouillés** restent intacts. Tous les nets de toutes les pastilles et tous les nœuds électriques du schéma sont identiques.
- ERC : **0 anomalie**.
- DRC : **0 erreur de violation**, **146 avertissements préexistants** (sérigraphie et écarts bibliothèque), **0 divergence schéma–PCB**. **499 connexions restent à router**, comme avant ; cela n'est pas un PCB prêt à fabriquer.
- Vérification indépendante : **1 064 pastilles numérotées**, aucune discordance de net, 340 composants, 328 Top / 12 Bottom ; 0 piste, 0 via, 0 zone.
- Géométrie : aucun conflit nouveau pour J102 ; les 6 débordements de courtyards et 2 contraintes autour de perçages appartenant aux placements verrouillés préexistent et sont inchangés. Aucune pastille hors carte.
- Assemblage STEP complet : **355 instances de modèles, aucune non identifiée, aucune intersection volumique entre références distinctes**. L'embase et la réservation de fiche sont sans collision avec PCB, turbines et autres composants ; composant le plus proche C354, **5,45 mm** de distance 3D. Les limites de fiabilité des modèles mécaniques précédents, notamment ESC estimé, restent applicables.
- Inspection visuelle effectuée sur les rendus KiCad de la carte complète et de la zone arrière. Les ultimes corrections de taille/texte de sérigraphie n'affectent pas la géométrie STEP auditée.

Rapports : `erc-final.json`, `drc-final.json`, `revision-diff.json`, `integration-verification.json`, `geometry-final.json`, `collisions-final.json`. Images : `board-3d.png` (carte principale), `rear-3d.png` (avec réserve de fiche). Schéma consultable : `schematic-final.pdf`. Sources et sauvegarde avant modification conservées dans ce dossier.

## Sources et validations physiques restantes

- [Dessin AMASS MR30PB 2021V1, copie archivée par Lucidar](https://lucidar.me/en/electronics/files/mr30pb-m.pdf).
- [Fiche AMASS MR30 2023V1 : MR30-F.G.Y, 20 A/AWG16/85 K, résistance de contact](https://www.china-amass.com/public/upload/20240530/db4152b756868052d42c3b96b5a13c21.pdf).
- [Modèles CAD exacts MR30PB-M et MR30-F publiés par Lucidar](https://lucidar.me/en/electronics/connector-mr30/), copies STEP dans `sources/`.
- [Page AMASS MR30PB-M actuelle](https://www.china-amass.com/biao/632.html), révision de dimensions à distinguer du modèle 2021V1.

Avant fabrication/sous tension : confirmer la révision et les dimensions livrées, contrôler la polarité du faisceau à l'ohmmètre, vérifier l'ajustement et la retenue mécanique, puis mesurer l'échauffement des contacts/soudures/fils au courant réel et la réponse en surcharge. Le routage de puissance et la qualification du pack restent des étapes distinctes.
