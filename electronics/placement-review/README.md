**Revue du placement — 6 septembre 2026**

Le placement est enregistré dans [UsainBot.kicad_pcb](../UsainBot.kicad_pcb).
342 empreintes sont présentes : 330 en Top et les 12 ITR8307 en Bottom.
84 empreintes existantes ont changé de face. Les 40 positions verrouillées,
leurs faces et leurs verrous sont conservés. Seul U201 a pivoté sur son centre
(155,217), de −135° à +45°. Le PCB contient toujours **zéro piste, zéro via,
zéro zone de cuivre** ; son contour et ses perçages mécaniques sont conservés.

Le placement des composants mobiles ne présente plus de collision de
courtyard, de pénétration des réserves mécaniques, de pad hors carte ou de
violation de clearance cuivre. **La carte entière conserve deux erreurs DRC
sur J103/J702 verrouillés et des réserves mécaniques initiales à arbitrer**,
détaillées plus bas. Ce dossier ne constitue donc pas une validation de fabrication.

[Vue globale](placement-top.png) · [STM32](mcu.png) ·
[Puissance](power.png) · [Laser avant](laser-front.png) ·
[Lasers latéraux](laser-lateral.png) ·
[Schéma analogique actualisé](schematic/05-sensors.svg)

**Organisation électrique retenue**

L'analyse part des nets du schéma actuel et des pastilles réelles du PCB,
sans reprendre les positions périmées de `tools/locked.json`. Les emplacements
sont recherchés dans les polygones de courtyard orientés, en conservant au
moins 0,12 mm entre courtyards mobiles et obstacles. Les cinq îlots du
courtyard OLED réservent son embase et ses quatre fixations : le volume libre
sous le module sur entretoises reste utilisable. Les composants mobiles
restent également hors du cercle indicatif de collier de turbine de rayon
23,75 mm. Les contrôles cuivre KiCad complètent cette géométrie.

Le STM32 regarde maintenant la barrette de ligne avec son côté analogique.
Le changement de 180° garde exactement son enveloppe et son centre. Il
raccourcit les accès aux lignes et à l'USB, avec un compromis sur le débogage
et certaines liaisons IHM. Les capacités sont affectées aux **broches**,
et non à une couronne géométrique indifférenciée : onze VDD, VDD33USB,
VBAT, VDDA, VREF et les deux VCAP. C212/C213 se trouvent à 1,88 mm des
broches VCAP ; les 100 nF VDD/USB à 1,30–3,68 mm. Le quartz, ses deux
charges et R204 restent ensemble auprès de OSC_IN/OSC_OUT. Le diviseur
batterie et les filtres de courant moteur se terminent côté ADC.

Les trois filtres ADC laser R508/C504, R528/C524 et R548/C544 sont placés
à la réception, côté STM32 ; leurs condensateurs sont à 3,77, 3,08 et
1,82 mm des broches 27–29. Le chargeur reste à l'arrière. Le buck complet
U103/L102 est passé dans l'épaule ouest, loin des récepteurs latéraux :
entrée et céramique VIN, bootstrap, self, sortie puis feedback forment
un ensemble compact. Le filtre FB101/C118–C120 est au point d'entrée du
domaine analogique. Les capacités de pompes des DRV8874 sont sur le côté
des broches 11–14 : C305/C355 à 1,76 mm et C306/C356 à 1,60 mm de leur
première broche. Le second terminal est pris en compte dans l'optimisation.

Le réservoir C354 en Top reste à 16,64 mm de VM du driver droit, contre
9,38 mm lorsqu'il était en Bottom. C357 est à 10,99 mm du connecteur
moteur droit. D102 reste dans l'épaule de puissance, à 27,23 mm du point
de bus Q103.5. Ces distances sont des compromis explicites dus aux verrous
et à l'occupation de la bande arrière ; les petits bypass et les pompes
ont la priorité sur ces composants volumineux. Prévoir le chemin de bus
et le cuivre de puissance en conséquence au routage.

Les résistances de courant et les RC de ligne ont été remontés au-dessus de
leur capteur associé. Le couplage AC des commandes laser et du buzzer a été
identifié comme tel : ces condensateurs restent en série avec le signal,
près des résistances de grille et de leur diode de limitation. Les commandes
laser sont séparées d'au moins 2 mm des courtyards des AOP. Les découplages
VDD/VDDIO de l'IMU sont à 1,20 mm de leurs broches ; celui du PCA9685 à
1,19 mm. Les réseaux de polarisation, protections USB, commandes de bancs IR,
IHM et communications sont rattachés à leurs circuits respectifs.

L'inventaire détaillé se trouve dans
[passive-roles-and-distances.csv](passive-roles-and-distances.csv), avec rôle,
broche d'ancrage et distance réelle. Les justifications par empreinte sont
dans [placement-rationale.json](placement-rationale.json).

**Trois chaînes laser locales**

U501A/B traite F, U502A/B traite FL, U504A/B traite L. Dans chaque boîtier :
1 = sortie TIA, 2 = photodiode, 3 = VREF_RX, 4 = alimentation analogique,
5 = entrée gain, 6 = retour gain, 7 = sortie gain, 11 = masse.
R504/C501, R524/C521 et R544/C541 sont placés **conjointement** avec
leur boîtier, ce qui réserve réellement la place des retours sensibles.
U501D conserve le buffer VREF_MID ; les amplificateurs inutilisés sont
polarisés à VREF_RX et bouclés en suiveurs sans charge.

| Liaison photodiode → entrée TIA | Avant | Après | Couloir Top prévisualisé |
|---|---:|---:|---:|
| TM501 → U501 | 33,86 mm | 3,10 mm | 3,68 mm |
| TM521 → U502 | 55,98 mm | 7,38 mm | 8,56 mm |
| TM541 → U504 | 69,01 mm | 2,90 mm | 3,61 mm |

Les colonnes avant/après sont des distances entre centres de pastilles.
La dernière colonne provient d'une recherche de passage autour des pads
Top et perçages réels, pour une piste hypothétique de 0,15 mm, avec
0,20 mm de garde aux autres pads, 0,25 mm aux trous et 0,5 mm au bord.
Les lignes orange des vues laser sont cette prévisualisation :
**aucun segment n'a été ajouté au PCB**. Ce contrôle ne couvre ni le
routage simultané de tous les nets ni l'intégrité des signaux et alimentations.

La somme des deux liaisons du condensateur de retour TIA passe de
140–150 mm à 3,55 mm ; celle des résistances de retour vaut désormais
6,32 mm. Le gain et la liaison AC restent dans la même station. Le rail
de référence sensible reçoit un filtrage local à chaque extrémité éloignée.

| Composant ajouté | Fonction |
|---|---|
| U504, TLV9064 | Boîtier propre à la station L |
| C568, 100 nF | Découplage local U504.4 |
| C569/C570, 100 nF | Filtrage VREF_RX près de U502.3/U504.3 |
| C223, 100 nF et C224, 1 µF | Découplage VBAT de U201.6, relié au 3,3 V |
| C351, 100 nF | Découplage local VREF_MOT du driver droit |

Seules les feuilles `02-mcu`, `03-motors` et `05-sensors` ont changé dans
le cadre de cette reprise. Les ajouts et réaffectations sont reportés dans
`tools/design.py`, sans régénérer les autres feuilles. Les valeurs des
chaînes analogiques et l'affectation des broches STM32 sont conservées.

**Vérifications et points restant ouverts**

L'ERC final est à **0 erreur / 0 avertissement**. Le DRC vérifie également
la parité schéma–PCB : **0 divergence**, et la comparaison explicite des
nets de toutes les pastilles ne relève aucun écart. Les 499 connexions
non réalisées restent attendues sur cette carte non routée.

Deux erreurs de placement DRC subsistent, toutes deux sur les verrous :
chevauchement J103/J702 et trou non métallisé de J103 dans le courtyard de
J702. Il s'agit d'un conflit entre les sorties ESC, distinct du chevauchement
avec la turbine accepté dans la demande. Sa suppression nécessite une
décision sur ces emplacements ou leur mécanique ; aucun verrou n'a été
déplacé pour le faire disparaître.

L'audit mécanique indépendant relève aussi les réserves de têtes de vis M3
(rayon 1,8 mm) touchant de 0,248 mm les courtyards des moteurs verrouillés.
Le cercle de collier, explicitement indicatif, recoupe J103/J104 (exceptions
demandées), J702 et les ensembles moteurs. Huit courtyards verrouillés
débordent légèrement du contour : USB J101, débogage J201, M1/M2,
TM521/TM541 et les deux capteurs extrêmes U401/U412. **Aucune pastille
cuivre ne déborde.** Certains débords correspondent à des organes qui
dépassent volontairement ; leur acceptation mécanique finale n'est pas
déduite d'un DRC cuivre. Les résultats bruts restent visibles dans
[geometry-after.json](geometry-after.json).

162 avertissements restent : 124 de sérigraphie, 12 de hauteur de texte
des optiques et 26 de correspondance des empreintes avec leur bibliothèque.
Les repères des composants mobiles ont été placés sur F.Fab, lisibles pour
la revue d'implantation. La sérigraphie de fabrication reste à finaliser.
Aucune règle DRC, exclusion ou géométrie de boîtier n'a été assouplie.

Pour le routage ultérieur des quatre couches existantes, préserver une
référence de masse continue sous les voies analogiques, les ADC et les
interfaces rapides ; garder les retours moteurs, buck, chargeur et
émetteurs hors des boucles de réception. Distribuer VREF_RX/VREF_MID avec
un retour de masse voisin et conserver le prélèvement du feedback buck
après la self et les condensateurs de sortie. Le découplage et les principes
de boucles courtes sont cohérents avec [ST AN5419](https://www.st.com/resource/en/application_note/an5419-getting-started-with-stm32h723733-stm32h725735-and-stm32h730-value-line-hardware-development-stmicroelectronics.pdf),
[TI TLV9064](https://www.ti.com/lit/ds/symlink/tlv9064.pdf) et
[TI DRV8874](https://www.ti.com/lit/ds/symlink/drv8874.pdf).

**Fichiers de contrôle**

[Synthèse vérifiable](verification-summary.json),
[DRC initial](drc-before.json), [DRC final](drc-after.json),
[ERC final](erc-after.json), [table des positions](placement.json),
[prévisualisation des chemins](analog-path-preview.json).
Les vues sont aussi disponibles en PDF. La sauvegarde des fichiers KiCad
avant intervention est [before-placement.zip](before-placement.zip).

Le PCB courant est la référence à poursuivre dans KiCad. Les anciens
`place_pcb.py --reset`, `layout.py` et `layout_fit.json` ne décrivent plus
cette implantation ; ne pas les appliquer à cette carte. Les scripts de
revue ajoutés sont autonomes par rapport à ces anciennes tables. L'audit
et les rendus sont en lecture seule. `apply_refined_placement.py` est une
opération d'écriture explicite de la table figée, avec vérification des
verrous et UUID ; il ne faut pas le relancer après de nouvelles retouches
manuelles sans réviser la table.
