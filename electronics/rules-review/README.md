**Règles de conception JLCPCB 4 couches et classes de nets — 2 octobre 2026**

La carte est réglée pour une fabrication JLCPCB 4 couches **standard**, sans autre option
payante que la finition ENIG choisie par l'utilisateur : FR-4 de 1,6 mm (JLC04161H-7628),
cuivre externe 1 oz, interne 0,5 oz, via gratuite, pas de commande d'impédance. Rien n'est
routé ni déplacé. Point de départ : le commit `ef2d518` (état de l'utilisateur, format 10.99).

| Document | Contenu |
|---|---|
| [capacites-jlcpcb.md](capacites-jlcpcb.md) | capacités relevées le 02/10/2026, URL, marge retenue |
| [courants.csv](courants.csv), [courants.md](courants.md) | bilan des courants, source de chaque chiffre, points à confirmer |
| [calculs.md](calculs.md) | IPC-2152, vias, zones, chutes, paire USB, diaphonie |
| [classes.md](classes.md) | les 13 classes, motifs, réglages de l'autorouteur, liste exhaustive net → classe |
| [drc-avant.json](drc-avant.json), [drc-apres.json](drc-apres.json) | DRC du fork, `--severity-all`, lancé dans ce dossier de projet |
| `calc.py`, `check_classes.py` | calculs de largeur ; contrôle croisé du `.kicad_pro` |

## Ce qui a été écrit

- `UsainBot.kicad_pro` : planchers de la carte (piste et isolement 0,15 ; via ≥ 0,45 de
  pastille, trou ≥ 0,2, anneau ≥ 0,10 ; trou→cuivre et trou→trou 0,25 ; cuivre→bord 0,5
  inchangé ; sérigraphie 1,0 / 0,15) ; 13 classes avec couleurs et 43 motifs ; listes de
  largeurs (0,2 · 0,3 · 0,34 · 0,5 · 1,2 · 2,0), de vias (0,5/0,3 · 0,6/0,3) et de paire
  (0,34/0,20) ; étape et courant de chaque net pour l'autorouteur ; In1 fermée au routage.
- `UsainBot.kicad_dru` (nouveau) : 6 règles commentées — trou PTH→cuivre 0,35, PTH→PTH
  0,50, anneau PTH 0,20 (trous de composants > 0,3 mm seulement) ; analogique et quartz à
  0,65 mm des sources de bruit ; deux étranglements sous les composants à pastilles
  étroites.
- `UsainBot.kicad_pcb` : empilage JLC04161H-7628 (préimprégnés 0,2104 mm εr 4,4, cœur
  1,065 mm εr 4,6, cuivre interne 15,2 µm, vernis 15,2 µm εr 3,8) ; In1.Cu en type
  « power » (plan GND), In2.Cu en « mixed » ; pont de vernis minimal 0,13 mm (vernis noir).
  Aucune empreinte, aucune piste, aucune zone touchée.

Rôle des couches (accepté par l'utilisateur) : F.Cu signaux et puissance ; In1.Cu plan GND
plein ; In2.Cu alimentations (VBAT, VPACK, +3V3) et quelques signaux ; B.Cu signaux et
puissance.

## DRC avant / après

Les deux rapports ont été produits dans ce dossier de projet (bibliothèques du projet
visibles), avec le `kicad-cli` de `/Applications/KiCad Autorouter`. Le moteur plafonne
chaque type à 199 rapports (499 pour les isolements et les connexions) : les 199
« lib_footprint_issues » et les 499 connexions ouvertes sont des plafonds, identiques
avant et après.

| Type | Avant | Après | Explication |
|---|---|---|---|
| pad_no_room_at_class_width | 0 | 26 | attendu, voir ci-dessous |
| text_height | 16 | 30 | +14 : textes de J102, TM501/521/541, J601 sous 1,0 mm (minimum JLCPCB, était 0,8) |
| text_thickness | 0 | 20 | +20 : traits de J102, J103 et des 12 ITR8307 sous 0,15 mm (minimum JLCPCB, était 0,08) |
| silk_over_copper | 62 | 24 | même défauts, regroupés : avec un pont de vernis minimal de 0,13 mm, KiCad fusionne les ouvertures trop proches et compte par objet de sérigraphie |
| lib_footprint_issues, lib_footprint_mismatch, silk_overlap, silk_edge_clearance | 199, 14, 44, 9 | inchangés | antérieurs, hors du sujet |
| isolement, perçage, anneau, largeur | 0 | **0** | aucune violation de règle de cuivre |

Les 26 « pad_no_room » sont toutes des pastilles plus étroites que la largeur de leur
classe de puissance : QFN du chargeur (9), USB-C (2), SOT-583 du buck (2), HTSSOP des
ponts (6), SOT-23-6 de protection (1), C101, C104, C108, C114, C705, L102. Chacune est
couverte par une règle d'étranglement. Le contrôle du fork ne les voit pas : il évalue la
largeur de classe sur une piste-sonde placée hors de la carte, où une condition de
courtyard ne s'applique jamais. Ces avertissements disparaissent quand la pastille est
routée.

## Vérifications

- Chaque règle du `.kicad_dru` a été rendue extrême, ou confrontée à des pistes-sondes,
  sur une copie de la carte : toutes produisent des violations, aucune n'est morte. Deux
  pièges trouvés en chemin :
  - dans ce moteur, `X && Y || Z && W` sans parenthèses ne correspond à **rien** (règle
    morte sans erreur) ;
  - le moteur évalue les conditions dans les deux ordres (A, B) et (B, A) : une condition
    écrite dans un seul sens suffit.
- Une règle d'exception entre pastilles a été essayée puis retirée : sans elle, zéro
  violation pastille-pastille.
- Affectation des classes relue par KiCad lui-même (voir [classes.md](classes.md)).
- `check_classes.py` : chaque largeur, isolement, via, anneau et paire ≥ JLCPCB ; un net →
  une classe ; aucun motif mort ; les 277 nets ont leur réglage d'autorouteur.
- Empilage relu par `kicad-cli pcb export stackup`.
- Le schéma ne se charge pas dans le `kicad-cli` du fork (« malformed root sheet
  instance path ») : la vérification s'est faite sur les nets de la carte, qui sont à jour.

## Décisions et questions pour l'utilisateur

1. **Finition ENIG** : option payante chez JLCPCB, **conservée** (décision de
   l'utilisateur) ; c'est la seule option payante de la carte.
2. **Paire USB** : renommage des nets en `_P`/`_N` demandé, traité dans un commit suivant.
3. **Constats de schéma** (voir [courants.md](courants.md)) : codeurs IE2 à passer en
   5 V et R615/R617/R618 à passer en 0603 (demandés, commit suivant) ; F101 sans
   référence et calibré 12 A pour une branche de 3,9 A ; notes périmées (IIN 2,4 A,
   buck 2 A, I_TRIP).
4. **Turbine** : 10 A à confirmer par mesure.
