# Règles de routage — largeurs, isolations, empilage

État du **13 septembre 2026**. Les règles ci-dessous sont **enregistrées dans le projet KiCad** : classes de nets et affectations dans `UsainBot.kicad_pro`, règles contextuelles dans `UsainBot.kicad_dru`, empilage dans `UsainBot.kicad_pcb`. **Aucune piste, via ou zone n'a été ajoutée.**

Reproduire : `python3 tools/routing_rules.py --apply` (calcul ≈ 4 min, puis écriture). `tools/apply_routing_rules.py` seul réécrit les fichiers sans recalculer ; il est idempotent.

## 1. Empilage : JLCPCB JLC04161H-3313, 1,6 mm

Relevé sur [jlcpcb.com/impedance](https://jlcpcb.com/impedance) le 13/09/2026.

| Couche | Épaisseur | εr | Rôle retenu |
|---|---|---|---|
| F.Cu | 35 µm (1 oz) | — | composants, puissance (VPACK, VBAT, moteurs), USB |
| préimprégné 3313 | 0,0994 mm | 4,1 | |
| In1.Cu | **15,2 µm (0,5 oz)** | — | **plan de masse continu**, sans coupure |
| cœur | 1,27 mm | 4,6 | |
| In2.Cu | **15,2 µm (0,5 oz)** | — | plan d'alimentation : VBAT large à l'arrière, +3V3, îlot 3V3A sous l'analogique |
| préimprégné 3313 | 0,0994 mm | 4,1 | |
| B.Cu | 35 µm (1 oz) | — | signaux, recopie VPACK/GND en parallèle de F.Cu |

L'ancien empilage déclarait 35 µm en couches internes. **Chez JLCPCB, le 4 couches standard a 15,2 µm à l'intérieur** : les couches internes ne portent pas les forts courants. Le 3313 est préféré au 7628 : 0,1 mm entre F.Cu et la masse raccourcit les boucles des ponts et des convertisseurs, divise la diaphonie et donne une paire USB routable.

## 2. Largeurs selon les courants

Méthode : **IPC-2221B**, I = k·ΔT^0,44·A^0,725 (A en mil², k = 0,048 externe, 0,024 interne), **ΔT = 20 °C au courant continu**. Cette formule est plus sévère que l'IPC-2152 pour une carte de 1,6 mm à plans : la marge est implicite.

| Classe | Nets | Courant continu / pic | Calcul externe | **Largeur de routage** | Mini DRC* |
|---|---|---|---|---|---|
| PUISSANCE_PACK | VPACK | 15,5 A / 18,5 A | 8,65 mm sur 1 couche ; 3,32 mm par couche sur 2 | **3,5 mm sur F.Cu + 3,5 mm sur B.Cu** | 1,0 mm |
| PUISSANCE_VBAT | VBAT, VBAT_SW_IN | 7,5 A / 12 A (F101) | 3,18 mm ; 3,71 mm au pic à ΔT 45 °C | **3,2 mm** | 1,0 mm |
| MOTEUR_3A | MOT_L/R_OUT1/2 | 3,0 A / 6,0 A | 0,90 mm ; 1,43 mm au pic à ΔT 45 °C | **1,0 mm** | 0,9 mm |
| CHARGEUR_3A | VBUS_IN, PMID, SW_CHG, SNS_CHG | 3,0 A / 4,0 A | 0,90 mm | **1,0 mm** | 0,9 mm |
| BUCK_2A | SW_BUCK | 2,0 A / 3,0 A | 0,51 mm | **0,6 mm** | 0,5 mm |
| RAIL_3V3 | +3V3 | 1,0 A / 2,0 A | 0,20 mm | **0,4 mm** + plan In2 | 0,2 mm |
| FAIBLE_300mA | +3V3A, +3V3_BLE, bancs IR, lasers, buzzer, PACK_MID | 0,3 A | 0,04 mm | **0,25 mm** | 0,2 mm |
| MASSE | GND | retours | plans et zones | **0,5 mm** pour les liaisons | 0,2 mm |
| ANALOGIQUE | PD, TIA, G, CG, FB, AMP, VREF, RX, LINE, IPROPI, VREF_MOT, VBAT_SENSE, quartz | < 1 mA | — | **0,2 mm** | 0,15 mm |
| USB_90R | USB_DP/DM, USB_DP_C/DM_C | — | impédance | **0,18 mm, écart 0,20 mm** | 0,17–0,19 mm |
| Default | tout le reste | < 25 mA | — | **0,15 mm** | 0,15 mm |

\* Le minimum DRC ne s'applique **qu'en dehors des courtyards** : on peut rétrécir une piste à l'entrée d'une pastille fine (QFN 0,25 mm, HTSSOP 0,45 mm), jamais sur le parcours.

Origine des courants :

- **VPACK.** ESC 12 A continus et 15 A en pointe, plus deux moteurs à 1 A et 1,5 A d'électronique : c'est le budget du [dossier MR30](../mr30-review/README.md). Le trajet J102 → J103 porte l'ESC, et J102 → F101 la branche carte.
- **VBAT.** Deux limites ITRIP de 3,0 A et 1,5 A d'électronique. Le pic est borné par le fusible F101 de 12 A.
- **Moteurs.** ITRIP = VREF / (A_IPROPI × R_IPROPI) = 1,34 V / (450 µA/A × 1 kΩ) = 3,0 A, régulé par le DRV8874. Le seuil de 6 A est sa protection de surintensité. Le courant réel vaut 1 A.
- **Chargeur.** R103 = 383 Ω fixe environ 2,4 A d'entrée, auxquels s'ajoute l'ondulation. L101 est prévue pour 4 A.
- **Buck.** TPS62933 prévu pour 2 A au schéma, 3 A au maximum, avec L102 à 3 A.
- **Faible courant.** Un banc IR allume 6 émetteurs à (3,3 − 1,2) V / 100 Ω ≈ 21 mA, soit 126 mA. Chaque laser tire 12 mA et l'équilibrage 88 mA.

Chutes calculées à 45 °C :

| Tronçon | Géométrie | R | Chute | Pertes |
|---|---|---|---|---|
| VPACK J102 → J103 (26 mm, 12 A) | 3,5 mm × 2 couches | 2,0 mΩ | 24 mV | 0,29 W |
| VBAT Q102 → U301 (100 mm, 3 A) | 1,0 mm externe | 54 mΩ | **162 mV** | 0,49 W |
| même tronçon | 2,0 mm externe | 27 mΩ | 81 mV | 0,24 W |
| même tronçon | bande In2 de 10 mm | 12,5 mΩ | 37 mV | 0,11 W |

Le pont gauche est à 100 mm des MOSFET de coupure. **Porter VBAT par une large bande In2**, doublée d'une piste externe de 2 mm, plutôt que par une piste de 1 mm.

### Vias

Le fût est traité comme un conducteur interne, avec 18 µm de métallisation supposée. JLCPCB publie une épaisseur moyenne, pas un minimum : la valeur est à confirmer.

| Via | Courant à ΔT 10 °C | Courant à ΔT 20 °C | Usage |
|---|---|---|---|
| 0,3 / 0,6 mm | 0,74 A | 1,00 A | signaux, découplage |
| 0,4 / 0,8 mm | 0,90 A | 1,22 A | puissance (imposé par la DRC sur les classes ≥ 2 A) |

Nombre minimal de vias 0,4 / 0,8 mm à chaque changement de couche :

| Classe | Vias |
|---|---|
| VPACK | 16 |
| VBAT | 8 |
| Moteur, par sortie | 4 |
| Chargeur, par net | 4 |
| Buck | 3 |
| Pastille thermique DRV8874 (≈ 2 W à 3 A) | ≥ 9 vias de 0,3 mm vers In1 et B.Cu |

## 3. Isolations selon les signaux

**Tension.** Tous les nets restent sous 15 V : 8,4 V sur VPACK, 5 V sur VBUS, 3,3 V ailleurs. L'IPC-2221B, tableau 6-1, demande alors au plus **0,13 mm** (pattes de composants nues, catégorie A6). Le fabricant accepte 0,09 mm. La tension n'impose donc rien au-delà du **défaut de 0,15 mm**. Les classes de puissance prennent 0,20 mm pour la tolérance de gravure des pistes larges et le pontage de soudure.

**Couplage.** C'est lui qui fixe les isolations. Avec h = 0,0994 mm, la diaphonie entre microrubans suit environ 1 / (1 + (s/h)²) :

| Espacement bord à bord | 0,15 mm | 0,3 mm | 0,5 mm | 1,0 mm |
|---|---|---|---|---|
| Couplage relatif | 30 % | 10 % | 3,8 % | 1,0 % |

Règles écrites dans `UsainBot.kicad_dru`, toutes hors courtyards :

| Règle | Isolation | Nets |
|---|---|---|
| Nœuds commutés | 0,3 mm | SW_BUCK, SW_CHG, BST_BUCK, BTST, sorties moteur, pompes de charge DRV, BUZZ_D, IR_BANK_x_N |
| Analogique | 0,3 mm | classe ANALOGIQUE (règle 3W pour 0,15 mm) |
| Entrées TIA 220 kΩ | 0,5 mm | PD_*, TIA_* : fuites et couplage capacitif sur nœud haute impédance |
| Agresseurs contre analogique | **1,0 mm** | commutation, porteuses TX_*, TXAC_*, LAS_*, ESC contre toute la classe ANALOGIQUE |
| USB : écart de paire | 0,19 mm minimum | USB_90R |
| USB : garde aux autres nets | 0,3 mm | USB_90R |
| Zones (défaut nouvelles zones) | 0,3 mm | toutes |
| Bord de carte / trou | 0,5 mm / 0,25 mm | inchangés |

Des pistes volontairement fautives ont été posées sur une copie de la carte. Les largeurs minimales et maximales, les vias de puissance, la garde USB, les nœuds commutés et l'éloignement de 1 mm ont produit l'erreur attendue. Les règles analogique 0,3 mm et TIA 0,5 mm utilisent la même syntaxe mais n'ont pas été déclenchées isolément.

## 4. Impédance USB

Un solveur de Laplace 2D en différences finies intégré à `routing_rules.py` calcule l'impédance. Il tient compte du masque et de l'épaisseur du cuivre. Validation sur un microruban nu de 0,20 mm : **50,5 Ω**, contre 50,3 Ω par la formule de Hammerstad.

| Largeur / écart | 0,17 / 0,18 | 0,18 / 0,18 | **0,18 / 0,20** | 0,19 / 0,20 | 0,20 / 0,20 |
|---|---|---|---|---|---|
| Zdiff (Ω) | 91,0 | 88,5 | **89,7** | 86,1 | 83,8 |

Retenu : **0,18 mm / 0,20 mm sur F.Cu, référencés à In1**, sans changement de couche et sans coupure de plan dessous. Une piste simple de 0,15 mm fait 53 Ω.

KiCad reconnaît une paire différentielle aux suffixes `P`/`N` ou `+`/`-`. Les noms `USB_DP` et `USB_DM` n'en font pas partie : l'outil de routage de paire ne les associera pas. Renommer les nets en `USB_D_P` et `USB_D_N` dans le générateur de schéma avant le routage, ou router les deux pistes à la main aux cotes ci-dessus.

## 5. Ce qui a changé dans le projet

- **Empilage.** Cuivre interne ramené à 15,2 µm, préimprégné 3313 de 0,0994 mm (εr 4,1), cœur de 1,27 mm (εr 4,6).
- **Classes de nets.** Dix classes créées, avec couleurs, et 39 motifs d'affectation. L'affectation a été relue par l'API KiCad, net par net.
- **Règles de carte.** Isolation minimale 0,15 mm, au lieu de 0. Piste minimale 0,15 mm, au lieu de 0,20 mm, alors que la classe par défaut routait déjà en 0,15 mm. Trou minimal 0,2 mm, pour les vias thermiques de l'empreinte du BQ25887.
- **Valeurs prédéfinies.** Largeurs, deux vias (0,6 / 0,3 et 0,8 / 0,4 mm) et la paire 0,18 / 0,20 mm.
- **Fichier de règles.** `UsainBot.kicad_dru` a été créé. Les valeurs y portent l'unité « mm », car KiCad lit un nombre sans unité en nanomètres.
- **DRC.** Le résultat est identique avant et après : 0 erreur et 181 avertissements hérités, surtout de la sérigraphie. Le rapport est dans `drc-apres-regles.json`.

## 6. Autoroutage

**Recommandation : [Freerouting](https://github.com/freerouting/freerouting) 2.4.1**, publié le 3 septembre 2026. Il est libre et gratuit, et prend en entrée le format Specctra DSN que KiCad exporte.

- **Vérifié ici.** Le binaire Linux, livré avec son Java 25, démarre. Le `.jar` seul refuse de tourner sous le Java 21 installé : il faut installer Java 25.
- **Export vérifié.** L'export DSN de KiCad 10 transmet bien les dix classes avec leurs largeurs et isolations.
- **Limite.** Freerouting ignore `UsainBot.kicad_dru`. Il faut **relancer la DRC KiCad** après import de la session `.ses`.

Méthode conseillée sur cette carte :

1. **À la main d'abord.** Zones VPACK et GND sur F.Cu et B.Cu avec leurs rangées de vias, plan In1 et bandes In2, boucles des convertisseurs et des ponts, paire USB, TIA et quartz. Verrouiller ces pistes.
2. **Exporter.** Fichier > Exporter > Specctra DSN.
3. **Router.** Par exemple `freerouting -de UsainBot.dsn -do UsainBot.ses -mp 100`, en excluant les classes de puissance avec `-inc`.
4. **Réimporter et contrôler.** Importer la session, remplir les zones, puis lancer la DRC.

Alternatives commerciales, en nuage, qui annoncent l'import KiCad sur leur page :

- **[Quilter](https://www.quilter.ai/).** Placement et routage « physics-aware », offre gratuite annoncée, déploiement hébergé possible.
- **[DeepPCB](https://deeppcb.ai/).** Greffon KiCad, paiement à l'usage.

Pour les deux, il faut accepter d'envoyer le projet sur un service tiers. Leurs tarifs ne sont pas détaillés sur les pages consultées.

## Réserves

- **Métallisation des vias.** Les 18 µm sont supposés. JLCPCB ne publie qu'une moyenne.
- **Fusible F101.** Un 1206 de 12 A limite la surface de cuivre à sa pastille. Son échauffement réel au courant de roulage reste à vérifier sur la fiche du composant choisi.
- **Retour de masse de l'ESC.** Les 12 A ne doivent pas passer par In1, trop fin avec 15,2 µm. Doubler la zone GND sous VPACK sur F.Cu et B.Cu, entre J102 et J103.
- **Courants retenus.** Ce sont des enveloppes de dimensionnement : limites des circuits intégrés, fusible, budget ESC. Ce ne sont pas des mesures. Les essais thermiques restent nécessaires.
