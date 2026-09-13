# ITR8307/S17/TR8(B) — empreinte et revue mécanique indépendante

La référence C81632 est **ITR8307/S17/TR8(B)**. Le suffixe B est le rang optique, sans changement du dessin mécanique S17. La variante S17 est un CMS gull-wing normal ; l’empreinte ITR8307 standard avec encastrement et son STEP étaient inadaptés. **Aucune fenêtre PCB n’est nécessaire** pour S17 sur Bottom, face optique vers le sol. Réduire une fenêtre ou déroger à la clearance bord traiterait la mauvaise variante.

Source primaire exacte : [Everlight Europe, DRX-0000322 rev6, page2](https://www.everlighteurope.com/custom/files/datasheets/DRX-0000322.pdf), obtenu depuis la [fiche produit S17](https://www.everlighteurope.com/product-details?category=Optical+Sensors&id=4043&name=ITR8307/S17/TR8). PDF conservé ici. Corps3.4±0.2 ×2.7±0.2mm, hauteur1.5(+0.2/0), portée totale des pattes4.6±0.2, pieds0.50 ×0.38, entraxe des deux voies1.80. Le corps est au-dessus du plan des pieds de0.12±0.05mm. Tolérance générale non précisée individuellement±0.15mm.

## Nouvelle empreinte

`Pacabot:ITR8307_S17_TR8_Bottom` est une bibliothèque **F.Cu standard**, à retourner sur B.Cu. Les références, centres, rotations et verrouillages du PCB doivent être conservés lors du remplacement. Seuls le boîtier, les lands locaux et le modèle sont corrigés pour la référence déjà choisie.

|Pad|Fonction|X,Y locaux bibliothèque (mm)|
|---|---|---|
|1|Cathode LED|−0.90,+2.11|
|2|Anode LED|−0.90,−2.11|
|3|Collecteur|+0.90,+2.11|
|4|Émetteur|+0.90,−2.11|

Le dessin frontal fabricant est tourné de90° horaire dans le plan : ses broches4/3 en haut et2/1 en bas deviennent4 en haut-droite,3 en bas-droite,2 en haut-gauche,1 en bas-gauche. Cela conserve l’orientation fonctionnelle de l’ancienne empreinte. Chanfrein côté2. Les centres des pieds sont calculés par4.6/2−0.38/2=2.11mm ; X=±1.8/2. En PCB Bottom, KiCad réalise le miroir géométrique usuel sans changer les fonctions des broches.

Lands **1.20×1.40mm**, coins arrondis20%, largeur/longueur conservées de l’empreinte projet mais centres rapprochés de0.69mm. C’est un land pattern de projet déduit du dessin, **pas un pattern publié par Everlight**. Nominalement le débord latéral est0.35mm et le débord longitudinal0.51mm par côté autour du pied ; pied de largeur maximale0.65mm→débord0.275mm. La séparation cuivre entre pads d’une même rangée est0.60mm. Aucune piste ou position de composant n’est changée dans ce fichier de bibliothèque.

Fab3.4×2.7mm, courtyard X±2.10/Y±3.10mm ; il inclut le corps maximal et au moins0.25mm autour des pads. Sans Edge.Cuts. Modèle `${KIPRJMOD}/kicad-lib/3d/Everlight_ITR8307_S17_TR8.step`, offset/rotation nuls, construit séparément par l’agent mécanique avecY3D=−Yempreinte. Chargement pcbnew et vérification des quatre numéros/positions réalisés.

À contrôler après remplacement réel : distances aux passifs Bottom et cuivreTop, absence de court-circuit nets, modèleBottom et direction optique. Une pose d’échantillon et l’accord assembleur sur ce pattern restent utiles avant fabrication ; aucune réduction de clearance bord n’est requise.
