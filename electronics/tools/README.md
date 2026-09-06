# Générateur du schéma

Les huit `*.kicad_sch` de `electronics/` et la bibliothèque
`kicad-lib/Pacabot.kicad_sym` sont **produits par ces scripts**, à partir du
brochage et des choix de composants du document d'architecture.

```sh
python3 gen_lib.py      # kicad-lib/Pacabot.kicad_sym  (puis normalisé par kicad-cli)
python3 optimize.py     # génère, optimise le placement, régénère, passe l'ERC
```

`design.py` seul régénère sans optimiser. Après toute retouche de `design.py`,
relancer `optimize.py` ; après un changement de texte (étiquette, valeur,
note), relancer d'abord `calibrate.py`.

Dans cet ordre : `design.py` recopie chaque symbole dans le schéma et KiCad
compare cette copie à la librairie. Si la librairie n'a pas été normalisée
avant, chaque symbole lève un avertissement « ne correspond pas à la copie ».

> **Le schéma est écrasé à chaque exécution.** À partir du moment où tu retouches
> quoi que ce soit dans Eeschema, ces scripts deviennent une archive de la
> version initiale — ne les relance pas sans avoir reporté tes modifications.

## Découpage

| Fichier | Rôle |
|---|---|
| `sexp.py` | lecture / écriture des S-expressions KiCad |
| `kigen.py` | placement, raccordements, vérifications géométriques |
| `gen_lib.py` | les douze symboles propres au projet |
| `design.py` | les sept feuilles et la feuille racine |
| `calibrate.py` | mesure du rendu réel de chaque texte → `metrics.json` |
| `optimize.py` | optimisation du placement en point fixe → `placement.json` |

Les bibliothèques KiCad sont cherchées dans `/Applications/KiCad/…`, puis
`/usr/share/kicad`. Sur une autre installation : `KICAD_SHARE=/chemin python3 …`.

## Conventions

**Tout passe par des étiquettes.** Chaque broche reçoit un tronçon de 2,54 mm
(5,08 mm sur le microcontrôleur) terminé par une étiquette locale, une étiquette
globale ou un symbole d'alimentation. Aucun fil long, donc aucun croisement à
arbitrer, et une netlist qui se relit signal par signal. Les feuilles
communiquent par étiquettes globales plutôt que par entrées de feuille : un bloc
se lit seul, et renommer un signal ne demande pas de retoucher la racine.

**Les étiquettes restent horizontales**, y compris au bout d'un tronçon
vertical. Écrite le long du fil, une étiquette traverse le composant placé
au-dessus ou au-dessous : c'est exactement ce qui arrivait aux deux `VBAT_SENSE`
du pont diviseur R119/R120, chacune écrite dans le corps de l'autre résistance.

**Une seule étiquette par net, même sur plusieurs broches.** Les broches
confondues du BQ25887 (`PMID`, `SW`, `SNS`, `BAT` sont doublées) et les grappes
étalées — quatre drains de l'AO4407A, cinq masses de l'embase USB-C — sont
ramenées par `cx_bar()` sur une barre commune terminée par une étiquette unique,
au lieu d'en empiler autant que de broches.

**Pas de coude.** Un tronçon part toujours tout droit dans l'axe de sa broche.
Deux tronçons parallèles ne se croisent jamais ; un coude, lui, retombe sur la
broche voisine et court-circuite deux nets sans que rien ne le signale à
l'écran. Les symboles d'alimentation ont leur broche à l'origine : les tourner
ne déplace rien, ce qui permet de les orienter proprement sans coude.

**Grille de 1,27 mm.** Toutes les coordonnées y sont ramenées à l'écriture.
Sinon KiCad refuse la connexion et l'ERC se remplit de `endpoint_off_grid`.

## Vérifications

`design.py` refuse de terminer en silence sur trois classes d'erreur :

- une empreinte qui n'existe pas dans les bibliothèques installées ;
- deux tronçons colinéaires de nets différents qui se recouvrent, une
  extrémité qui tombe au milieu d'un fil étranger, ou **deux extrémités de
  nets différents au même point** — le court-circuit géométrique, invisible à
  l'œil sur une feuille A3. Ce dernier cas a été ajouté le 4 septembre après
  qu'il eut relié B+ à B− sur la prise d'équilibrage : les coudes que `cx()`
  ajoute aux symboles d'alimentation retombaient tous deux sur la ligne de la
  broche du milieu, à 2,54 mm de pas. La parade dans le générateur est de
  donner aux trois tronçons **trois longueurs différentes** ;
- un composant ou une note qui tombe dans le cartouche ;
- deux boîtes englobantes qui se recouvrent — corps, référence, valeur,
  étiquette, symbole d'alimentation, note. Un texte écrit par-dessus un boîtier
  ne casse rien électriquement et ne sera donc jamais signalé par l'ERC, mais
  rend la feuille illisible.

Ces contrôles ne remplacent pas l'ERC, ils attrapent ce qui, sans eux,
n'apparaîtrait qu'après coup dans la netlist.

## Placement automatique

Deux fichiers de données pilotent la mise en page, tous deux régénérables :

**`metrics.json`** — produit par `calibrate.py`. Plutôt que d'estimer la
largeur des textes, le script fait rendre par `kicad-cli` chaque chaîne du
schéma sur des feuilles de calibration, rasterise le SVG et mesure l'encre au
huitième de millimètre. Le vérificateur de recouvrements travaille donc sur
les rectangles que KiCad dessine vraiment — c'est ainsi qu'on a appris qu'un
texte multi-lignes s'étend vers le *haut* depuis son ancre, et que le cadre
d'une étiquette globale déborde de 1,1 mm sous sa ligne d'attache.

**`placement.json`** — produit par `optimize.py`. Boucle en point fixe :
génération, classement des recouvrements, calcul de déplacements, écriture,
regénération, jusqu'à zéro recouvrement dur. Trois politiques :

- seuls bougent les composants à deux ou trois pattes, les notes et la
  longueur des tronçons d'étiquette — jamais les circuits intégrés, les
  connecteurs ni les fils ;
- une passe qui fait apparaître un défaut électrique (fils qui se recouvrent)
  est **annulée en bloc** : la lisibilité ne s'achète jamais contre la netlist ;
- deux étiquettes de broches voisines dont les cadres se frôlent de moins de
  1 mm sont tolérées — c'est l'aspect normal d'une colonne de broches au pas
  de 2,54 mm, pas un défaut.

L'état de référence est **0 erreur, 0 avertissement** :

```sh
cd .. && kicad-cli sch erc --severity-all UsainBot.kicad_sch
```

Le contrôle `single_global_label` est activé dans `UsainBot.kicad_pro` : une
étiquette globale qui n'apparaît qu'une fois est une faute de frappe, pas un
signal.

## Placement du PCB

Quatre fichiers, même philosophie que le schéma : la position de chaque
composant est **écrite dans un script**, jamais posée à la souris — à une
exception près, décrite juste après.

- `lock_import.py` — **l'exception, et elle prime.** Une empreinte
  verrouillée dans pcbnew est une décision prise à l'écran, sur la pièce
  réelle ; ce script les relève dans `locked.json`, que `layout.py` applique
  par-dessus sa propre table. `place_pcb.py` ne les efface pas au `--reset`
  et ne les déplace jamais. Il **rafraîchit** en revanche leur dessin
  d'empreinte sur place : verrouiller fige où l'on est, pas la version du
  plan — c'est ainsi que le module OLED a suivi la correction d'entraxe sans
  bouger d'un micron.
- `layout.py` — la table `P : ref -> (x, y, rot, face)`, organisée par zones.
  Le contour réel (relevé du polygone que KiCad referme) : corps pleine
  largeur seulement de y 120 à ~160, puis un fuseau qui s'effile jusqu'à la
  tête en arc. Les capteurs de ligne sont générés sur l'arc (r = 134,6, les
  deux extrêmes +0,15 mm pour la garde cuivre/bord) **et leurs passifs avec
  eux, face dessous** : ils étaient dessus à l'aplomb, ce qui coûtait trois
  vias par capteur et occupait la seule surface où la station de télémétrie
  avant pouvait tenir.
- `fit_layout.py` — contrôleur hors pcbnew : appartenance au polygone
  (marge 0,3 mm), collisions par paires (même face seulement), zones
  interdites (courtyards des équerres, quatre perçages du module OLED, trou
  de turbine). Les défauts sur pièces non figées sont résolus par poussées en
  spirale (0,5 puis 0,25 mm) ; le résultat va dans `layout_fit.json`, que
  `place_pcb.py` applique par-dessus la table.
- `place_pcb.py` — exporte la netlist, charge les empreintes, câble les nets,
  pose selon `layout` + `layout_fit.json`, répare les modèles 3D, puis
  réécrit `/tmp/board_geom.json` (tailles natives + polygone) pour la passe
  suivante de `fit_layout.py`.

**Boîtes orientées.** Les trois stations de télémétrie (20 × 19 mm posées à
15 / 45 / 75°) ne sont pas décrites par leur boîte
englobante droite : à 45° elle leur prêterait 27 × 27 mm et inventerait des
collisions avec la moitié de l'épaule. `fit_layout.py` les traite en
rectangles **orientés**, séparation par test SAT — exact, et sans les
approximations en norme L1 qui faisaient passer un trou de turbine distant de
33 mm pour une pénétration de 2 mm.

```sh
"$KPY" lock_import.py            # relève les verrous de pcbnew -> locked.json
python3 fit_layout.py            # controle + ajustements -> layout_fit.json
"$KPY" place_pcb.py --reset      # pose (KPY = python de KiCad)
cd .. && kicad-cli pcb drc --format json --severity-error -o /tmp/drc.json UsainBot.kicad_pcb
```

L'état de référence est **0 violation DRC** et **0 empreinte sans modèle 3D**
(`place_pcb.py` le vérifie et le dit à chaque passe). L'empreinte
`Pacabot:ITR8307_dessous` est la Everlight officielle **sans la fenêtre
Edge.Cuts** (capteur monté dessous, face au sol : pas de regard traversant).

## Zonage de la carte (refonte du 4 septembre)

Le principe : **chaque passif se pose contre son actif**. Les rangées de
résistances alignées loin de leur circuit ont disparu ; à leur place, une
grappe par fonction. Ce qui ne pouvait pas suivre — les passifs lents des
deux ponts en H, séparés de leur boîtier par le courtyard de l'équerre
moteur — est regroupé en un bloc unique par pont, pas dispersé.

| Zone | y | Contenu |
|---|---|---|
| Arrière | 120 → 133,7 | ponts en H aux angles + découplage, chargeur, USB, et à droite **pack XT30 vertical, équilibrage JST-XH vertical, deux gros perçages pour les fils de l'ESC** |
| Couloir | 133,7 → 143 | centrale inertielle au plus près du centre de rotation, broche unique de commande de l'ESC |
| Épaule ouest | 157 → 182 | passifs lents du pont gauche, configuration du chargeur, buzzer, module OTA |
| Épaule est | 157 → 185 | **convertisseur 3,3 V descendu de la bande arrière**, écrêtage VBAT, interrupteur général, station de télémétrie à 75° |
| IHM | 179 → 216 | écran sur entretoises, MCU dessous, **joystick et boutons à gauche**, télémètres à droite |
| Avant | 216 → 250 | chaînes analogiques, flash, mux de surveillance, témoins |
| Nez | 250 → 285 | station à 15° sur la passerelle, moustache et ses passifs **dessous**, **une LED de présence de ligne par capteur** sur la face avant de l'arc |

**Les passifs lents des ponts en H et du chargeur vivent DESSOUS**, à
l'aplomb exact de leur boîtier. Ils étaient exilés dans les épaules à trente
millimètres de leur circuit — l'équerre moteur occupe toute la bande
y 133,7-156,3 et il n'y avait pas d'autre place sur la face dessus. Il y en
avait une dessous, vide : trente millimètres deviennent trois via un via, et
les épaules respirent. La barrette de ligne prouvait déjà que la face
arrière s'assemble.

**Une LED de présence de ligne par capteur** (D401 à D412, `R_TEMOIN = 137`)
occupe la face avant de l'arc, à l'aplomb du capteur qu'elle rapporte : entre
le capteur (r 134,6, dessous) et le bord avant (r 139,9). Elles sont pilotées
en PWM par un **PCA9685 sur I2C2** (`U105`, sous la passerelle) : douze
rapports cycliques, **aucune broche de microcontrôleur consommée**, et la
ligne se lit d'un coup d'œil sous le robot. Les six témoins génériques d'avant
— trois rails, trois états — ont été rendus avec leurs trois GPIO ; deux des
trois bleues de suivi caméra aussi, la caméra gardant un triangle avec la
bleue restante et les deux rouges des coins arrière.

**La mise sous tension se fait par bouton poussoir** (`SW101` au bord
arrière). L'appui tire la grille des deux FET au 0 V par `D106` ; le firmware
met PE0 à 1 dès le démarrage, `Q104` tient la grille et le bouton peut être
relâché ; il lit ensuite le bouton sur PE1 et coupe en relâchant PE0 — après
avoir fermé la flash, ce qu'un interrupteur à glissière ne savait pas faire.
Toute cette électronique de grille vit **dessous**, à l'aplomb des deux FET :
quelques microampères, et la face dessus de cet angle est prise.

**La turbine est posée sur la carte** (`Pacabot:Turbine_EDF27_dessus`,
référence `M3`, table `MECA` de `place_pcb.py`). Elle n'y était pas : le
contour ne portait qu'un cercle ⌀32 tracé à la main, et **les trois vis M2
n'existaient nulle part** — rien ne la fixait. L'empreinte apporte les deux.
Son courtyard est la lèvre ⌀36,7 qui porte sur l'anneau de carte, soit
**r 18,6** : c'est cette valeur, et non le rayon du trou, qui commande ce
qu'on peut poser autour.

**Le microcontrôleur est passé en LQFP144 et vit DESSOUS** (4 septembre).
Le LQFP-100 se glissait sous l'écran, tourné à 45°, avec 0,17 mm de reste ;
le LQFP-144 demande 4 mm de plus dans chaque direction. La contrainte n'est
pas l'encombrement du module mais ce qui **traverse la carte** sous lui : la
rangée 1×4 à 10,85 mm au-dessus de son centre et les quatre entretoises à
±10,35. La fenêtre où le boîtier échappe aux trois obstacles commence à
y = 208,4, c'est-à-dire hors du module — et devant, cette place est prise par
la station de télémétrie à 45°.

Le boîtier est donc **en face arrière**, à (155 ; 216), posé à plat : la
rotation à 45° n'avait de sens que pour s'inscrire entre les quatre
entretoises. Ses douze condensateurs forment une couronne carrée autour de
lui, trois par côté à 13,5 mm de l'axe, soit 2 mm des pastilles. La face
avant garde juste au-dessus son quartz, ses VCAP et son groupe de reset :
1,6 mm par un via au lieu de plusieurs millimètres de cuivre en surface. La
station à 45° a dû remonter de 14 mm — son débord passe de 10 à 12 mm.

**La table de brochage est donnée par NOM DE PORT, jamais par numéro de
patte** (`MCU_PORTS` dans `design.py`). C'est ce qui a rendu la bascule
tenable : 85 des 87 affectations se sont transposées telles quelles, parce
qu'une affectation est un choix de port — PA0 porte la voie de ligne 00 — et
pas un choix de patte. Seuls les deux VCAP ont demandé un arbitrage. Les
broches absentes de la table sont marquées non connectées **automatiquement**
en fin de feuille : aucune ne peut être oubliée en silence, ce qui compte sur
un boîtier de 144.

**Le multiplexeur 74HC4051 a disparu.** Le LQFP144 apporte douze entrées ADC
de plus (PF3 à PF14) : VBAT_SENSE, IPROPI_L et IPROPI_R ont chacune la leur.
Et surtout **PF11 est ADC1_INP2 quand PF13 est ADC2_INP2** — même numéro de
voie sur deux convertisseurs, donc les deux courants moteur se lisent au même
instant en mode double simultané. Le multiplexeur l'interdisait par
construction.

## Empreintes specifiques (gen_fp.py)

- `Pacabot:OLED_096_I2C` — embase 1x4 + 4 percages M2 du module 0,96".
  Courtyard limite a l embase et aux percages : le module est sur
  entretoises (6 mm). Le MCU ne vit plus dessous : le LQFP144 n y tient pas
  (cf. plus haut). **Entraxes corriges le 4 septembre** : la carte du
  module a ete relevee au pied a coulisse a 27,0 x 24,7 (et non 27,3 x 27,8
  suppose), donc des entraxes de **23,0 x 20,7** au lieu de 23,3 x 23,8 —
  1,55 mm d'ecart sur les percages du haut et du bas, de quoi empecher les
  quatre entretoises de tomber en face. La mesure vit dans
  `mechanics/oled096_i2c.py`, qui produit aussi le modele 3D. Consequence :
  la rangee de broches remonte de 1,55 mm et arrivait a 0,17 mm des
  pastilles du LQFP — **le microcontroleur descend donc de 2,5 mm** sous le
  centre de l'ecran (cf. `layout.py`).
- `Pacabot:SKRHABE010` — joystick Alps 4 directions + appui, plan de pose
  releve du catalogue SKRH (pads 1,35 aux colonnes +/-3,575, pas 1,85,
  pattes 2x1,8 a +/-4,05, bossages 0,75/1,05). Pads numerotes comme le
  symbole SW_Nav_5Way ; directions A-D a recaler au firmware. **Pose a
  gauche de l'ecran**, les deux boutons dessous : on regarde l'ecran par
  l'arriere du robot, la main droite tombe sur les optiques de telemetrie
  qui occupent tout le flanc droit.
- `Pacabot:Telemetry_Duo` — perçage M2 seul, **plus utilisé** : les trois
  stations portent maintenant `Pacabot:Telemetry_Duo_Coude`, qui tient les
  deux boîtiers couchés, le pare-soleil et ses deux pions dans une seule
  empreinte (générateur dans `kicad-lib/`). Elle demandait un symbole à
  quatre broches — deux symboles ne peuvent pas se partager une empreinte :
  c'est `Pacabot:Telemetry_Duo` dans `gen_lib.py`, références `TM501`,
  `TM521`, `TM541`.
- `Pacabot:ESC_Multistar_10A` — le variateur de turbine **monté debout sur
  sa tranche, côté entrée de puissance**. Carte 22 × 12 mm (Turnigy
  MultiStar 10 A BLHeli-S Opto, 5,1 g) : posée sur le chant, elle ne prend
  plus que **12 × 5 mm au sol pour 22 mm de haut**, et la bande arrière
  n'offrait justement que 7,2 mm entre l'embase USB et le courtyard de
  l'équerre. Ses deux fils d'alimentation se soudent dans deux perçages
  ⌀2,0 au pas de 5,08 et le tiennent debout ; deux trous de collier bride
  le corps — deux soudures ne tiennent pas un porte-à-faux de 22 mm sur un
  robot qui freine à 8 g. Le PWM part sur `J702`, une broche **coudée**
  posée à côté, orientée vers l'arrière : le fil de commande descend du
  variateur à plat, sans boucle par-dessus le corps.
- `Pacabot:ITR8307_dessous` — Everlight officielle sans la fenetre
  Edge.Cuts (capteur dessous, face au sol).

## Modèles 3D

`kicad-lib/gen_3d_models.py` produit les boîtiers que KiCad 10 **déclare mais
ne livre pas** (USB-C HRO, Micro-MaTch TE, selfs Taiyo-Yuden NR, MSK12C02,
AMASS XT30U) plus le joystick Alps, le variateur debout et les quatre
entretoises de l'écran. Ce sont des modèles d'**encombrement** : les cotes hors-tout qui décident des collisions, pas le
détail du contact. `place_pcb.py` porte en plus une table de réparation des
chemins morts (le HTSSOP-16 et le HVQFN-24 existent sous un autre nom) et
refuse de finir en silence s'il reste une empreinte sans modèle.
