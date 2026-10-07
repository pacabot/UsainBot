# Capacités JLCPCB retenues — 4 couches standard

Relevé du **2 octobre 2026**. Les pages ont été téléchargées puis converties en texte ; une
valeur « vue » est écrite telle quelle sur la page, une valeur « déduite » est calculée ou
interprétée à partir d'elle.

Sources :

| Repère | Page |
|---|---|
| [C] | https://jlcpcb.com/capabilities/pcb-capabilities |
| [I] | https://jlcpcb.com/impedance |
| [Q] | https://cart.jlcpcb.com/quote (textes d'aide des options) |
| [L] | https://jlcpcb.com/help/article/multi-layer-pcb-standard-laminated-structures (mise à jour du 09/09/2026) |
| [U] | https://jlcpcb.com/help/article/User-Guide-to-the-JLCPCB-Impedance-Calculator (mise à jour du 16/09/2026) |
| [X] | https://jlcpcb.com/help/article/in-what-cases-will-there-be-charged-extra (mise à jour du 09/09/2026) |
| [S] | https://jlcpcb.com/help/article/jlcpcb-surface-finish (mise à jour du 09/09/2026) |

« Standard » = FR-4 1,6 mm, cuivre externe 1 oz, interne 0,5 oz, plus petite via sans
surcoût, pas d'impédance contrôlée payante (confirmé par l'utilisateur le 02/10/2026).

## Empilage

L'empilage « No requirement » de [I], pris quand on ne précise rien, est numériquement
identique au **JLC04161H-7628** (vu) :

| Couche | Matériau | Épaisseur (mm) | εr | Source |
|---|---|---|---|---|
| Vernis | encre | 0,0152 sur cuivre, 0,0305 sur stratifié | 3,8 | [I], [U] |
| F.Cu | cuivre 1 oz | 0,035 | — | [I] |
| préimprégné | 7628 × 1 | 0,2104 | 4,4 | [I], [L] |
| In1.Cu | cuivre 0,5 oz | 0,0152 | — | [I], [U] |
| cœur | FR-4 (NP-155F) | 1,065 | 4,6 | [I], [L] |
| In2.Cu | cuivre 0,5 oz | 0,0152 | — | [I], [U] |
| préimprégné | 7628 × 1 | 0,2104 | 4,4 | [I], [L] |
| B.Cu | cuivre 1 oz | 0,035 | — | [I] |

Total ≈ 1,59 mm hors vernis (déduit). Le cuivre interne 0,5 oz par défaut est vu sur [C]
et [Q] ; [U] le modélise à 0,6 mil = 15,2 µm (et non 17,5 µm nominaux) : c'est la valeur
retenue pour les calculs, elle est prudente. [L] précise que les épaisseurs et les εr sont
des valeurs après pressage. Variante JLC04161H-3313 (préimprégné 0,0994 mm, εr 4,1) : non
retenue, rien n'indique en statique qu'elle soit sans surcoût.

## Valeurs

| Paramètre | JLCPCB | Vu / déduit | Retenu pour la carte | Marge |
|---|---|---|---|---|
| Piste / isolement mini (multicouche, 1 oz) | 0,09 / 0,09 mm [C] | vu | plancher 0,15 / 0,15 | ×1,67 |
| Surcoût piste fine | +20 % entre 3,0 et 3,5 mil (0,076–0,089 mm) [X] | vu | hors zone (≥ 0,15) | — |
| Tolérance de largeur | ±20 % [C] | vu | — | — |
| Pastille CMS → pastille, nets différents | 0,15 mm [C] | vu | pas de règle : fixé par les empreintes | égal au LGA-14 de l'IMU (0,15) ; 0,20 au LQFP, au QFN, à l'USB-C |
| Pastille → piste | 0,10 mm [C] | vu | ≥ 0,15 | ×1,5 |
| Via sans surcoût | trou ≥ 0,3 et pastille ≥ 0,4 ; ou trou 0,2 et pastille ≥ 0,45 en multicouche [Q] | vu | vias des classes : trou 0,3, pastille 0,5 (signaux) ou 0,6 (puissance) ; plancher : pastille 0,45 | pastille +25 % |
| Via la plus petite (payante) | 0,15 / 0,25 [C] | vu | interdite | — |
| Anneau de via | pastille = trou + 0,1 (0,15 préféré) [C] | règle vue, anneau 0,05 / 0,075 déduit | 0,10 mini | ×1,33 sur le préféré |
| Anneau PTH (1 oz) | 0,15 absolu, 0,20 recommandé [C] | vu | 0,20 | = recommandé |
| Trou PTH | 0,15 à 6,3 mm, ≥ 0,5 recommandé [C] | vu | plancher 0,2 : vias thermiques du QFN U102 (0,2 / 0,5, gratuites en multicouche) | — |
| Tolérance de perçage PTH | +0,13 / −0,08 [C] | vu | — | — |
| Trou de via → trou de via | 0,2 [C] | vu | 0,25 | +25 % |
| Trou PTH → trou PTH | 0,45 [C] | vu | 0,50 | +11 % |
| Trou de via → piste | 0,2 [C] | vu | 0,25 | +25 % |
| Trou PTH → piste | 0,28 mini, 0,35 recommandé [C] | vu | 0,35 | = recommandé |
| Trou de via → cuivre interne | 0,2 [C] | vu | 0,25 | +25 % |
| Trou PTH → cuivre interne | 0,3 [C] | vu | 0,35 | +17 % |
| Cuivre → bord fraisé | 0,2 [C] | vu | 0,5 (inchangé, déjà respecté) | ×2,5 |
| Pont de vernis, 1 oz | 0,10 vert ; **0,13 noir ou blanc** [C] | vu | 0,13 (la carte est en vernis noir) | égal |
| Ouverture de vernis | 1:1, LDI [C] | vu | expansion 0 (inchangée) | — |
| Sérigraphie | trait ≥ 0,15, hauteur ≥ 1,0 [C] | vu | 0,15 / 1,0 | égal |
| Métallisation des trous | 18 µm en moyenne, aucun minimum publié [C] | vu | 18 µm dans les calculs de vias | — |
| Tolérance d'impédance | ±10 % [C] ; ±20 % en test gratuit [L] | vu, contradictoire | aucune commande d'impédance | — |
| Épaisseur de carte | ±10 % [C] | vu | — | — |

## Points qui touchent au coût

- **Finition ENIG** : la carte déclare `ENIG` dans l'empilage. [S] : « ENIG incurs a
  substantial surcharge per square meter » ; c'est donc une option payante, **conservée
  par choix de l'utilisateur** (surface plane pour le LGA-14 et les QFN). C'est la seule
  option payante retenue.
- **Vernis noir** : seul un délai de deux jours de plus est écrit sur [Q] ; le prix n'est
  pas visible en statique. Il porte le pont de vernis minimal à 0,13 mm.
- **Via dans la pastille** : par défaut à partir de 6 couches [C] ; non utilisée.
- **Impédance contrôlée** : la méta-description de [I] dit « at no extra charge », sans
  confirmation sur le devis. La paire USB est dimensionnée sur l'empilage par défaut, sans
  commande d'impédance.

## Limites du relevé

- La page [C] est dynamique ; le relevé a été fait sur le texte téléchargé. Aucune valeur
  ci-dessus n'a été supposée : celles qui manquaient sont signalées comme absentes.
- La tolérance d'impédance (±10 % contre ±20 %) et le prix du vernis noir sont à
  confirmer auprès de JLCPCB si cela devient décisif.
