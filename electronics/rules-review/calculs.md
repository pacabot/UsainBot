# Calculs — largeurs, zones, vias, chutes de tension, paire USB, diaphonie

Les entrées (courants, longueurs) viennent de [courants.md](courants.md) et du placement
du 2 octobre 2026 (commit `ef2d518`). Les capacités de fabrication viennent de
[capacites-jlcpcb.md](capacites-jlcpcb.md). Les hypothèses sont séparées des résultats.

## 1. Méthode de largeur : IPC-2152

### Hypothèses

- **Courbe de base** : figure 5-2 d'IPC-2152 (« universal chart », pistes internes et
  externes, air calme, sans plan), sous la forme ajustée par L. Rozenblat d'après les
  coefficients de J. Olson (https://www.smps.us/pcb-calculator.html) :

  `A [mil²] = (117,555 · ΔT^−0,913 + 1,15) · I^(0,84 · ΔT^−0,108 + 1,159)`

  Contrôle publié : 10 A, 20 °C → 513 mil² (formule) contre ≈ 500 à 520 lus sur le graphe.
  La figure 5-2 couvre 5 à 700 mil² ; au-delà (10 A sous 10 °C) la formule extrapole.
- **Correcteurs** de J. Olson (« Determining Circuit Board Current Carrying Capability »,
  p. 5-9, https://frontdoor.biz/HowToPCB/HowToPCB-extra/HowTo2152.pdf) : cuivre 1 oz
  ×0,84 ; FR-4 ×1,02 ; carte de 0,062 in ×1,08. Produit : ×0,925. Le même ×0,84 est
  appliqué au cuivre interne 0,5 oz faute de correcteur publié pour cette épaisseur.
- **Pas de crédit de plan** : le plan GND d'In1 est à 0,21 mm sous F.Cu et réduit
  nettement l'échauffement (Olson : ×0,47 sur la section pour un plan 1 oz à 20 mil ;
  Brooks et Adam : ΔT ×0,36 pour un plan à 10 mil sous une piste de 200 mil). Notre plan
  est en 0,5 oz : aucun facteur publié ne s'y applique directement. Il reste donc une
  marge non chiffrée, et les largeurs ci-dessous sont prudentes.
- **Échauffement** : ΔT = 10 °C en continu, 20 °C en crête courte (accord de
  l'utilisateur du 02/10/2026).
- **Épaisseurs** : externe 35 µm, interne 15,2 µm (valeur du calculateur JLCPCB).
- **Cuivre** : ρ20 = 1,7241 µΩ·cm, α = 0,00393 /K (IPC-TM-650 2.5.14A §4.2) ; chutes
  calculées à 40 °C. Brooks et Adam citent des mesures jusqu'à +40 % sur ρ selon la
  fabrication : les chutes ci-dessous en sont l'ordre de grandeur, pas une borne.

### Résultats : largeur par courant (une seule couche, sans crédit de plan)

| I (A) | ΔT 10 °C : externe 1 oz | ΔT 10 °C : interne 0,5 oz | ΔT 20 °C : externe 1 oz | ΔT 20 °C : interne 0,5 oz | IPC-2221 externe, 10 °C (contrôle) |
|---|---|---|---|---|---|
| 0,5 | 0,08 | 0,17 | 0,04 | 0,10 | 0,12 |
| 1 | 0,26 | 0,61 | 0,15 | 0,34 | 0,30 |
| 1,5 | 0,55 | 1,27 | 0,31 | 0,71 | 0,53 |
| 2 | 0,93 | 2,14 | 0,51 | 1,17 | 0,78 |
| 2,5 | 1,39 | 3,21 | 0,76 | 1,74 | 1,06 |
| 3 | 1,94 | 4,47 | 1,04 | 2,40 | 1,37 |
| 4 | 3,27 | 7,53 | 1,73 | 3,99 | 2,03 |
| 5 | 4,90 | 11,29 | 2,57 | 5,92 | 2,77 |
| 6,5 | 7,89 | 18,18 | 4,09 | 9,41 | 3,97 |
| 10 | 17,24 | 39,71 | 8,75 | 20,15 | 7,19 |
| 13 | 27,76 | 63,91 | 13,91 | 32,04 | 10,33 |

Largeurs en mm. Sous 1 A, la figure 5-2 est hors de sa plage et donne moins
qu'IPC-2221 : on retient alors la plus grande des deux. Au-delà d'environ 3 A, la largeur
dépasse ce qu'une pastille de boîtier peut recevoir : le courant passe par des **zones**,
et la classe ne porte que la largeur des raccords.

Le tableau se régénère avec `python3 calc.py` (ce dossier).

## 2. Vias

### Hypothèses

- Via retenue : **trou 0,3 mm**, pastille 0,5 mm (signaux) ou 0,6 mm (puissance), sans
  surcoût chez JLCPCB (trou ≥ 0,3 et pastille ≥ 0,4).
- Métallisation : 18 µm en moyenne (JLCPCB, aucun minimum publié). Brooks rappelle qu'elle
  est souvent irrégulière dans le fût.
- Méthode IPC-2152 (A.3.4, cité par Brooks et Adam, « Via Currents and Temperatures »,
  2015) : la section du fût doit valoir au moins celle de la piste qui y arrive, sinon on
  met plusieurs vias. Brooks et Adam jugent cette règle « extremely conservative » : un via
  court entouré de diélectrique chauffe moins qu'une piste de même section.

### Résultats

- Section du fût : π · t · (d − t) = π × 0,018 × (0,300 − 0,018) = 0,0159 mm² = **24,7 mil²**
  (équivalent d'une piste 1 oz de 0,46 mm).
- Résistance d'un via de 1,6 mm : 1,7 mΩ.
- Contrôle croisé avec `via_current.cpp` du fork (IPC-2221 externe, section π·d·t,
  ΔT 10 °C) : **1,41 A par via** de 0,3 mm. C'est la valeur que l'autorouteur utilise pour
  ajouter des vias à côté de chaque via routé d'un net dont la classe porte un courant.

| Courant à faire passer | Section IPC-2152, 10 °C | Vias (règle de section) | Section IPC-2152, 20 °C | Vias (règle de section) | Vias selon le fork (1,41 A/via) |
|---|---|---|---|---|---|
| 1 A | 14,4 mil² | 1 | 8,1 mil² | 1 | 1 |
| 2 A | 50,5 mil² | 3 | 27,6 mil² | 2 | 2 |
| 3 A | 105,3 mil² | 5 | 56,6 mil² | 3 | 3 |
| 6,5 A | 428 mil² | 18 | 222 mil² | 9 | 5 |
| 10 A | 936 mil² | 38 | 475 mil² | 20 | 8 |

Lecture : une sortie moteur ou le raccord VBAT d'un pont (1,42 A au blocage) demande
2 vias sous 10 °C par la règle de section ; le fork en pose 2 pour MOTEUR (courant de
classe 1,5 A) et 3 pour VBAT (3,9 A). Le départ du tronc VBAT (3,9 A) en demande 7 : ce
sont des vias de couture de zone, posées à la main (§6). Le chemin 10 A n'a pas de
changement de couche : MR30 et ESC sont traversants, le courant passe sur toutes les
couches sans via (voir §3).

## 3. Chemin 10 A : MR30 → ESC et retour GND

### Hypothèses

- Courant de dimensionnement de la turbine : **10 A continus** (décision de l'utilisateur du
  02/10/2026, au lieu des 12 A continus / 15 A crête de l'ESC EMAX Bullet 12A).
- Le courant de la branche VBAT (ponts moteurs + buck) ne passe pas par l'ESC : il quitte
  VPACK au fusible F101. Le retour GND porte les deux : 10 A + branche VBAT (2,3 A en
  continu, 3,9 A au pire, voir [courants.md](courants.md)), soit **12,3 A, 13,9 A au pire**
  sous la MR30.
- Longueurs mesurées sur le placement (centre à centre) : J102.3 → J103.3 = 25,0 mm ;
  J102.1 → J103.1 = 23,2 mm ; J102.3 → F101.1 = 27,4 mm.

### Résultats

| Chemin | Courant | Section de cuivre IPC-2152 (ΔT 10 °C) | Exemple de répartition | Chute à 40 °C |
|---|---|---|---|---|
| VPACK, J102.3 → J103.3 | 10 A | 0,60 mm² | 8,6 mm sur F.Cu + 8,6 mm sur B.Cu (35 µm) | 7,7 mV |
| GND, J103.1 → J102.1 | 10 A (ESC seul) | 0,60 mm² | plan In1 entier + bandes F.Cu/B.Cu | 7,1 mV |
| GND, sous la MR30 (ESC + VBAT) | 13,9 A (pire cas) | 1,11 mm² | plan In1 (≈ 20 mm utiles × 15,2 µm) + 2 × 12 mm en F.Cu/B.Cu | 5,4 mV à 13,9 A |

Une piste n'a pas de sens ici : **le chemin MR30 → ESC est une zone VPACK sur F.Cu et une
sur B.Cu** (plus In2 si la place manque), entre pastilles traversantes, donc sans
changement de couche ni via sur le chemin du courant. GND : plan plein In1 plus zones GND
sur F.Cu et B.Cu autour de la MR30, de l'ESC et des ponts. L'addition des sections de
couches parallèles est une approximation : les couches se chauffent mutuellement, et le
plan GND d'In1, à 0,21 mm, refroidit les zones de F.Cu (crédit non compté, voir §1).

Point de vigilance du placement : entre la MR30 (x ≈ 164–172) et l'ESC (x ≈ 140–148),
à y ≈ 133, se trouvent l'USB-C J101, la protection U101 et R101/R102. Les deux zones de
puissance devront contourner ce groupe ou passer dessous par B.Cu et In2 : les 0,60 mm²
sont un objectif de section, pas une largeur à tenir sur une seule couche.

## 4. Paire USB 2.0 pleine vitesse

### Hypothèses

- Cible : 90 Ω différentiel ±15 % (USB 2.0) ; à 12 Mb/s c'est souhaitable, pas critique.
  Aucune commande d'impédance contrôlée.
- Paire en microruban sur F.Cu, référencée au plan GND d'In1 : h = 0,2104 mm, εr = 4,4,
  t = 35 µm (JLC04161H-7628).
- Calculateur : bibliothèque `common/transline_calculations` de KiCad (coupled
  microstrip, Kirschning-Jansen), compilée telle quelle, 100 MHz. Ce modèle ne compte pas
  le vernis (εr 3,8, 15 µm sur le cuivre), qui abaisse l'impédance de quelques ohms.

### Résultats

| Largeur / écart (mm) | Zdiff sans vernis (Ω) |
|---|---|
| 0,20 / 0,20 | 119,0 |
| 0,30 / 0,20 | 99,0 |
| 0,32 / 0,20 | 95,8 |
| **0,34 / 0,20** | **93,0** |
| 0,35 / 0,20 | 91,6 |
| 0,36 / 0,20 | 90,3 |
| 0,38 / 0,20 | 87,7 |

Retenu : **0,34 mm / 0,20 mm** (93 Ω sans vernis, ≈ 90 Ω une fois le vernis compté),
dans ±15 %. Aux bornes de la tolérance de largeur JLCPCB (±20 %, entraxe constant de
0,54 mm), le calcul donne 79,4 Ω (0,408 / 0,132) et 108,5 Ω (0,272 / 0,268) sans vernis :
le pire cas sort légèrement de ±15 %. La liaison U101 → U201 fait ≈ 71 mm à vol d'oiseau
(U101.6 en 153,6/134,3, U201.104 en 157,8/204,7), soit ≈ 0,45 ns de propagation, petite
devant les fronts de 4 à 20 ns de la pleine vitesse : l'écart d'impédance y est sans
conséquence. Le préimprégné 7628 épais impose des pistes larges : la paire doit se
rétrécir aux pastilles de l'USB-C (0,30 mm au pas de 0,5) et du LQFP.

Point bloquant pour le routeur de paires : KiCad ne reconnaît une paire que par des noms
en `_P`/`_N` ou `+`/`-`. `USB_DP`/`USB_DM` et `/Alimentation/USB_DP_C`/`USB_DM_C` ne
sont donc pas vus comme des paires : la classe porte la largeur et l'écart, mais le
routeur de paires du fork ne s'en servira pas tant que les nets ne sont pas renommés
(proposition : `USB_D_P`/`USB_D_N` et `USB_C_D_P`/`USB_C_D_N`, à faire dans le schéma).

## 5. Diaphonie : isolement entre analogique et sources de bruit

### Hypothèses

- Couplage entre deux microrubans parallèles sur un plan (H. Johnson et M. Graham,
  *High-Speed Digital Design*, 1993, chapitre 5) : proportionnel à 1 / (1 + (D/H)²),
  D = distance entre pistes, H = hauteur au-dessus du plan.
- H = 0,2104 mm (F.Cu → In1, et B.Cu → In2 si In2 porte un plan sous la piste).
- Victimes : TIA (220 kΩ), réseaux de gain, références, IPROPI, retour du buck, entrées
  CAN, quartz. Agresseurs : nœuds de commutation (SW_CHG, SW_BUCK), amorçage et pompes de
  charge, sorties moteur, émetteurs pulsés, chemin de puissance du chargeur.

### Résultats

| D | D/H | Couplage relatif (D = 0 → 1) |
|---|---|---|
| 0,15 mm (isolement de base) | 0,71 | 0,66 |
| 0,30 mm | 1,43 | 0,33 |
| **0,65 mm** | **3,09** | **0,095** |
| 1,00 mm | 4,75 | 0,042 |

Retenu : **0,65 mm ≈ 3 H** entre les classes ANALOGIQUE/HORLOGE et les classes de bruit,
soit un couplage divisé par 7 par rapport à l'isolement de base. La règle exclut les
paires de pastilles (l'écart entre pastilles est fixé par les empreintes) : elle ne
contraint que le cuivre routé et les zones. Elle exempte aussi les courtyards des boîtiers
qui portent les deux domaines sur des broches voisines (chargeur et buck U102/U103, ponts
U301/U351, capteurs TM501/521/541) : sans cette exemption, le contrôle d'échappement du
fork montrait que la broche SS du buck (entre BST et FB) ne pouvait plus être raccordée
du tout. Dans ces courtyards, l'éloignement se gère à la main, en sortant les pistes
analogiques du côté opposé au nœud de commutation.

## 6. Résultat par classe

Courants de [courants.md](courants.md) ; largeur = celle de la classe (raccords) ; ΔT par
la méthode du §1 sur F.Cu ou B.Cu (35 µm), sans crédit de plan.

| Classe | Largeur | Courant continu → ΔT | Courant crête → ΔT | Remarque |
|---|---|---|---|---|
| PACK | 1,2 mm | 1,5 A (charge) → 4 °C | 2,2 A (ICHG maxi) → 9 °C | tronc 10 A en zones (§3) ; branche F101 en zone (ci-dessous) |
| VBAT | 0,5 mm | 1,0 A (un pont) → 5 °C | 1,42 A (blocage) → 10 °C | tronc 3,9 A en zone sur In2 (ci-dessous) |
| MOTEUR | 0,5 mm | 1,0 A → 5 °C | 1,42 A → 10 °C | 10,6 mm de U301.8 à J301.2 : 16 mV à 1,42 A |
| CHARGEUR | 2,0 mm | 2,4 A → 6 °C | 3,0 A → 10 °C | VBUS : 31 mm de J101 à U102, 25 mV à 3 A |
| COMMUTATION | 2,0 mm | 3,0 A (SW_CHG) → 10 °C | 3,5 A → 13 °C | F.Cu seule, sans via ; surface minimale |
| AMORCAGE | 0,3 mm | mA | 0,1 A en impulsions | largeur pour l'inductance, pas pour le courant |
| ALIM_LOGIQUE | 0,3 mm | 0,35 A → < 1 °C | 1,2 A (cumul +3V3) → 13 °C | distribution par In2 ; la piste ne porte qu'une broche |
| GND | 0,3 mm | raccords de pastille | — | plan plein In1 ; zones F.Cu/B.Cu (§3) |
| IMPULSION | 0,3 mm | 0,06 A | 0,126 A (banc IR) | largeur pour l'inductance de boucle |
| ANALOGIQUE, HORLOGE, Default | 0,2 mm | ≤ 25 mA | — | — |
| USB | 0,34 mm | — | — | impédance (§4) |

### Zones à dessiner au routage

| Zone | Couche(s) | Courant | Largeur mini IPC-2152 (ΔT 10 °C) | Chute |
|---|---|---|---|---|
| VPACK MR30 → ESC | F.Cu + B.Cu (+ In2) | 10 A | 0,60 mm² : 8,6 mm sur chaque couche externe | 7,7 mV sur 25 mm |
| VPACK MR30 → F101 | F.Cu | 3,9 A | 3,1 mm (ou 7,2 mm sur In2) | — |
| VBAT Q102/Q103 → ponts et buck | In2 (+ F.Cu près des AO4407A) | 3,9 A au départ | 7,2 mm sur In2 au départ ; 1,2 mm par pont, 0,5 mm vers le buck | 66 mV à 3,9 A sur 100 mm en 7,2 mm |
| GND | In1 plein + F.Cu/B.Cu autour de MR30, ESC, ponts | 13,9 A | 1,11 mm² sous la MR30 | 5,4 mV |
| +3V3 | In2 | 1,2 A | 0,3 mm suffisent au courant ; la zone sert la distribution | — |

Le pont gauche (U301) est à 100 mm des AO4407A : une branche In2 de 1,2 mm y perdrait
145 mV à 1,42 A ; une branche de 3 mm ramène la chute à 58 mV. Pas de contrainte de
tension (VM ≥ 4,5 V pour le DRV8874, pack ≥ 5,0 V), mais la largeur reste à prendre
généreuse sur In2, qui est en 0,5 oz.

Changements de couche : la zone VBAT d'In2 est reliée aux drains des AO4407A et aux broches
VM par des vias. Règle de section IPC-2152 (§2) : 3,9 A sous 10 °C → **7 vias** de 0,3 mm au
départ des AO4407A ; 1,42 A → 2 vias à chaque pont (le fork en pose 3 par changement de
couche, la classe VBAT portant 3,9 A). Ces groupes de vias se posent à la main avec la
zone : ce sont des vias de couture, pas des vias de routage.
