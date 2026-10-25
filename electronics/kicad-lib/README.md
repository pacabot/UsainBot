# Bibliothèque KiCad — UsainBot

## Turbine_EDF27_dessus / Turbine_EDF27_dessous

La turbine d'appui EDF 27 mm, **mécanique seule** : ses trois fils vont à
l'ESC, jamais à la carte. Deux empreintes, **exactement les mêmes perçages** —
c'est tout l'intérêt du Ø34 : le sens de montage n'est pas figé au routage, on
change d'empreinte dans les propriétés et ni la position ni la rotation ne
bougent.

- **Un perçage Ø 34,0 sur `Edge.Cuts`**, porté par l'empreinte (comme
  `Motor_bracket_1524_shim`) : le contour suit la pièce, il n'y a plus de
  cercle libre à entretenir dans le `.kicad_pcb`
- **Trois NPTH M2 Ø 2,2 à 42,5 de BCD**, aux angles −90 / +30 / +150° :
  **la vis isolée regarde le nez**, les deux autres partent vers la queue
- **X de l'empreinte = l'essieu.** C'est la seule direction contrainte, et
  l'orientation à 3 vis est choisie pour elle (voir plus bas)
- Les deux empreintes se posent **côté dessus (`F.Cu`)** : la turbine traverse
  le plan de carte dans les deux cas, **il ne faut jamais les retourner**

### Pourquoi 34 et pas autre chose

| Cote | Valeur | Ce qu'elle vaut |
|---|---|---|
| Gorge du bell mouth | r = **17,20** | le perçage s'arrête à r 17,00 : **0,20 mm de marge**, l'entrée d'air n'est pas obstruée |
| Portée plate de la lèvre | r 17,20 → 18,35 | large de 1,15 mm, **entièrement en appui** sur la carte |
| Anneau de carte restant | **1,35 mm** | ce sur quoi la lèvre porte en montage posé |
| Jeu radial fût / perçage | **2,15 mm** | ce que le fût Ø29,7 laisse en montage encastré — **à étancher** |
| Matière entre perçage et vis | 1,80 mm | BCD 42,5, perçage M2 Ø2,2 |
| Débord latéral des deux vis arrière | **19,50 mm** | pour **20,20** disponibles une fois la voie à 155 (arrière du codeur) |

Ø34 est le **plus grand perçage rond qui laisse la portée plate de la lèvre
entièrement en appui** : à Ø34,4 le bord du perçage vient tangenter la gorge
du bell mouth, au-delà il mange la portée, qui n'a que 1,15 mm de large. Et il
est déjà plus large que le fût (29,7), donc il sert aussi au montage encastré :
un seul perçage pour les deux montages, c'est exactement ce qu'on cherchait.

Les deux outils booléens de `../../mechanics/turbineEDF27.py` (`DecoupeAir`
Ø28,4 et `DecoupeTraversante` Ø30,7) sont les **minima aérodynamiques**, pas
des perçages de carte : le 34 les couvre tous les deux.

### Les deux montages

| | `_dessus` (défaut) | `_dessous` |
|---|---|---|
| Position | posée sur la face dessus | encastrée par le dessous |
| Appui | la lèvre sur l'anneau de carte | le congé lèvre/fût **coince sur l'arête du perçage** et centre la turbine tout seul |
| Au-dessus de la carte | **25,80 mm** | **22,34 mm** |
| Sous la carte | rien | **3,46 mm** (la lèvre) |
| Vis M2 | par le dessous, collier sur la lèvre | par le dessus, collier sous la carte |
| Aspiration | lit la carte à bout portant | bell mouth dégagé dans le plénum |

Le montage encastré gagne **3,46 mm de hauteur** et une entrée d'air propre,
mais **la lèvre descend 3,46 mm sous la carte**, soit **1,54 mm du sol** —
plus bas que le bord de jupe, qui s'arrête à 3 mm. Il talonne le premier sur
les ondulations de la bâche. Et il ouvre **2,15 mm de jeu annulaire autour du
fût** : sans joint, le plénum se court-circuite par le perçage. Les deux
points se règlent au collier ; tant qu'ils ne sont pas tranchés, **le montage
posé reste le défaut**.

### Ce qui n'est pas dans l'empreinte

- **Le collier de serrage.** C'est une pièce imprimée à dessiner : elle prend
  les trois vis, elle serre la lèvre. Son diamètre indicatif (Ø48) est tracé
  en tirets sur `Dwgs.User`, et **il n'est pas dans le courtyard** — celui-ci
  ne porte que l'encombrement propre de la turbine, qui est une cote sûre.
- **La limite latérale.** Les deux traits d'axe à ±20,2 sur `Dwgs.User`
  rappellent où arrive l'arrière du codeur **une fois la voie élargie à 155**.
  Sur la carte actuelle les courtyards des équerres s'arrêtent à ±12,4 de
  l'axe de la turbine : ni la lèvre Ø36,7 ni les vis n'y passent. Le PCB n'a
  pas encore reçu la révision mécanique du 31 août.
- **Un symbole.** La turbine n'a pas de pad : elle ne remonte pas par la
  netlist. À poser à la main dans pcbnew, ou à faire passer par un symbole
  mécanique dans `../tools/gen_lib.py` + `design.py` si on veut qu'elle vive
  dans la chaîne scriptée comme les autres.

### À faire côté PCB avant de poser l'empreinte

1. **Supprimer le `gr_circle` Ø32 libre** en (155, 153) dans
   `UsainBot.kicad_pcb` : c'est l'ancien trou de turbine, il ferait doublon
   avec le `Edge.Cuts` de l'empreinte.
2. Passer `TURBINE` de `../tools/fit_layout.py` de `(155.0, 153.0, 16.3)` au
   nouveau centre et à **r 23,8** (le collier), sinon le placeur continue de
   ranger des composants sous la bride.

### Modèle 3D

`3d/Turbine_EDF27.step`, copie de `../../mechanics/turbineEDF27.step` produit
par le script paramétrique. Il est bâti **aspiration vers +Z** : les deux
empreintes le retournent (`rotate 180 0 0`) puis le descendent à son assise —
offset Z **25,800** en posé, **22,337** en encastré, valeur calculée par le
générateur à partir du congé de lèvre, pas saisie à la main.

Régénérer : `python3 gen_turbine_footprint.py` (tout se règle en tête de
fichier), puis `freecadcmd ../../mechanics/turbineEDF27.py` et recopier le
STEP si les cotes de la turbine changent. **Cotes de fiches revendeurs, à
recaler au pied à coulisse sur la pièce reçue** — en particulier la lèvre
Ø36,7, dont dépendent le Ø34 et le BCD.

## Telemetry_Duo_Coude

Une station de télémétrie complète sur **une seule empreinte** : l'OPV302
(VCSEL 850 nm, TO-46) et le BPV10NF (photodiode T-1¾) **couchés, pattes
cintrées à 90°**, plus les perçages du support pare-soleil imprimé qui les
guide et se **visse par le dessous** de la carte.

- Origine = **axe de la vis M2** du support ; **visée optique vers +X**
  (l'azimut se règle à la rotation de placement, comme les trois stations
  posées à −15/−45/−75°) ; axes optiques à **Z = 6,0 mm** au-dessus de la
  carte, **entraxe 10 mm** — TX en Y = −5, RX en Y = +5
- Pads **1 = TX K, 2 = TX A** (perçage 0,8) et **3 = RX K, 4 = RX A**
  (perçage 1,0), cathodes en roundrect, sur la ligne X = −7,5 derrière la
  face arrière du support. Même convention que `Device:LED` / `D_Photo`
  (broche 1 = cathode). **Couper la broche 3 (NC) du TO-46 au ras.**
- NPTH : **M2 Ø 2,2 au centre** + **2 pions Ø 1,6** en (−3,5, 0) et
  (+3,5, +1,5) — le second est décalé : **détrompeur**, le support ne se
  monte pas à 180°
- Face avant du pare-soleil à **X = +8** depuis le 4 septembre (elle était à
  +10 : 2 mm de trop). Le tube RX passe de 6,1 à 4,1 mm, donc de ±9,5 à
  ±11,6° vus de la puce — un peu moins de rejet du ciel, mais le
  recouvrement TX/RX commence à **49 mm au lieu de 61**, ce qui compte plus
  face à un mur proche. `Dwgs.User` porte les deux axes optiques en tirets
- **Courtyard en deux largeurs.** Le rectangle unique réservait les 18,5 mm
  du socle sur toute la longueur, y compris derrière la face arrière où il
  n'y a que la rangée de pads : impossible d'approcher quoi que ce soit des
  pattes des diodes sans déclencher la règle de recouvrement, alors que rien
  n'occupe ce volume. La partie arrière se borne désormais à la colonne de
  pads (X −8,60 à −5,25 sur Y −6,90 à +7,37)
- Le support est **opaque** dans le modèle 3D : c'est un pare-soleil, un
  rendu translucide laisserait croire que la lumière traverse la paroi
- Une empreinte ne pouvant servir qu'un symbole, la question était de savoir
  lequel : **tranchée le 4 septembre 2026** par un symbole à quatre broches,
  `Pacabot:Telemetry_Duo` (voir `../tools/gen_lib.py`), qui remplace le
  couple `Device:LED` + `Device:D_Photo`. Les trois stations sont désormais
  les références **`TM501` (15°), `TM521` (45°), `TM541` (75°)**, et le
  perçage mécanique `H50x` a disparu — il est dans l'empreinte
- **Rotation de placement** : l'empreinte visant +X au repos, un azimut
  `deg` compté depuis l'avant vers la droite de l'écran demande une rotation
  de `deg − 90`. L'origine est l'axe de la vis ; la face avant du
  pare-soleil est 10 mm plus loin dans l'axe de visée
- Le support **déborde du contour** aux stations 45 et 75° : sur un fuseau
  qui s'effile à ~40°, un rectangle de 18 mm de large présenté à 45 ou 75°
  ne peut pas tenir entièrement dedans. Le débord est du côté de la face
  avant, c'est-à-dire là où le faisceau sort de toute façon ; la vis M2 et
  les deux pions, eux, restent bien à l'intérieur

Régénérer : `python3 gen_telemetry_footprint.py`. Cotes des boîtiers :
datasheets TT OPV302 Rev C et Vishay BPV10NF Rev 2.3, **à recaler sur les
pièces reçues**.

### Le support pare-soleil (`../../mechanics/telemetry_duo.py`)

Trois corps PartDesign : le support (à imprimer, `Telemetry_Support.stl`),
et les deux diodes couchées qui servent de gabarit de cintrage. Le script
contrôle sur les solides : voies optiques dégagées, aucune interférence
support/diodes, cloison TX/RX pleine, chaque patte au travers de son pad.

- Deux fûts Ø 8 percés en ligne : lamage Ø 6,2 × 0,9 (collerettes), alésage
  Ø 4,9 (capot TO-46) / Ø 5,25 (corps T-1¾), puis **tube Ø 3,5 jusqu'à la
  face avant** — côté RX c'est **le pare-soleil** : ±9,4° vus de la puce
  (±20° natif), le spot du VCSEL (4° FWHM) reste vu au-delà de ~61 mm
  malgré la parallaxe de l'entraxe ; axes parallèles, sans pincement
- Vis **M2 par le dessous** : avant-trou Ø 1,7 × 7, engagement 6 mm
  (M2×8 avec la carte de 1,6). Résine cassante : si l'autotaraudage
  fissure, percer à 3,1 et coller un insert laiton M2
- Alésages cotés **SLA** ; en FDM prévoir +0,1 à +0,2 ou aléser après coup

**Contrairement aux générateurs moteurs, aucun miroir en Y à l'export** :
le modèle est construit directement dans le repère 3D de KiCad, STEP et STL
sont la même pièce. Deux pièges de plus au passage : en offscreen,
`saveImage()` segfaulte (pas de contexte OpenGL) et `print()` est avalé —
le bilan du script sort aussi dans `Telemetry_Duo.log`.

## Motor_Faulhaber_1524_15-10

Empreinte **mécanique** de la motorisation qui remplace le N20 : Faulhaber
**1524T006SR** + codeur **IE2-1024** + réducteur planétaire **15/10 3,33:1** à
paliers frittés, sur équerre-berceau usinée, roue **JSumo JS4311** 43 × 11 mm.

- Origine = **centre de l'équerre**, qui est symétrique en X et en Y
- Axe moteur suivant **Y**, arbre de sortie vers **−Y**, comme le N20
- 4 trous non métallisés **Ø 2,2 mm**, rectangle **18,0 × 18,0 mm**
- Axe à **14,90 mm** au-dessus du dessus de carte, soit 16,50 au-dessus du
  dessous : avec une roue de 43 mm, la garde au sol vaut **5,00 mm**
- Emprise : X ±11,25 mm, Y −16,00 → +29,80 mm (le moteur dépasse de 13,8 mm à
  l'arrière de l'équerre, ce qui dégage largement la nappe du codeur)
- `F.Fab` équerre, corps, arbre, et les quatre taraudages —
  `F.SilkS` l'équerre seule
- `Dwgs.User` : la roue en tirets, et surtout **le rectangle plein qui donne ce
  qu'il faut retirer du contour de carte** — ±15,50 mm entre Y −27,50 et −16,50.
  C'est là que le disque de 43 mm descend sous le plan de la carte.

Aucune connexion électrique : le moteur *et* le codeur passent par la nappe six
conducteurs du codeur, connecteur EN 60603-13 / DIN 41651 au pas 2,54 (2×3) —
`1` Moteur−, `2` Moteur+, `3` GND, `4` UDD, `5` Voie B, `6` Voie A. C'est une
embase à part dans le schéma, pas un pad de cette empreinte.

## Motor_bracket_1524_shim

L'entretoise, 22 × 32 mm à flancs obliques comme l'équerre, **contour porté par `Edge.Cuts`**. La hauteur d'axe
n'est pas faite par l'équerre mais par un empilage de trois de ces cales, tirées
dans les chutes du panneau de la carte mère : trois épaisseurs de 1,6 mm font
4,80 mm, et l'aluminium n'a plus qu'à porter les 2,55 mm de fond de berceau.

À poser dans une zone perdue du panneau, **trois fois par moteur**. Le milieu est
évidé : l'équerre ne porte que sur ses joues, et une cale pleine viendrait toucher
le fond du berceau. Prévoir des pontets ou demander l'usinage à onglets, sinon la
pièce se détache pendant le routage — un contour fermé isolé n'est pas accepté
tel quel par tous les fabricants.

Changer `SHIM_N` dans `faulhaber_geom.py` change du même coup le nombre de cales,
l'épaisseur du fond de berceau et la hauteur d'axe : la garde au sol reste celle
que demande `CLEARANCE`.

### Chaîne de génération

```sh
FCMD=/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd
#        l'équerre ne se génère plus : elle se modifie dans FreeCAD, voir plus bas
$FCMD gen_faulhaber_3d.py                   # moteur, réducteur, codeur, roue
python3  colorize_step.py                   # couleurs AP214
python3  gen_faulhaber_footprint.py         # les deux .kicad_mod
$FCMD    check_faulhaber_assembly.py        # contrôle interférences et jeux
```

Toutes les cotes sont dans **`faulhaber_geom.py`**, importé par les quatre
générateurs : c'est le seul fichier à toucher. Changer de diamètre de roue ou de
garde au sol y tient en une ligne, tout le reste suit — hauteur d'axe, épaisseur
du fond, nombre d'entretoises, découpe de carte, position de la roue.

`check_faulhaber_assembly.py` relit les six STEP comme KiCad les chargera et
échoue si deux pièces s'interpénètrent ou si l'un des trois jeux de montage
s'écarte de sa valeur. À relancer après toute retouche.

### Le repère des modèles 3D

Le repère des modèles 3D de KiCad a son **Y inversé** par rapport à celui de
l'empreinte. Les deux générateurs appliquent donc un miroir en Y au moment de
l'export : sans lui, une empreinte tournée de ±90° affiche ses modèles côté pour
côté, arbre et roue partant du mauvais bord de la carte.

Le miroir passe par `transformShape`, ni `mirror()` ni `transformGeometry`.
`mirror()`, sur une forme qui porte un `Placement`, travaille dans le repère
local puis réapplique le placement : elle déplace la pièce au lieu de la
retourner. `transformGeometry` convertit cylindres et cercles en NURBS — volume
juste, mais boîte englobante surestimée, et c'est une `BoundBox` que
`check_faulhaber_assembly.py` lit pour la garde au sol. Le STL, lui, est la pièce
à usiner : il ne se miroite pas.

## Symboles (`Pacabot.kicad_sym`)

Douze symboles absents des bibliothèques KiCad, ou dont le typage de broches
rendait l'ERC inexploitable. Régénérer avec `../tools/gen_lib.py`.

| Symbole | Pourquoi il est là |
|---|---|
| `DRV8874PWPR` | KiCad ne fournit que les DRV8870/71/72. Brochage HTSSOP-16 saisi depuis la fiche TI SLVSF66A : `EN/IN1` 1, `PH/IN2` 2, `nSLEEP` 3, `nFAULT` 4, `VREF` 5, `IPROPI` 6, `IMODE` 7, `OUT1` 8, `PGND` 9, `OUT2` 10, `VM` 11, `VCP` 12, `CPH` 13, `CPL` 14, `GND` 15, `PMODE` 16, pad thermique 17 |
| `AO4407A` | Canal P SO-8 pour la protection anti-inversion. Les `Q_PMOS_*` de KiCad n'ont que trois broches : impossible de les faire correspondre aux 1-3 source / 4 grille / 5-8 drain du boîtier |
| `LSM6DSOTR` | Copie de `Sensor_Motion:LSM6DS3` — même LGA-14, même brochage. `SDX` et `SCX` retypées en passif : elles sont strappées à la masse, et les laisser bidirectionnelles fait crier l'ERC sans raison |
| `ITR8307` | Copie de `Sensor_Proximity:ITR8307-S17-TR8`, phototransistor retypé en passif. « Collecteur ouvert » relié à un rail est un défaut d'ERC alors que c'est exactement le montage voulu |
| `HC4051` | Copie de `Analog_Switch:CD4051B` — même brochage que le 74HC4051. Les huit voies et le commun retypés en passif : les laisser bidirectionnelles fait crier l'ERC dès qu'on met une entrée inutilisée à la masse, ce qui est pourtant le bon réflexe sur un multiplexeur |
| `SW_Nav_5Way` | Switch 5 directions à commun unique. **Empreinte à confirmer** sur la référence retenue (LCSC C3674) : le champ est laissé vide exprès |
| `Motor_Faulhaber` | Embase TE Micro-MaTch 215079-6 de la nappe moteur + codeur |
| `Telemetry_Duo` | Le couple TX/RX d'une station de télémétrie en **un seul** symbole à quatre broches (1 = TX K, 2 = TX A, 3 = RX K, 4 = RX A). Une empreinte ne sert qu'un symbole : `Telemetry_Duo_Coude` porte les deux boîtiers, il lui fallait donc un symbole qui les porte aussi |
| `VBAT` `VPACK` `+3V3A` `+3V3_BLE` | Symboles d'alimentation des quatre rails propres au projet |

### Composants pris sur des symboles génériques

| Composant | Symbole | Empreinte |
|---|---|---|
| OPV302 + BPV10NF, station de télémétrie | `Pacabot:Telemetry_Duo` | `Pacabot:Telemetry_Duo_Coude` |
| TLV9064, quadruple ampli op | `Amplifier_Operational:TLV9064` | `Package_SO:TSSOP-14_4.4x5mm_P0.65mm` |

Les deux optiques sont traversantes et posées à la main, couchées sur pattes
cintrées : leurs cotes (TO-46 Ø 5,4 mm, T-1¾ Ø 5,0 mm) sont à recaler sur les
boîtiers réellement reçus, et la conséquence tombe côté mécanique, dans les
alésages du support imprimé.

## Modèles 3D (`3d/`)

Fichiers STEP **colorés**, déjà positionnés sur l'origine de l'empreinte
(offset et rotation à 0 dans le `.kicad_mod`, rien à régler dans KiCad).

### Boîtiers que KiCad déclare mais ne livre pas (`gen_3d_models.py`)

Plusieurs empreintes des bibliothèques KiCad 10 pointent vers un STEP absent
du paquet, ou vers son ancien nom. En 3D la carte se retrouvait trouée là où
vivent justement les pièces les plus hautes, et le contrôle d'encombrement —
turbine, équerres moteur, pack à l'arrière — ne voulait plus rien dire.

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd gen_3d_models.py

| Fichier | Ce que c'est | Cotes |
|---|---|---|
| `USB_C_Receptacle_HRO_TYPE-C-31-M-12.step` | blindage + languette | 8,94 × 7,30 × 3,26 (F.Fab + fiche HRO) |
| `TE_Micro-MaTch_215079-6_2x03_P1.27mm_Vertical.step` | corps **rouge**, contacts, queues | 9,70 × 5,20 × 4,00 (plan client TE C-215079 rév. Y2) |
| `L_Taiyo-Yuden_NR-30xx.step` / `NR-40xx` | self blindée | 3,0³ h 1,5 / 4,0³ h 3,0 |
| `SKRHABE010.step` | capot + bascule | 7,35 × 7,50 × 1,80 |
| `Turbine_EDF27.step` | les quatre corps du document PartDesign | ré-exporté par `../../mechanics/export_turbineEDF27.py` |
| `OLED_Standoffs_M2x6.step` | les quatre entretoises M2 × 6 et leurs vis | fûts ⌀4 à (±11,5 ; ±10,35) |

**Le Micro-MaTch a été refait le 4 septembre** : le premier modèle reprenait
la boîte englobante du F.Fab de KiCad — 6,70 × 9,71 × 5,60 en **noir**,
alors que le plan client donne 9,70 × 5,20 × 4,00 et que le boîtier est en
**polyester PBT rouge** (contacts bronze phosphoreux étamés sur nickel).
Longueur et largeur étaient interverties, la hauteur dépassait de 1,6 mm.
Les cotes viennent maintenant du plan, pas d'une boîte englobante.

Ce sont des modèles d'**encombrement** : les volumes qui décident des
collisions, pas le détail du contact. Les couleurs sont injectées après coup
par `step_colors.py` — FreeCAD en console n'a pas de `ViewObject` et son
export STEP sort sans la moindre couleur, alors que KiCad 10 ne lit plus que
du STEP. Deux chemins morts se réparent en revanche sans rien modéliser (le
HTSSOP-16 et le HVQFN-24 existent sous un autre nom) : la table est dans
`../tools/place_pcb.py`, qui refuse de finir en silence s'il reste une
empreinte sans modèle.

### Motorisation Faulhaber

Six fichiers, produits par `gen_faulhaber_3d.py` et
`../../mechanics/Motor_bracket_1524.FCStd`.

| Fichier | Couleur | Origine | Masse |
|---|---|---|---|
| `Faulhaber_1524_motor.step` | acier nickelé | STEP Faulhaber, fils du moteur nu tronqués | 18 g (fiche) |
| `Faulhaber_15-10_gearhead.step` | inox | STEP Faulhaber, aucune retouche | 19 g (fiche) |
| `Faulhaber_IE2-1024_encoder.step` | sombre | **reconstruit** : enveloppe Ø15 × 1,4 + amorce de nappe | — |
| `Motor_bracket_1524.step` | aluminium | export de `../../mechanics/Motor_bracket_1524.FCStd` | 8,1 g |
| `JSumo_JS4311_hub.step` | aluminium | **reconstruit** d'après les cotes JSumo | 12,8 g |
| `JSumo_JS4311_tire.step` | silicone orange | **reconstruit** | 4,5 g |

Les deux STEP Faulhaber ne sont pas redessinés : `gen_faulhaber_3d.py` leur
applique une rotation de 90°, une translation et le miroir en Y, rien de plus.
Leur provenance et les cotes qu'on en a tirées sont dans `3d/vendor/README.md`.
Basculer `GEAR_STEP` sur `15-10K_1stage.stp` suffit à passer à la version à
roulements : la portée de centrage et le début de l'arbre suivent.

Position de la roue : face extérieure à 0,2 mm du bout d'arbre, face intérieure
à 0,5 mm de la platine de l'équerre.

### Couleurs

KiCad 10 n'utilise plus que du STEP (aucun `.wrl` livré) : la couleur doit être
portée par le fichier lui-même. FreeCAD en mode console ne sait pas les écrire —
pas de `ViewObject`. Les entités `COLOUR_RGB` / `STYLED_ITEM` sont donc ajoutées
en post-traitement par `colorize_step.py`, sur le même motif que les modèles
livrés avec KiCad. Pour changer une teinte : éditer `PALETTE` en tête du script,
régénérer le STEP concerné, puis relancer `python3 colorize_step.py`.

**Un troisième piège de console, celui-là silencieux.** `step_colors.py`
reconnaît chaque solide par le nom de son `PRODUCT`, c'est-à-dire le `Label`
FreeCAD : il lui faut donc **un PRODUCT par corps** dans le STEP.
`Part.export()` n'en écrit qu'un seul, anonyme (`Open CASCADE STEP translator
7.8 1`), qui rassemble toute la liste — aucun label ne correspond plus, la
fonction rend 0 sans rien dire et le modèle arrive gris uniforme dans KiCad.
C'est ce qui est arrivé à l'ESC EMAX du 6 septembre 2026 : 27 solides, zéro
`COLOUR_RGB`. **Exporter par `Import.export()`**, qui conserve la structure
d'assemblage et les labels — c'est ce que fait `gen_3d_models.py` — et
vérifier le nombre de styles rendus (`build_emax_bullet12a.py` l'assertionne
contre le nombre de corps).

## Ré-export de la turbine

`turbineEDF27.FCStd` **se modifie à la main dans FreeCAD** : c'est lui qui
fait foi, et `mechanics/turbineEDF27.py` ne doit plus être relancé dessus —
les deux visent le même nom de fichier. Pour rafraîchir le STEP que porte
l'empreinte après une retouche du PartDesign :

```sh
cd ../../mechanics
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd export_turbineEDF27.py
```

Le script **ne fabrique rien** : il ouvre le document, exporte les quatre
corps (`Fut`, `Redresseur`, `Rotor`, `Faisceau`) et copie le résultat dans
`3d/Turbine_EDF27.step`. **Il ne sauvegarde jamais le document** — une
sauvegarde hors interface emporte `GuiDocument.xml`, donc toutes les
couleurs.

Les couleurs sont **relues dans le .FCStd**, pas redéclarées : `GuiDocument.xml`
dit quel objet pointe vers quel blob, et les blobs binaires `ShapeAppearanceNN`
du même zip portent quatre couleurs empaquetées en uint32 petit-boutiste
(ambiante, **diffuse**, spéculaire, émissive) puis brillance et transparence.
Une palette recopiée dans un script se serait désynchronisée au premier coup
de pinceau. Passer par l'interface aurait été plus direct — un `ViewObject`
n'existe que si elle est chargée — mais `QT_QPA_PLATFORM=offscreen` reste
bloqué à l'ouverture de ce document-ci, faute de contexte OpenGL.

**Deux pièges de plus, en console.** `freecadcmd` **avale les exceptions du
script et sort avec le code 0** : un contrôle géométrique qui échoue ne se
voit à rien, sinon à l'absence de fichier de sortie. Pour déboguer, lancer le
script depuis un `exec()` enveloppé dans un `try` (voir l'historique de
session). Et le contrôle de cloison de `telemetry_duo.py` sondait un volume
avec une **boîte écrite en dur** : raccourcir le pare-soleil de 2 mm la
faisait dépasser de la pièce et signalait une cloison ajourée là où il n'y
avait plus que du vide. La sonde suit maintenant `X_AVANT`.

## Réserves — motorisation Faulhaber

1. **Les deux paires de trous de la face de sortie sont attribuées par leur
   foret, pas par le plan.** Le plan du 15/10 porte « M2 2x », « 2-56 UNC 2x »,
   « Ø10,92 » et « Ø11 » sans dire quel filetage va sur quel cercle. Le STEP
   tranche : Ø1,6 à (0, ±5,5) — foret M2 — et Ø1,8 à (±5,46, 0) — foret #50 du
   2-56 UNC. **Le berceau se boulonne donc sur la paire verticale**, ce qui tombe
   bien : c'est celle qui reprend le mieux le moment de la roue. À confirmer au
   jeu de forets sur la pièce reçue avant de percer une carte.

2. **Le modèle du codeur est une enveloppe**, pas un relevé : Faulhaber ne publie
   pas de STEP pour l'IE2. Ø15 × 1,4 mm — la seule cote donnée par la fiche, via
   L1 = 26,2 mm pour le 1524…SR — plus une amorce de nappe de 7 mm dessinée à
   l'estime. La sortie de nappe réelle est à relever sur la pièce : elle décide
   du dégagement à laisser derrière le berceau.

3. **La roue JS4311 est reconstruite.** JSumo ne publie aucune CAO. Le hors-tout
   (Ø43, 11 mm, gomme de 8 mm, alésage 3 mm) vient de la fiche produit ; le
   découpage interne du moyeu — jante de 2 mm, voile de 3,2 mm, six allègements
   Ø4,5 sur Ø23 — est un choix, calé pour retrouver les 17,7 g annoncés. On
   arrive à 17,3 g, soit 2 % d'écart. **Ce qui compte pour la carte est juste**
   (diamètre, largeur, alésage) ; le reste est du rendu.

4. **La vis de pression seule ne tiendra pas sur l'arbre lisse du 15/10.**
   L'arbre de sortie est un Ø3 h8 sans méplat, et le couple s'inverse à chaque
   freinage. Prévoir un méplat limé au droit de la vis M4 du moyeu.

5. **La charge radiale admissible est le point serré du montage.** Le 15/10 à
   paliers frittés n'accepte que **4 N à 6,5 mm** de sa face d'appui — la version
   K, à roulements préchargés, en accepte 30. La roue est centrée à **8,50 mm**
   de la face (2,50 de platine + 0,50 de jeu + 5,50 de demi-largeur), ce qui
   ramène l'admissible à **3,06 N**. En statique le robot en met environ 2,2 N
   par roue, poussée de turbine comprise : il reste **moins de 30 % de marge**,
   et un choc de bordure la mange. Deux leviers, dans cet ordre : garder la roue
   au plus près de la face — `BR_FLANGE_T` est déjà au minimum, voir la réserve
   suivante — et, pour une saison de compétition, passer aux 15/10**K**. Les deux
   sont interchangeables : `GEAR_STEP` et `GEAR_BOSS_H` dans `faulhaber_geom.py`.

6. **La platine avant est plafonnée à 2,50 mm par la roue, pas par la rigidité.**
   Le Ø3 utile de l'arbre ne fait que 12,0 mm (de Z 2,2 à 14,2 sur le 15/10
   fritté) pour une roue de 11,0 mm : il reste 1,0 mm à répartir entre le jeu
   sous la platine et le retrait du bout d'arbre. Épaissir la platine repousse la
   roue vers l'extérieur, aggrave le porte-à-faux de la réserve précédente, et
   finit par déborder du bout d'arbre. C'est aussi pourquoi les deux vis de la
   platine sont **fraisées** : une tête cylindrique dépasserait de 1,3 mm et
   viendrait taper la roue, qui n'est qu'à 0,5 mm.

7. **Le moteur n'est retenu que par les deux vis de la platine.** Le berceau
   ouvre à 180° : il porte le corps et l'évacue thermiquement, il ne le serre
   pas. C'est le montage prévu par Faulhaber, et un berceau qui enveloppe plus de
   180° ne serait plus usinable en trois axes depuis le haut. Si les vibrations
   le demandent, la platine supérieure peut recevoir un patin demi-rond au droit
   du berceau — les quatre taraudages sont là pour ça.

8. **La platine supérieure se pose à 12,35 mm, le moteur monte à 22,40.** Elle
   devra donc être fendue ou évidée au droit des deux moteurs, ou surélevée par
   des entretoises. Ses quatre appuis par moteur sont à (±9,00, ±9,00) dans le
   repère de l'empreinte — les mêmes que ceux de la carte, puisque les taraudages
   traversent.

9. **Les deux vis d'une même position se partagent un trou traversant.** M2 sur
   toute la hauteur de joue, 10,10 mm : la carte se visse par le dessous, la
   platine de renfort par le dessus. La joue ne fait plus que 7,55 mm depuis que
   le berceau est au tiers du diamètre : compter **4,0 mm d'engagement maximum par
   le bas et 3,0 mm par le haut** — au-delà, les deux vis se rencontrent. C'est le
   prix du trou unique, qui supprime la moitié des opérations de taraudage et
   surtout la collision qu'avaient les trous borgnes : à cette longueur d'équerre,
   ceux du dessus mordaient dans la platine.

10. **La pièce n'a aucun congé, et c'est délibéré.** Ce qui adoucit sa ligne, ce
    sont trois enlèvements de matière qui ont chacun une raison — l'aileron, le
    gousset, la fenêtre — pas des rayons posés après coup. Une version antérieure
    en avait partout : ils se mangeaient l'un l'autre au calcul, imposaient un
    ordre d'application, et l'un d'eux était impossible à obtenir. Ne pas les
    remettre.

## Visserie

| Où | Vis | Nombre |
|---|---|---|
| Platine → réducteur | **M2×5 tête fraisée 90°** (DIN 965) | 2 par moteur |
| Carte + 3 entretoises → équerre, par le dessous | M2×12 | 4 par moteur |
| Platine supérieure → équerre, par le dessus | M2×L selon son épaisseur | 4 par moteur |

L'équerre n'a que **quatre taraudages M2, traversants**, avant-trou Ø1,6 sur les
10,10 mm de hauteur de joue : la carte se visse par le dessous et la platine de
renfort par le dessus, dans le même trou. Un perçage-taraudage par position au
lieu de deux, et les deux vis ne peuvent plus se gêner — à condition de rester
sous **4,0 mm d'engagement par le bas et 3,0 mm par le haut**, faute de quoi
elles se rencontrent.

Ils sont percés dans les joues, jamais dans le fond du berceau : celui-ci ne fait
que 2,55 mm et une vis le traverserait pour venir toucher le moteur.

La tête fraisée n'est pas un détail de style : une tête cylindrique dépasserait
de 1,3 mm de la platine et viendrait taper la face interne de la roue, qui n'est
qu'à 0,5 mm. Fraisée, elle affleure. Et la longueur est **5 mm, pas 6** : le
taraudage du réducteur ne fait que 3 mm, la platine en consomme 2,5, et une M2×6
talonnerait au fond du trou avant d'avoir serré.

## L'équerre, pièce PartDesign

`mechanics/Motor_bracket_1524.FCStd` est un **corps PartDesign**, construit comme
on le dessinerait à la main : **dix esquisses, dix fonctions**, tout ouvrable et
modifiable dans l'interface. C'est cette version-là qu'il faut éditer.

| Fonction | Esquisse | Ce qu'elle fait |
|---|---|---|
| `Corps` | `Esq_Contour` | pad du rectangle, jusqu'au haut des joues |
| `Berceau` | `Esq_Berceau` | poche du cylindre, sur toute la longueur |
| `Platine` | `Esq_Platine` | pad du profil en D, pleine largeur sous l'axe |
| `Pincement` | `Esq_Pincement` | poche en cadre : les quatre flancs obliques d'un coup |
| `Lamage` | `Esq_Lamage` | portée de centrage, esquisse décalée en Y |
| `Arbre` | `Esq_Arbre` | passage d'arbre |
| `VisPlatine` | `Esq_VisPlatine` | les deux M2 traversants |
| `Fraisures` | `Esq_Fraisures` | poche **à dépouille −45°** = fraisure à 90° |
| `Taraudages` | `Esq_Taraudages` | quatre M2, avant-trou Ø1,6 |
| `Evidement` | `Esq_Evidement` | **poche à profondeur donnée** — voir plus bas |

Les **dix esquisses sont entièrement contraintes**, et chaque cote est une
contrainte nommée liée au tableur `Params` par expression. Ouvrir une esquisse
montre donc des cotes lisibles ; changer une valeur du tableur les déplace toutes
ensemble. Saisir une cote à la main la détache du tableur — c'est le comportement
normal de FreeCAD, pas un défaut.

Le corps est dessiné dans **son propre repère** — avant en Y=0, dessous en Z=0 —
puis reposé dans celui de l'empreinte par son `Placement`, lui aussi lié au
tableur. Travailler ainsi évite tout plan de référence : les dix esquisses
tiennent sur les trois plans d'origine du corps.

**La pièce ne se génère plus par script.** Elle a été reprise dans l'interface —
la platine retouchée, deux poches d'allègement ajoutées — et c'est le `.FCStd` qui
fait foi. Les scripts qui l'avaient créée ont été retirés : ils l'auraient écrasée.

Deux esquisses ajoutées à la main sont **accrochées à des faces** (`Taraudages`
Face6, `Pocket` Face6). Toute modification doit donc se faire **en bout d'arbre**,
ou en amont seulement si l'on est prêt à recoller ces attachements.

### Le filetage des vis de support

La fonction `Filetage`, en bout d'arbre, porte le **filet M2 réellement modélisé**
— hélice comprise — sur les quatre trous de fixation. Le tableur porte un
interrupteur `filet_modelise` : à `1` le filet est là, à `0` il ne reste que les
quatre avant-trous Ø1,6.

C'est une fonction `Hole` et non une poche, parce qu'elle seule sait générer
l'hélice. Elle vient **après** `Pocket001` et ne touche donc à aucune face en
amont ; les trous Ø1,6 existaient déjà, elle n'y creuse que les gorges — 15,4 mm³
en tout.

### Ce filet ne s'imprime pas

Il est dans le modèle, mais **JLC3DP ne le reproduira pas en frittage**, et il ne
faut pas le leur envoyer. Leurs propres règles :

| Règle JLC3DP, SLM | Valeur | Notre pièce |
|---|---|---|
| Plus petit filetage imprimable | **M6** | M2, pas de 0,4 mm |
| Tolérance dimensionnelle | ±0,3 mm | hauteur de filet M2 : 0,22 mm |
| Tolérance sur les perçages | ±0,5 mm | perçage Ø1,6 |
| Profondeur max d'un Ø1,5 / Ø2,0 | 4,5 / 6,0 mm | trous traversants de 7,55 mm |
| Épaisseur de paroi minimale | 1,5 à 2,0 mm | **0,91 mm** autour des filets |

Ce dernier chiffre est mesuré sur le solide : entre le filet Ø2,0 et le berceau il
ne reste que **0,91 mm**, et 1,00 mm vers le flanc. C'est confortable pour de
l'aluminium usiné, c'est sous le minimum de leur procédé.

**Ce qu'il faut envoyer**, donc : `Motor_bracket_1524_SLM.step`, exporté avec
`filet_modelise = 0`, quatre avant-trous lisses — puis **tarauder M2 après
impression**, taraud à goujure hélicoïdale et huile de coupe, 7,55 mm de
profondeur dans du titane.

### Titane : ce que ça coûte

Le TC4 de JLC3DP est le Ti-6Al-4V. Deux conséquences à peser avant de commander :

- **La masse.** 4,43 g/cm³ contre 2,70 pour l'aluminium : la pièce passe de
  **8,1 à 13,2 g**, soit **+10,2 g pour les deux équerres** sur un robot de 250 g.
- **Le refroidissement.** Le titane conduit **25 fois moins** que l'aluminium
  (≈ 6,7 contre 167 W/m·K). Or cette équerre a été choisie en aluminium *parce
  qu'elle sert de radiateur au moteur* : la fiche Faulhaber donne 3,9 K/W de
  résistance thermique boîtier-ambiance sur bride métallique contre 30 K/W sur
  bride plastique, et le calcul de course sortait 1,88 W efficaces par moteur.
  En titane, l'équerre cesse largement de jouer ce rôle — l'échauffement du
  bobinage se rapprochera des +79 K du cas plastique plutôt que des +30 K de
  l'aluminium.

À quoi s'ajoute que la pièce est **dessinée pour l'usinage** : que des plans et
des cercles, aucun congé, aucune forme que la fraise ne sache faire. La payer en
frittage, c'est en payer le prix sans utiliser la liberté de forme qui le
justifierait.

### L'évidement du fond n'est pas traversant

C'est une **poche à profondeur donnée**, 3,05 mm, et il faut qu'elle le reste. En
« à travers tout » elle remonterait dans la rainure et ressortirait sur le dessus,
coupant le berceau en deux. À 3,05 mm elle ne perce le fond que sur les **5,4 mm
du milieu**, là où la rainure descend le plus bas ; sur les bords il subsiste une
lèvre, et c'est voulu.

### Trois pièges rencontrés en PartDesign

- **Le plan XZ a sa normale vers −Y.** Un pad la suit, une poche va à l'opposé :
  d'où le `Reversed = True` de la platine et le `Reversed = False` des poches. Une
  poche prise à l'envers ne retire rien et ne dit rien.
- **Une contrainte de rayon sur l'arc laisse l'esquisse sous-contrainte** tout en
  paraissant complète : ce sont les deux naissances de l'arc, sur les épaules, qui
  donnent le rayon. `solve()` renvoie un code de retour, pas un nombre de degrés
  de liberté — seul `FullyConstrained` fait foi.
- **La fraisure est une poche à dépouille rentrante** sur un cercle au diamètre de
  tête, pas une dépouille sortante sur le diamètre de passage. Les deux enlèvent
  exactement le même volume ; seule la comparaison des solides montre que le cône
  est à l'envers.

## Usinage de l'équerre
