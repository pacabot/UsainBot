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
firmware/         à venir : configuration STM32CubeMX du H723ZGT6, puis le code
mechanics/        sources FreeCAD du châssis, des supports et de la carte
documentation/    document d'architecture
rules/            règlement de l'épreuve
```

Les bibliothèques sont référencées en `${KIPRJMOD}/kicad-lib/…` : le dépôt se clone et
s'ouvre tel quel, sans chemin absolu ni variable d'environnement à déclarer.

## Architecture

Le document de conception — choix du microcontrôleur, schémas blocs, implantation,
élévations, affectation des broches, nomenclature JLCPCB et revue de conception en
trente-sept points — est ici (rédigé avant le passage au LQFP144 et au BPV10NF : le
schéma `electronics/UsainBot.pdf` fait foi là où ils divergent) :

**[`documentation/architecture-usainbot.html`](documentation/architecture-usainbot.html)**

| Fonction | Choix | JLCPCB |
|---|---|---|
| Microcontrôleur | STM32H723ZGT6, Cortex-M7 550 MHz, LQFP144 | `C730146` |
| Capteur de ligne | 12 × ITR8307/S17, pas 10 mm, émetteurs pulsés | `C81632` |
| Télémétrie | 3 × OPV302 + BPV10NF, détection synchrone | pose manuelle |
| Inertie | LSM6DSO, 6 axes, SPI | `C2655100` |
| Puissance moteurs | 2 × DRV8874, 6 A crête, retour de courant | `C1855818` |
| Motorisation | 2 × Faulhaber 1524T006SR + codeur IE2-1024 + réducteur 15/10 3,33:1 | hors carte |
| Charge | BQ25887, 2S élévateur depuis USB-C, équilibrage | `C2761614` |
| Alimentation | Pack 2S commun sur AMASS MR30, bus 5,0–7,3 V, buck 3,3 V | `C3200405` |
| Turbine | EDF 27 mm, ESC EMAX Bullet 12A monté debout | hors carte |

## Géométrie

La garde au sol vaut `rayon de roue − hauteur de l'axe moteur au-dessus du dessous de
carte`. Les roues JSumo JS4311 font 43 mm ; l'équerre usinée et trois cales de 1,6 mm
tirées du panneau de la carte placent l'axe à 16,50 mm au-dessus du dessous de carte, ce
qui donne **5,00 mm de garde**, dans la plage utile de l'ITR8307. Toutes les cotes
dérivent de `electronics/kicad-lib/faulhaber_geom.py` (détail dans
`electronics/kicad-lib/README.md`).

## Points ouverts

- **Pack commun 2S.** Cellules, capacité, chimie et protection générale à arrêter ; la
  recharge BQ25887 reste inhibée jusqu'à configuration et validation du firmware.
- **Montage de l'ESC.** L'empreinte `EMAX_Bullet_12A_Vertical_3Pin_PROTOTYPE` est tirée
  de photographies : mesurer pads, épaisseur et continuités de masse sur l'ESC réel avant
  fabrication.

- **Départ par télémètre.** Le chapitre 2 du règlement énumère trois moyens de départ —
  interrupteur, bouton poussoir, jack — et cette liste se lit comme limitative. Question à
  poser aux organisateurs ; un bouton physique conforme est conservé en secours.
- **Porteuse de la télémétrie.** À choisir hors de la bande de scintillement des
  éclairages et à l'écart des 38 kHz des barrières de chronométrage, avec un codage propre
  au robot pour la réjection par corrélation. À caler sur plaque d'essai. Rester à 12 mA :
  monter en fréquence pour débloquer les 48 mA de l'OPV302 ne change pas la puissance
  moyenne, donc pas la portée — les deux régimes donnent 1,26 mW. Le seul levier de portée
  est la surface du récepteur.
- **Inclinaison des diodes.** 4° vers le haut, soudées à plat sur la carte. Le rayon bas du
  faisceau monte alors de 35 mm par mètre et n'atteint jamais la bâche, mais le centre passe
  au-dessus d'un cube de 100 mm au-delà d'environ un mètre.
- **Approvisionnement.** OPV302 et BPV10NF ne sont probablement pas dans la bibliothèque
  JLCPCB : pose manuelle des six composants de la languette à prévoir.
- **Poussée de la turbine.** À mesurer sous 6,4 V et non sous les 8,4 V pour lesquels les
  ensembles ESC et brushless du commerce sont calibrés.

## Contenu tiers

- `rules/Reglement-Formule-1-v2.11.pdf` — règlement rédigé par Frédéric Giamarchi et
  Jean-Roch Vaillé pour le Tournoi National de Robotique Sumo. Publié sur
  [robot-sumo.fr](https://robot-sumo.fr), reproduit ici pour le confort de travail de
  l'équipe. Tous droits réservés à leurs auteurs.
- `electronics/kicad-lib/3d/vendor/*.stp` — modèles Faulhaber du moteur 1524 et du
  réducteur 15/10. Provenance dans `electronics/kicad-lib/3d/vendor/README.md`.
