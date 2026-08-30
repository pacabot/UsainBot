# UsainBot

Robot suiveur de ligne de l'équipe **Pacabot**, conçu pour l'épreuve **Formule 1** du
Tournoi National de Robotique Sumo (règlement v2.11, 2025).

Course de vitesse contre la montre sur circuit fermé : ligne noire de 19 mm sur bâche
blanche, rayon de virage minimum de 200 mm, lignes droites jusqu'à 6 m. Trois phases de
qualification, de difficulté croissante — Q3 piste nue, Q2 avec un cube de 100 mm à
éviter sans contact, Q1 avec en plus un virage à gauche escamoté et un mur de 100 mm de
haut placé à 150 mm à gauche de l'axe de la piste absente.

## Architecture

Le document de conception complet — choix du microcontrôleur, schémas blocs, implantation,
élévations, affectation des broches, nomenclature JLCPCB et revue de conception — est ici :

**[`Documentation/architecture-usainbot.html`](Documentation/architecture-usainbot.html)**

En résumé :

| Fonction | Choix | JLCPCB |
|---|---|---|
| Microcontrôleur | STM32H723VGT6, Cortex-M7 550 MHz, LQFP100 | `C730142` |
| Capteur de ligne | 12 × ITR8307, pas 10 mm, émetteurs pulsés | `C81632` |
| Télémétrie | 2 × VL53L1X + 1 voie analogique rapide à gauche | `C2970716` |
| Inertie | LSM6DSO, 6 axes, SPI | `C2655100` |
| Puissance moteurs | 2 × DRV8874, 6 A crête, retour de courant | `C1855818` |
| Charge | BQ25887, 2S élévateur depuis USB-C, équilibrage | `C2761614` |
| Alimentation | Pack 2S LiFePO4, bus 5,0–7,3 V, buck 3,3 V | `C3200405` |

## Organisation du dépôt

```
UsainBot/            projet KiCad (schéma, PCB, table de bibliothèques)
UsainBot.ioc         configuration STM32CubeMX
kicad-lib/           empreintes et modèles 3D propres au projet
  Pacabot.pretty/    empreintes mécaniques
  3d/                modèles STEP des moteurs, supports et roues
Mecanique/           sources FreeCAD du châssis, des supports et de la carte
Documentation/       document d'architecture
Reglements/          règlement de l'épreuve
```

Les chemins de bibliothèque sont exprimés en `${KIPRJMOD}/../kicad-lib/…` : le dépôt se
clone et s'ouvre tel quel, sans variable d'environnement à déclarer.

## Points ouverts

- **Diamètre de roue et garde au sol.** La bibliothèque 3D contient une roue Pololu
  40 × 7 mm. Or la garde au sol vaut `rayon de roue − hauteur de l'axe moteur au-dessus du
  dessous de carte`, soit environ 9 mm avec des roues de 40 mm — au-delà de la plage utile
  de l'ITR8307, qui travaille entre 2 et 4 mm. À trancher avant de router : roues plus
  petites, support moteur rehaussé, ou capteurs déportés.
- **Départ par télémètre.** Le chapitre 2 du règlement énumère trois moyens de départ
  (interrupteur, bouton poussoir, jack) et cette liste se lit comme limitative. Question à
  poser aux organisateurs ; un bouton physique conforme est conservé en secours.
- **Approvisionnement du télémètre analogique.** OPV302 et BPW77 ne sont probablement pas
  dans la bibliothèque JLCPCB ; pose manuelle à prévoir, ou repli sur un VL53L1X.

## Contenu tiers

- `Reglements/Reglement-Formule-1-v2.11.pdf` — règlement rédigé par Frédéric Giamarchi et
  Jean-Roch Vaillé pour le Tournoi National de Robotique Sumo. Publié sur
  [robot-sumo.fr](https://robot-sumo.fr), reproduit ici pour le confort de travail de
  l'équipe. Tous droits réservés à leurs auteurs.
- `Mecanique/battery-holder-4xaa-1.snapshot.1/` — modèle de porte-piles téléchargé,
  conservé pour référence. Devenu sans objet depuis le passage à un pack 2S LiFePO4.
- `kicad-lib/3d/GM12-N20_*.step` — dérivés du modèle Waveshare du motoréducteur.
  Voir `kicad-lib/README.md` pour la provenance et les réserves de cotation.
