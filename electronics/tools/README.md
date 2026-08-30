# Générateur du schéma

Les huit `*.kicad_sch` de `electronics/` et la bibliothèque
`kicad-lib/Pacabot.kicad_sym` sont **produits par ces scripts**, à partir du
brochage et des choix de composants du document d'architecture.

```sh
python3 gen_lib.py      # kicad-lib/Pacabot.kicad_sym  (puis normalisé par kicad-cli)
python3 design.py       # UsainBot.kicad_sch + 01-power … 07-comms
```

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
| `gen_lib.py` | les neuf symboles propres au projet |
| `design.py` | les sept feuilles et la feuille racine |

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
- deux tronçons colinéaires de nets différents qui se recouvrent, ou une
  extrémité qui tombe au milieu d'un fil étranger — le court-circuit
  géométrique, invisible à l'œil sur une feuille A3 ;
- un composant ou une note qui tombe dans le cartouche ;
- deux boîtes englobantes qui se recouvrent — corps, référence, valeur,
  étiquette, symbole d'alimentation, note. Un texte écrit par-dessus un boîtier
  ne casse rien électriquement et ne sera donc jamais signalé par l'ERC, mais
  rend la feuille illisible.

Ces contrôles ne remplacent pas l'ERC, ils attrapent ce qui, sans eux,
n'apparaîtrait qu'après coup dans la netlist. L'état de référence est
**0 erreur, 0 avertissement** :

```sh
cd .. && kicad-cli sch erc --severity-all UsainBot.kicad_sch
```

Le contrôle `single_global_label` est activé dans `UsainBot.kicad_pro` : une
étiquette globale qui n'apparaît qu'une fois est une faute de frappe, pas un
signal.
