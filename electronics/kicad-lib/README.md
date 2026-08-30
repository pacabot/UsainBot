# Bibliothèque KiCad — UsainBot

## Motor_GM12-N20_Bracket

Empreinte **mécanique** (aucune connexion électrique) du moteur GM12-N20 6 V 1:30
monté sur son support N20/N30.

- Origine = **milieu des deux trous de fixation**
- Axe moteur suivant **Y**, arbre de sortie vers **−Y**
- Face avant du support **6,00 mm en retrait** de la face de sortie d'axe
- 2 trous non métallisés **Ø 2,2 mm** (M2 avec jeu), **entraxe 18,00 mm**
- Emprise totale : X ±12,75 mm, Y −22,45 → +17,85 mm (40,30 mm de long)
- `F.Fab` : contour support + corps moteur + arbre — `F.SilkS` : support seul

Régénérer après une mesure : éditer les constantes en tête de
`gen_motor_footprint.py` puis `python3 gen_motor_footprint.py`.

## Symboles (`Pacabot.kicad_sym`)

Neuf symboles absents des bibliothèques KiCad, ou dont le typage de broches
rendait l'ERC inexploitable. Régénérer avec `../tools/gen_lib.py`.

| Symbole | Pourquoi il est là |
|---|---|
| `DRV8874PWPR` | KiCad ne fournit que les DRV8870/71/72. Brochage HTSSOP-16 saisi depuis la fiche TI SLVSF66A : `EN/IN1` 1, `PH/IN2` 2, `nSLEEP` 3, `nFAULT` 4, `VREF` 5, `IPROPI` 6, `IMODE` 7, `OUT1` 8, `PGND` 9, `OUT2` 10, `VM` 11, `VCP` 12, `CPH` 13, `CPL` 14, `GND` 15, `PMODE` 16, pad thermique 17 |
| `AO4407A` | Canal P SO-8 pour la protection anti-inversion. Les `Q_PMOS_*` de KiCad n'ont que trois broches : impossible de les faire correspondre aux 1-3 source / 4 grille / 5-8 drain du boîtier |
| `LSM6DSOTR` | Copie de `Sensor_Motion:LSM6DS3` — même LGA-14, même brochage. `SDX` et `SCX` retypées en passif : elles sont strappées à la masse, et les laisser bidirectionnelles fait crier l'ERC sans raison |
| `ITR8307` | Copie de `Sensor_Proximity:ITR8307-S17-TR8`, phototransistor retypé en passif. « Collecteur ouvert » relié à un rail est un défaut d'ERC alors que c'est exactement le montage voulu |
| `SW_Nav_5Way` | Switch 5 directions à commun unique. **Empreinte à confirmer** sur la référence retenue (LCSC C3674) : le champ est laissé vide exprès |
| `VBAT` `VPACK` `+3V3A` `+3V3_BLE` | Symboles d'alimentation des quatre rails propres au projet |

### Réserve

Le `VL53L1CBV0FY/1` utilise le symbole standard `Sensor_Distance:VL53L1CXV0FY1`
et l'empreinte `Sensor_Distance:ST_VL53L1x`. Même boîtier optique et même
brochage ; seule la valeur a été changée. À revérifier si le composant
réellement approvisionné n'est pas un CB.

## Modèles 3D (`3d/`)

Six fichiers STEP **colorés**, déjà positionnés sur l'origine de l'empreinte
(offset et rotation à 0 dans le `.kicad_mod`, rien à régler dans KiCad).

| Fichier | Couleur | Origine |
|---|---|---|
| `GM12-N20_bracket.step` | blanc ABS | `n20_motor_mounting_bracket001` de `../motorHolder.fcstd` |
| `GM12-N20_motor_gearbox.step` | laiton | STEP Waveshare, faces à Y ≥ 16,07 (réducteur + arbre) |
| `GM12-N20_motor_can.step` | nickel | STEP Waveshare, faces à 1,0 ≤ Y < 16,07 |
| `GM12-N20_motor_encoder.step` | sombre | STEP Waveshare, faces à Y < 1,0 |
| `Pololu_wheel_40x7_hub.step` | blanc | STEP officiel Pololu, faces à r ≤ 18,3 mm |
| `Pololu_wheel_40x7_tire.step` | noir | STEP officiel Pololu, faces à r > 18,3 mm |

La roue est le modèle officiel Pololu du 40×7 mm **blanc** — exactement la
référence 1454 achetée. Séparation moyeu/gomme au rayon 18,25 mm, d'après le
plan coté Pololu : moyeu Ø36,5 mm, hors-tout Ø40,0 mm.

Position de la roue : emmanchée à fond, face extérieure au bout d'arbre.

### Couleurs

KiCad 10 n'utilise plus que du STEP (aucun `.wrl` livré) : la couleur doit être
portée par le fichier lui-même. FreeCAD en mode console ne sait pas les écrire —
pas de `ViewObject`. Les entités `COLOUR_RGB` / `STYLED_ITEM` sont donc ajoutées
en post-traitement par `colorize_step.py`, sur le même motif que les modèles
livrés avec KiCad. Pour changer une teinte : éditer `PALETTE` en tête du script,
régénérer le STEP concerné, puis relancer `python3 colorize_step.py`.

## Provenance des cotes

| Cote | Valeur | Source |
|---|---|---|
| **Entraxe des trous** | **18,00 mm** | vue de dessus de la datasheet Handson `GA12-N20-Bracket.pdf` — **confirmé au pied à coulisse sur la pièce réelle** |
| Diamètre des trous | M2 (écrou hexagonal) | datasheet — porté à 2,20 mm sur la carte pour le jeu |
| Largeur hors-tout | 25,00 mm | datasheet |
| Profondeur | 11,50 mm | datasheet (dont 8,50 mm pour la zone des oreilles) |
| **Retrait support / face de sortie d'axe** | **6,00 mm** | **mesuré sur le montage réel** |
| Section moteur | 10 × 12 mm | plan coté Waveshare + STEP |
| Longueur totale moteur | 40,30 mm | STEP Waveshare |
| Arbre | Ø3 mm, méplat D 2,5 mm, 9,2 mm | STEP Waveshare |

## Réserves

1. **Le 3D du support ne correspond pas exactement à la pièce réelle.**
   `n20_motor_mounting_bracket001` (extrait de `../motorHolder.fcstd`) mesure
   27,50 mm de large pour un entraxe de 18,50 mm, alors que la pièce achetée
   fait 25,00 mm pour 18,00 mm d'entraxe. C'est un modèle téléchargé, pas un
   relevé de la pièce. **L'empreinte est juste** (cotes datasheet vérifiées au
   pied à coulisse) ; seul le rendu 3D est indicatif, avec 0,25 mm d'écart par
   trou et 1,25 mm par côté.

2. **Attention au texte de la datasheet Handson** : son résumé annonce
   « *Pitch: about 16 mm* », ce qui est faux. La cote de 18,0 mm portée sur la
   vue de dessus, dont les lignes d'attache aboutissent au centre des logements
   d'écrou, est la bonne.

3. **Le 3D du moteur est un Waveshare DCGM-N20-12V-EN-200RPM (12 V, 1:150)**,
   pas le GM12-N20 6 V 1:30 réellement acheté. Même famille et mêmes cotes
   d'enveloppe, mais le bloc encodeur en bout diffère : le modèle porte un
   connecteur ZH1.5-6PIN là où la pièce réelle a un faisceau.

4. Le bloc encodeur du modèle descend à Z = −0,41 mm (très légèrement sous le
   plan de la carte) et culmine à Z = 18,50 mm.

5. Le sens de montage du support est **confirmé** : la face à 7,25 mm de l'axe
   des trous est bien côté arbre. Le support serre le **corps du moteur**, pas le
   réducteur — il couvre 3,03 mm de réducteur et 8,47 mm de moteur.
