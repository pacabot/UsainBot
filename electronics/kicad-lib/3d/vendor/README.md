# Modèles d'origine constructeur

Fichiers **téléchargés tels quels**, jamais édités. Les modèles utilisés par
l'empreinte sont produits à partir d'eux par `../../gen_faulhaber_3d.py`, qui ne
fait que les transposer dans le repère de l'empreinte.

| Fichier | Source | Contenu |
|---|---|---|
| `1524T_SR.stp` | [`1524_SR_3D-CAD.zip`](https://eshop.faulhaber.com/media/3c/f9/7c/1755610716/1524_SR_3D-CAD.zip) | moteur 1524T…SR nu, arbre Ø1,5 |
| `15-10K_1stage.stp` | [`15-10_3D-CAD.zip`](https://eshop.faulhaber.com/media/47/49/d8/1755624128/15-10_3D-CAD.zip) | réducteur 15/10**K** une étage, roulements préchargés |
| `15-10_1stage.stp` | idem | variante paliers frittés, gardée pour comparaison |

Publiés par Dr. Fritz Faulhaber GmbH & Co. KG sur `eshop.faulhaber.com`, page
produit, rubrique « 3D-CAD Files ». Reproduits ici pour que la chaîne de
génération tourne sans accès réseau. Tous droits réservés à leur auteur.

## Ce qu'on en a tiré

Les deux STEP sont la **référence de cotation** du projet : `../../faulhaber_geom.py`
ne contient que des valeurs relevées sur ces solides, pas de cotes recopiées d'un
plan. Le relevé a d'ailleurs corrigé une lecture du plan papier — voir la réserve
sur les trous M2 dans `../../README.md`.

Points relevés utiles :

| Cote | Valeur | Où |
|---|---|---|
| Corps moteur | Ø15,0 × 24,8 | `1524T_SR.stp`, Z −1,0 … 23,8 |
| Face avant moteur | Z = 23,8 | plan d'appui sur le réducteur |
| Fixation moteur | 6 × M1,6 sur Ø10, prof. 2,0 | couverte par le réducteur, inutilisée |
| Corps réducteur | Ø15,0 × 17,1 | `15-10K_1stage.stp`, Z −17,1 … 0 |
| Portée de centrage | Ø7,0 saillant de 1,0 | version K ; 0,5 seulement en frittés |
| **Fixation réducteur** | **2 × M2 à (0, ±5,5), prof. 3,0** | foret de taraudage Ø1,6 |
| Fixation impériale | 2 × 2-56 UNC à (±5,46, 0) | foret Ø1,8, non utilisée |
| Arbre de sortie | Ø3,0 de Z 2,0 à 14,0, chanfrein 14,2 | épaulements Ø4,5 puis Ø3,5 avant |

La différence des deux forets — 1,6 pour M2, 1,8 pour 2-56 UNC — est ce qui
permet d'attribuer chaque paire de trous à son filetage : le plan les nomme sans
dire laquelle est sur quel diamètre de perçage.

L'emmanchement des deux STEP se fait en décalant le moteur de **40,9 mm**
(la cote L1 du catalogue) : le pignon du moteur tombe alors exactement dans la
cavité Ø6 du réducteur, ce qui vérifie la valeur.
