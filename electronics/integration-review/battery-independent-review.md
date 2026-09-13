# Revue indépendante batterie / interface ESC — 6 septembre 2026

Périmètre : lecture des schémas 01-power et 07-comms, contrôle de leur netlist exportée, empreinte et enveloppes Mega-Fit. Cette revue ne remplace pas le contrôle d’assemblage et de DRC de la carte finale, réalisé séparément. Les schémas et le PCB principaux n’ont pas été modifiés par cette revue.

## Résultat

La correspondance électrique attendue est confirmée par la netlist : J102 1=GND, 2=PACK_MID, 3=VPACK ; J103/ESC103 1=GND, 2=ESC_SIG, 3=VPACK. R707 100Ω relie PB8 du MCU (broche139) à ESC_SIG. ESC103 sorties4/5/6 vont uniquement à M703 phases1/2/3 ; ces deux symboles sont hors PCB. J103 représente les trois perçages sur la carte, exclu de BOM afin de ne pas compter deux fois le module. C704 est maintenant polarisé, 220µF/16V, positif1 sur VPACK, négatif2 sur GND ; C705 est également sur VPACK/GND. Les anciens J104/J702 ont disparu. Le titre du schéma alimentation annonce maintenant une chimie et des cellules à définir, en accord avec la clarification utilisateur.

Une erreur critique de la première version du **nouveau fichier de bibliothèque** a été trouvée puis corrigée avant synchronisation finale : les numéros moulés 1 et 3 de l’embase Mega-Fit étaient inversés. Avec verrou au nord, la face mâle d’accouplement / vue Top PCB porte **3 à gauche, 2 au milieu, 1 à droite**. La prise femelle regardée face accouplement avec verrou au nord présente 1 à gauche, 3 à droite. Les vues sont en miroir. Correction effectuée dans l’empreinte, sa sérigraphie et les étiquettes du modèle ; géométrie et origine inchangées. Parent averti qu’un rechargement de l’empreinte J102 dans le PCB est nécessaire.

Vérification par pcbnew du fichier corrigé : pad3 à(0,0), pad2 à(5.70,0), pad1 à(11.40,0), perçages1.80mm, cuivreØ2.70mm. Tétons NPTHØ3.00 à(2.85,1.34)/(8.55,1.34). Le dégagement nominal cuivre–NPTH minimal est0.2995mm. Le dessin source est côté composants ; les numéros sont déduits des marquages FIRST/LAST CKT des vues, indépendamment du sens de lecture du perçage.

Modèles STEP relus sous FreeCAD/Part : embase7solides valides, enveloppe femelle1solide valide. Embase hors-tout XYZ= (−3.18,−3.32,−3.23)…(14.57,7.28,17.50)mm. Enveloppe femelle= (−3.18,−4.02,15.30)…(14.57,7.98,30.90)mm. Le repère KiCad est X3D=Xempreinte et Y3D=−Yempreinte : les tétons sont àY3D−1.34 et le verrou nord versY3Dpositif. Les axes des contacts corrigés sont identiques aux trous. Ces STEP sont des enveloppes simplifiées documentées, pas des fichiers constructeur.

## Réserves électriques à conserver

- La capacité de24A du connecteur correspond à3circuits AWG12 dans les conditions de référence Molex (ΔT30°C, air calme) ; elle exige déclassement et essai dans le montage réel. Elle ne prouve pas la capacité du futur cuivre. Le budget19.5A continu/22.5A pointe découle d’un seul ESC et des deux limites DRV8874 actuelles, avant tolérances.
- VPACK brut laisse l’ESC alimenté quand le bouton coupe VBAT. F10112A protège seulement la branche carte/traction ; la protection pack/ESC doit encore être spécifiée avec les cellules. Les IPROPI ne mesurent pas le courant total batterie ; un plafond logiciel supposé22A ne constitue pas une protection globale sans cette mesure.
- Charge BQ25887 inhibée par défaut matériel ; chimie, cellules, capacité et firmware de charge non validés. La température pack est actuellement remplacée par un diviseur fixe. La mesure/équilibrage du point milieu reste reliée via R106/R107.
- **Observation R107 corrigée par le parent et vérifiée dans le schéma/la netlist : 47Ω/1W, empreinte2512 conservée.** L’ancienne10Ω/1W dissipait~1.46W à4.2V/cellule. La formule TI Ibal=Vcell/(R107+Rdson) donne maintenant87.5mA avec Rdson typ1Ω, soit0.360W dans R107. Une borne conservatrice à4.6V et Rdson nul donne0.450W (0.455W à−1% de R). Il reste à respecter le déclassement thermique de la résistance réelle. Ce choix réduit volontairement le courant et allonge la phase d’équilibrage si les cellules sont déséquilibrées ; la charge principale ne ralentit pas nécessairement. À titre d’ordre de grandeur,50mAh de déséquilibre demandent au moins34min à87.5mA, avant pauses de mesure. Le seuil automatique3.7V du BQ25887 confirme que l’ancienne hypothèseLiFePO4 n’est pas validée ; le profil Li-ion/LiPo doit suivre les cellules choisies.
- C70416V prépare la tension2S mais son MPN, courant ondulé et comportement transitoire ESC restent à choisir/valider. La géométrie ESC prototype et continuité petitGND/grosGND restent du ressort des mesures du module réel.

## Sources contrôlées

- [Molex embase2002411133](https://www.molex.com/en-us/products/part-detail/2002411133), [femelle2004561213](https://www.molex.com/en-us/products/part-detail/2004561213), [contacts1720631333](https://www.molex.com/en-us/products/part-detail/1720631333), [TPA1054150003](https://www.molex.com/en-us/products/part-detail/1054150003).
- [Plan mâle Molex2002411000C hébergé Farnell](https://www.farnell.com/cad/2867617.pdf) ; [plan femelle Molex2004561000E1 hébergéRS](https://docs.rs-online.com/df2b/A700000012778846.pdf), tous deux copiés dans battery-sources.
- [Spécification Molex1720631000-PS revD mars2026, §4.3](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/productspecificationpdf/172/172063/1720631000-PS-000.pdf?inline=).
- [TI BQ25887 revB, §8.3.4.3 page20](https://www.ti.com/lit/ds/symlink/bq25887.pdf).

## État exact examiné

- `01-power.kicad_sch` SHA256 `1ae6a18b3ef84dcb06adbb513451b5e84bf2d60b77fc9a62ab9dc5f2bdde6f3f`
- `07-comms.kicad_sch` SHA256 `520760be0e5c933b602e02c73bf4267ace4f1bd26440bf9f312a040ede387656`
- `integration-review/after-netlist.xml` SHA256 `ff607e438cd2adebbd0585dda378d40a9a7ebd6fce5af4490311ac8ee8228aab`
