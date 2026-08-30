# UsainBot

Robot suiveur de ligne de l'équipe **Pacabot**, conçu pour l'épreuve **Formule 1** du
Tournoi National de Robotique Sumo (règlement v2.11, 2025).

Course de vitesse contre la montre sur circuit fermé : ligne noire de 19 mm sur bâche
blanche, rayon de virage minimum de 200 mm, lignes droites jusqu'à 6 m. Trois phases de
qualification, de difficulté croissante — Q3 piste nue, Q2 avec un cube de 100 mm à
éviter sans contact, Q1 avec en plus un virage à gauche escamoté et un mur de 100 mm de
haut placé à 150 mm à gauche de l'axe de la piste absente.

## Organisation

```
electronics/      projet KiCad — schéma, PCB, table de bibliothèques
  kicad-lib/      empreintes et modèles 3D propres au projet
firmware/         configuration STM32CubeMX, puis le code
mechanics/        sources FreeCAD du châssis, des supports et de la carte
documentation/    document d'architecture
rules/            règlement de l'épreuve
```

Les bibliothèques sont référencées en `${KIPRJMOD}/kicad-lib/…` : le dépôt se clone et
s'ouvre tel quel, sans chemin absolu ni variable d'environnement à déclarer.

## Architecture

Le document de conception complet — choix du microcontrôleur, schémas blocs, implantation,
élévations, affectation des broches, nomenclature JLCPCB et revue de conception en
trente-sept points — est ici :

**[`documentation/architecture-usainbot.html`](documentation/architecture-usainbot.html)**

| Fonction | Choix | JLCPCB |
|---|---|---|
| Microcontrôleur | STM32H723VGT6, Cortex-M7 550 MHz, LQFP100 | `C730142` |
| Capteur de ligne | 12 × ITR8307, pas 10 mm, émetteurs pulsés | `C81632` |
| Télémétrie | 2 × VL53L1X + 1 voie analogique rapide à gauche | `C2970716` |
| Inertie | LSM6DSO, 6 axes, SPI | `C2655100` |
| Puissance moteurs | 2 × DRV8874, 6 A crête, retour de courant | `C1855818` |
| Charge | BQ25887, 2S élévateur depuis USB-C, équilibrage | `C2761614` |
| Alimentation | Pack 2S LiFePO4, bus 5,0–7,3 V, buck 3,3 V | `C3200405` |

## Géométrie

La garde au sol vaut `rayon de roue − hauteur de l'axe moteur au-dessus du dessous de
carte`. Avec les roues Pololu 40 × 7 retenues et le support N20 nu, l'axe est à 11 mm et
la garde serait de 9 mm — au-delà de la plage utile de l'ITR8307, qui travaille entre 2 et
4 mm. **Quatre millimètres d'entretoises sur mesure** sous le support portent l'axe à
15 mm et ramènent la garde à 5 mm.

Conséquence à répercuter : le décalage en Z des modèles 3D du moteur et du support, dans
`electronics/kicad-lib/Pacabot.pretty/`, devra suivre l'épaisseur d'entretoise retenue.

## Points ouverts

- **Départ par télémètre.** Le chapitre 2 du règlement énumère trois moyens de départ —
  interrupteur, bouton poussoir, jack — et cette liste se lit comme limitative. Question à
  poser aux organisateurs ; un bouton physique conforme est conservé en secours.
- **Approvisionnement du télémètre analogique.** OPV302 et BPW77 ne sont probablement pas
  dans la bibliothèque JLCPCB : pose manuelle à prévoir, ou repli sur un VL53L1X.
- **Poussée de la turbine.** À mesurer sous 6,4 V et non sous les 8,4 V pour lesquels les
  ensembles ESC et brushless du commerce sont calibrés.

## Contenu tiers

- `rules/Reglement-Formule-1-v2.11.pdf` — règlement rédigé par Frédéric Giamarchi et
  Jean-Roch Vaillé pour le Tournoi National de Robotique Sumo. Publié sur
  [robot-sumo.fr](https://robot-sumo.fr), reproduit ici pour le confort de travail de
  l'équipe. Tous droits réservés à leurs auteurs.
- `mechanics/battery-holder-4xaa-1.snapshot.1/` — modèle de porte-piles téléchargé,
  conservé pour référence. Sans objet depuis le passage à un pack 2S LiFePO4.
- `electronics/kicad-lib/3d/GM12-N20_*.step` — dérivés du modèle Waveshare du
  motoréducteur. Voir `electronics/kicad-lib/README.md` pour la provenance et les réserves
  de cotation.
