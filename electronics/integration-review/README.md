> Mise à jour du 7 septembre 2026 : le Mega-Fit décrit dans ce compte rendu historique est remplacé dans le projet principal par le MR30. Voir [l’intégration MR30 actuelle](../mr30-review/README.md).

# Intégration KiCad — LED, EMAX Bullet 12A et batterie commune 2S

État enregistré le **6 septembre 2026** dans [le PCB principal](../UsainBot.kicad_pcb) et [le schéma principal](../UsainBot.kicad_sch). Les modifications sont appliquées et la netlist exportée du schéma a réellement été synchronisée avec le PCB. **Aucun routage n'a été effectué. L'interface ESC reste un prototype mécanique à mesurer avant fabrication.**

La batterie sera assemblée par l'utilisateur et alimentera toute la carte et l'ESC. Il n'existe donc pas de connecteur de pack déjà choisi à reproduire. Le connecteur commun et l'équilibrage sont intégrés ; la sélection des cellules, le profil de charge, la protection du pack et l'autonomie restent à définir.

## État et documents à ouvrir

- [Schéma complet PDF](schematic-final.pdf).
- [Vue 3D complète KiCad](3d-overview.png), [zone arrière](3d-rear.png), [montage ESC](3d-esc-mount.png), [face Bottom](3d-bottom.png).
- [Placement des douze témoins](line-led-alignment.png), [placement arrière](rear-integration-placement.png). Figures recalculées depuis la géométrie finale.
- [Assemblage STEP final](final-assembly-s17-mated.step), export natif KiCad incluant l'enveloppe de la prise batterie accouplée. La [copie de revue](assembly-mated.kicad_pcb) ajoute uniquement cette enveloppe au modèle de J102 ; le fichier de production du projet demeure `../UsainBot.kicad_pcb`.
- [Vérification nets/verrous/pads](integration-verification.json), [ERC](erc-final.json), [DRC](drc-final.json), [géométrie](geometry-final.json), [collisions 3D finales](final-s17-3d-collisions.json), [revue mécanique expliquée](mechanical-3d-validation.md).
- `before-integration.zip` sauvegarde le point de départ de cette intégration, après la reprise précédente du placement analogique/passifs. Les fichiers `*-validated`, `*-proposed` et les anciens STEP sans `s17` sont des étapes intermédiaires ; ils ne remplacent pas les résultats finaux ci-dessus.

## LED et capteurs de ligne

D401–D412 sont en Top, chacune **exactement au même centre XY** que son capteur Bottom U401–U412. Angle LED = angle capteur +90°, axes longs concordants, anodes vers l'intérieur. La géométrie répétée suit la symétrie existante, sans corriger par déplacement l'arrondi micrométrique des capteurs verrouillés. Les résistances de LED sont à 2,80 mm vers l'intérieur sur le même axe. Les résistances IR, charges de phototransistor et filtres suivent également une cellule locale identique. D606/R615 et Q602/R619/R620 dégagent la rangée. Au total, 65 placements mobiles ont été repris dans cette zone.

Correspondance contrôlée : U401+i / LINE_i / entrée STM32 et D401+i / LGNi / canal PCA9685 i, pour i=0…11. La LED est commandée par le PCA9685, pas directement par le signal analogique ; le firmware doit conserver cette même association. La [table complète](line-led-report.md) donne les broches.

Le contrôle 3D a révélé une erreur de variante héritée : `ITR8307_dessous` utilisait un modèle à ouverture PCB et des pattes espacées de 6,7 mm, alors que la nomenclature C81632 désigne **ITR8307/S17/TR8(B)** à pattes formées, portée 4,6 mm, sans ouverture. L'empreinte, son association schématique et le modèle ont été corrigés **ensemble**, avec conservation stricte des centres, angles, face, UUID et verrous des douze capteurs.

La nouvelle `Pacabot:ITR8307_S17_TR8_Bottom` suit le [dessin Everlight DRX-0000322 rév.6, p.2](https://www.everlighteurope.com/custom/files/datasheets/DRX-0000322.pdf) : corps 3,4 ×2,7 mm, hauteur depuis plan de soudure 1,62 mm nominal /1,87 mm maximum, centres de pieds (±0,9 ; ±2,11) mm. Broches 1 cathode, 2 anode, 3 collecteur, 4 émetteur ; chanfrein côté broche 2. Les lands de 1,2 ×1,4 mm sont un choix du projet à faire accepter à l'assembleur, pas un land pattern publié par Everlight. Détails dans la [revue capteur](sensor-sources/README.md).

Après correction, distances projetées centres de pads : sortie capteur → filtre **1,016 mm**, → résistance de charge **1,332 mm**, anode IR → résistance **0,880 mm**, identiques sur les douze voies. Les pastilles restent au moins à 0,965 mm du bord de carte. Aucun déplacement supplémentaire de passif ni fenêtre PCB n'a été nécessaire. [Contrôle détaillé](line-s17-passive-review.md).

## ESC retenu et montage

**EMAX D-SHOT Bullet Series 12A BLHeli-S, EMX-SC-1873** : 12 A continu, 15 A crête, 2–4S, 11 ×15 mm, 2,4 g sans fils, sans BEC. [Page constructeur et brochure](https://emaxmodel.com/products/emax-d-shot-bullet-series-12a-2-4s-blheli_s-esc-2-4g-support-onshot42-multishot). Aucun ESC 20/30 A ni modèle approchant n'a été utilisé. La page EMAX USA conserve la référence mais annonce maintenant AM32 : vérifier la révision du matériel livré, sans supposer qu'elle est mécaniquement identique au BLHeli-S demandé.

Aucun plan coté des pads ni STEP exact fiable n'a été trouvé. Photos constructeur recto/verso conservées, complétées par la [photo originale de Joe Earlam d'un Bullet 12A](https://forum.bristolbotbuilders.com/t/guide-how-to-solder-robots-good/725/2), 1920 ×1579 pixels, presque perpendiculaire. Homographie de quatre coins ramenée au rectangle nominal 11 ×15 mm ; incertitude indicative **±0,4 mm**, sans valeur de tolérance de fabrication. Les photos ne documentent pas l'épaisseur.

Le bord d'entrée présente **quatre pads CMS** visibles : gros GND puissance, petit GND logique, SIGNAL, +BATT. Leur identification provient des fils visibles, faute de dessin de brochage constructeur. Le montage à trois pins utilise le gros GND ; il suppose que le petit GND est commun avec celui-ci. **Cette continuité doit être mesurée sur le module réel avant d'omettre le quatrième fil.** Sinon, prévoir un retour logique séparé ou un petit adaptateur.

Empreinte créée : `Pacabot:EMAX_Bullet_12A_Vertical_3Pin_PROTOTYPE`.

| Pad | Fonction | Centre local X/Y, mm | Pin cuivre plein étamé | Trou fini | Cuivre PCB principal |
|---|---|---|---|---|---|
| 1 | GND puissance | −4,30 /0 | Ø1,2 mm | Ø1,4 mm | carré 3 ×3 mm |
| 2 | SIGNAL | +0,80 /+0,30 | Ø0,6 mm | Ø0,8 mm | Ø1,6 mm |
| 3 | +BATT /VPACK | +4,42 /0 | Ø1,2 mm | Ø1,4 mm | Ø3 mm |

Entraxes projetés 5,10 et 3,62 mm, **aucun pas standard supposé**. Le décalage de 0,30 mm du pin signal compense son rayon différent pour que les trois tiges soient tangentes à la même face de pads verticale. Les tiges se soudent en recouvrement sur des pads CMS ; le module n'a pas de trous traversants correspondants. GND/+BATT ont une liaison pleine aux futures zones, sans relief thermique.

L'empreinte comporte F.Fab, F.SilkS avec connexions/orientation, F.CrtYd 16,8 ×7,6 mm, ainsi que deux NPTH Ø1,7 mm pour un berceau isolant. Les seules soudures CMS ne sont pas un maintien suffisant sous vibrations : le petit berceau proposé est la modification mécanique minimale retenue. Ses tétons, sa matière et sa fixation doivent être qualifiés sur pièce.

Le [STEP ESC](../kicad-lib/3d/EMAX_Bullet_12A_Vertical_PROTOTYPE.step) et le [document FreeCAD Part Design](../kicad-lib/3d/EMAX_Bullet_12A_Vertical_PROTOTYPE.FCStd) comprennent 27 solides, chacun portant sa couleur AP214 (masque aubergine, pins en cuivre étamé, pastilles ENIG, boîtiers noirs, berceau blanc cassé). Le PCB ESC est vertical à **90°**, son bord inférieur à **2 mm** au-dessus de la carte, son sommet à **17 mm**. Les trois pins sont tangents aux pads du modèle sans pénétrer son FR4. Les trois sorties moteur restent accessibles au sommet. La gaine est retirée. **Estimations explicites** : PCB ESC 1,0 mm d'épaisseur, enveloppe électronique environ 3,85 mm, contours de pads, positions/hauteurs des composants, enveloppe des soudures. La garde de 2 mm et le berceau sont des choix de conception. Les couleurs sont indicatives : elles distinguent les volumes en vue 3D, elles ne relèvent aucune cote. [Sources, relevés, calculs et limites](esc-research.md).

Pins de puissance : section 1,131 mm², résistance calculée environ 0,097 mΩ pour 6,35 mm, soit 14 mW à12 A et22 mW à15 A par pin, hors soudures. Cela vérifie seulement la faible résistance de la tige. La capacité thermique des soudures, métallisations et futures zones cuivre **n'est pas encore qualifiée**. Aucun via ni piste n'est ajouté avant le routage demandé ultérieurement.

## Batterie commune et recharge

Connectique retenue : **Molex Mega-Fit 2002411133**, femelle **2004561213**, contacts **1720631333** pour AWG12, retenue secondaire **1054150003**. Une seule prise transporte **1 GND, 2 point milieu PACK_MID, 3 VPACK**. Vu dessus l'embase mâle, verrou au nord, l'ordre gauche→droite est **3 /2 /1**, contrôlé contre le dessin fabricant et sa vue femelle en miroir. [Embase Molex](https://www.molex.com/en-us/products/part-detail/2002411133).

Courant de référence retenu : **24 A avec AWG12**, trois circuits chargés, élévation de température30°C dans les conditions de la [spécification Molex §4.3](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/productspecificationpdf/172/172063/1720631000-PS-000.pdf?inline=). Cette valeur demande déclassement et essai du montage ; elle ne garantit pas le futur cuivre PCB. Le budget provisoire est19,5 A continus /22,5 A pointe pour un ESC, deux limites moteur actuelles et une provision logique, avant tolérances. Aucun connecteur d'équilibrage JST-XH n'est employé en puissance.

Empreinte spécifique au plan : pas5,70 mm, trous électriquesØ1,80 mm, padsØ2,70 mm, deux NPTHØ3 mm, minimum nominal cuivre–NPTH≈0,30 mm. Corps17,75 ×6,79 mm, hauteur maximale17,50 mm ; enveloppe accouplée30,90 mm. Le STEP exact n'a pas pu être téléchargé : deux enveloppes Part Design ont été créées suivant le dessin constructeur, avec simplifications documentées et enveloppe de verrou conservatrice. [Dossier constructeur, CAO et courant](battery-sources/README.md).

Le point milieu rejoint le BQ25887 existant. **R107 passe de10 Ω/1 W à47 Ω/1 W**, dans la même empreinte2512 : environ87,5 mA d'équilibrage et0,36 W à4,2 V, au lieu d'une dissipation dépassant1 W. L'équilibrage devient plus lent. [Justification TI et revue électrique](battery-independent-review.md).

La charge reste inhibée par défaut matériel. Il manque encore les cellules/capacité, le profil firmware et la vraie surveillance thermique du pack : le schéma existant emploie un diviseur fixe sur la température. Le seuil d'équilibrage du BQ25887 ne valide pas l'ancienne hypothèse LiFePO4. Ne pas présenter cette intégration comme une batterie déjà qualifiée pour recharge. Le budget d'autonomie devra utiliser le courant moyen mesuré et la durée cible ; aucune autonomie numérique n'a été inventée.

**VPACK est le rail brut demandé.** L'ESC reste alimenté quand le bouton coupe la branche VBAT ; F10112 A ne protège que cette dernière. La protection pack/ESC et le conducteur MID doivent être dimensionnés avec les cellules retenues. Ces limites figurent également dans le schéma.

## Modifications et contrôles finaux

Le remplacement nécessaire des anciens J102/J103 et la suppression de J104/J702 concernent les quatre interfaces verrouillées devenues obsolètes. **Les 36 autres placements verrouillés, dont les douze capteurs, sont conservés exactement**, y compris leurs UUID. Carte finale :340 empreintes,328 Top /12 Bottom,0 piste,0 via,0 zone.

Le schéma comporte J103 (les trois pins réellement sur le PCB), ESC103 (symbole complet six ports, exclu du PCB) et M703 (moteur externe). ESC103 et J103 désignent un seul module, compté une seule fois dans la nomenclature. Les phases4/5/6 relient uniquement ESC103 à M703 ; aucun pad moteur fictif n'est ajouté à la carte principale. SIGNAL rejoint PB8 du STM32, broche139, via R707100Ω. C704220µF/**16 V**, désormais symbole polarisé, et C705100nF rejoignent VPACK/GND. Ils sont placés avec le nouveau montage ; U101 et Q101 sont légèrement déplacés. Les boucles principales du chargeur et la reprise précédente des chaînes laser sont conservées.

| Contrôle sur les fichiers enregistrés | Résultat |
|---|---|
| ERC natif KiCad | 0 violation |
| Parité schéma–PCB | 0 divergence ;1 064 pads physiques numérotés contrôlés |
| DRC natif | 0 erreur ;146 avertissements |
| Connexions non routées | 499, cohérent avec l'absence de routage |
| Géométrie ajoutée/déplacée | Aucun nouveau conflit cuivre/courtyard/perçage ;0 pastille hors carte |
| Export 3D final | 355 instances identifiées, aucun modèle manquant |
| Intersections solides | 160 couples candidats contrôlés ;0 collision entre références ou avec le FR4 |

Les146 avertissements DRC sont64 sérigraphies sur cuivre,44 chevauchements de sérigraphie,16 hauteurs de texte,13 différences avec bibliothèques et9 sérigraphies proches du bord. Ils restent à traiter avant fabrication ; les règles n'ont pas été affaiblies pour les masquer.

Réserves héritées :6 courtyards verrouillés débordent le contour (J101,J201,M1,M2,TM521,TM541) ;2 réservations de tête de vis de turbine intersectent en projection les courtyards M1/M2. Les solides actuellement modélisés ne se touchent pas, mais les vraies têtes de vis/rondelles et le futur collier doivent être validés. Aucun composant verrouillé n'a été déplacé pour supprimer ces signalements.

L'ESC placé à(144 ;134,5),180° conserve des jeux solides de4,83 mm versM1,7,30 mm versM3 et3,75 mm versUSB. Son plus proche composant estR112 à1,15 mm. L'enveloppe conservatrice du futur collier R18,35–23,75 mm, sur toute la hauteurESC, laisse **0,844 mm** au berceau. Son courtyard empiète encore de14,35 mm² sur le cercle indicatif du collier : cette différence entre réserve de soudure et solide est conservée explicitement. Le Mega-Fit accouplé reste à2,68 mm deC354, son voisin le plus proche.

## Points restant à valider physiquement

1. Révision exacte du Bullet12A ; dimensions nues, pads, continuité des deux masses et surfaces réellement soudables. Recaler footprint/STEP si les mesures diffèrent des estimations photographiques.
2. Montage des pins, accès du fer, résistance mécanique du berceau et des soudures, refroidissement/échauffement à12 A et aux pointes15 A ; parcours des trois fils moteur.
3. Collier et vis réels de turbine, dégagement du verrou et des fils AWG12 de la prise batterie ; garde au sol des capteurs S17 et tolérances d'assemblage.
4. Cellules, autonomie, protection du pack et deMID, mesure de température, profil/logiciel de charge. La recharge n'est pas validée tant que ces choix ne sont pas arrêtés.
5. Routage de puissance et retours de masse, métallisation des trous/vias, cuivre et essais thermiques. Les dimensions de pads et la section des pins préparent cette étape sans la remplacer.
