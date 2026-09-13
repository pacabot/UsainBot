# Connecteur batterie 2S commun — revue du 6 septembre 2026

## Décision

Le pack sera assemblé par l’utilisateur ; il n’existe donc pas de prise d’équilibrage physique à identifier. La proposition précédente XT30 + JST-XH du projet était une intention de schéma, pas une preuve de connectique du pack réel. Une liaison unique à trois conducteurs est possible avec un faisceau sur mesure.

Retenu : embase verticale Molex **2002411133** (Mega-Fit, 3 circuits, 5,70 mm, or 0,76 µm), boîtier femelle **2004561213**, retenue secondaire **1054150003**. Pour B− et B+, contacts **1720631333**, fil cuivre étamé **AWG12** (isolant ≤4,06 mm pour ce contact). La broche intermédiaire peut recevoir le même contact et fil, ou un contact correctement dimensionné pour sa section ; ne pas sertir un fil de mesure fin dans le contact AWG12. Les pages constructeur confirment 200 cycles pour le contact or ; l’option étamée était limitée à 25 cycles. [Embase](https://www.molex.com/en-us/products/part-detail/2002411133), [boîtier](https://www.molex.com/en-us/products/part-detail/2004561213), [contact](https://www.molex.com/en-us/products/part-detail/1720631333), [TPA](https://www.molex.com/en-us/products/part-detail/1054150003).

Comparaison : JST-XH B3B-XH-A, seulement 3 A sous AWG22, rejeté comme puissance ; Amass MR30PW-M, annoncé 20 A avec critère d’échauffement pouvant atteindre 85 K, trop faible pour l’enveloppe commune retenue ; Mega-Fit fournit une courbe de déclassement exploitable. [JST](https://www.jst-mfg.com/product/pdf/jpn/XH.pdf), [Amass](https://www.china-amass.net/mr30pw-m-product/).

## Brochage et empreinte

Vue dessus PCB / face d’accouplement de l’embase **mâle**, verrou vers Y négatif (nord) : **broche 1 à droite, broche 3 à gauche**. L’origine géométrique est le centre de la broche 3, à gauche ; cela conserve le repère du plan mécanique et du modèle. Le numéro du circuit suit le marquage moulé Molex, pas l’ordre gauche→droite.

| Broche | Fonction | Net projet | X, Y (mm) |
|---|---|---|---|
|1|BATT−|GND|11,40, 0|
|2|Point milieu 1S|/Alimentation/PACK_MID|5,70, 0|
|3|BATT+|VPACK|0, 0|

Les deux trous de maintien non métallisés sont en (2,85 ; 1,34) et (8,55 ; 1,34), diamètre 3,00 ±0,05 mm. Les trois trous électriques sont de 1,80 ±0,05 mm. Le perçage fabricant est donné côté composants. La numérotation a été vérifiée séparément sur les vues portant les marquages « FIRST CKT » et « LAST CKT » : l’embase mâle vue face accouplement avec verrou au nord porte la broche 1 à droite ; la prise femelle vue face accouplement avec verrou au nord porte la broche 1 à gauche. Ces deux vues de faces opposées sont en miroir. La version initiale de cette nouvelle empreinte avait les circuits 1 et 3 inversés ; la revue indépendante l’a corrigée avant intégration finale. Le modèle conserve ses axes et positions et ses étiquettes de contacts ont été corrigées. Dimensions documentées : corps 17,75 ×6,79 mm ; profondeur hors-tout 10,60 mm ; hauteur d’interface 15,30 mm, hauteur maximale 17,50 mm ; assemblage accouplé 30,90 mm haut et 11,30 mm profond. Zone réservée rectangulaire fabricant 20,76 ×12,90 mm. [Dessin Molex 2002411000 C5](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/200/200241/2002411133_sd.pdf), [copie C téléchargée depuis Farnell](https://www.farnell.com/cad/2867617.pdf), [dessin femelle Molex 2004561000 E1, copie RS](https://docs.rs-online.com/df2b/A700000012778846.pdf).

Fichier créé : `kicad-lib/Pacabot.pretty/Molex_Mega-Fit_200241-1133_1x03_P5.70mm_Vertical.kicad_mod`.

Les pastilles rondes de cuivre ont un diamètre de 2,70 mm, soit 0,45 mm d’anneau nominal. Ce choix laisse environ 0,30 mm entre cuivre et trous mécaniques : un pad de 2,80 mm laisserait seulement 0,2495 mm, juste sous la règle 0,25 mm du projet. Le pin 1 à droite est signalé par triangle et texte ; une pastille rectangulaire empiéterait davantage sur le trou mécanique. Les pads 1/3 imposent une connexion pleine aux zones. Courtyard : X −4,93…16,33 ; Y −9,03…4,37, soit la zone réservée constructeur augmentée de 0,25 mm. La sérigraphie identifie de gauche à droite 3:+BATT / 2:MID / 1:GND, et LATCH au nord.

## Courant : ne pas confondre le maximum catalogue avec l’assemblage réel

La spécification Molex 1720631000-PS rev D, pages 6–7, indique pour le simple rang 3 circuits, tous chargés en air calme, une élévation limite de 30 °C : 19 A avec AWG16, 22 A avec AWG14, **24 A avec AWG12**, 29 A avec AWG10. Les valeurs 3 circuits sont interpolées par le fabricant. Le déclassement dépend de la température, du cuivre et de l’échauffement voisin. Les essais du tableau utilisent cuivre étamé et contacts étamés ; l’utilisation or doit rester soumise à cette enveloppe conservatrice puis à un essai thermique du montage. Le chiffre de 30 A en catalogue n’est donc pas revendiqué ici. Le même document demande 19,1 mm de fil libre avant une attache pour 3–6 circuits. [Spécification Molex](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/productspecificationpdf/172/172063/1720631000-PS-000.pdf?inline=).

Analyse locale : le schéma règle les deux DRV8874 à environ 2,97 A chacun, à partir du pont 10k/6k8 sous 3,3 V et d’IPROPI 1k. Avec un ESC 12 A permanent /15 A pointe et une provision de 1,5 A batterie pour logique/convertisseur, enveloppe **19,5 A continus, 22,5 A de pointe**, avant tolérances. Les notes mécaniques Faulhaber parlent de 1 A maximum sur la nappe IE2, mais ce plafond n’est pas celui des résistances actuelles du schéma. Il ne faut pas utiliser cette hypothèse de 1 A pour réduire silencieusement la connectique.

AWG12 est retenu plutôt qu’AWG14, mais la marge à 22,5 A reste modeste : conserver un budget d’usage d’environ 20 A continus et vérifier température de contact, sertissage et rails. Un seuil logiciel de 22 A n’est efficace que si le courant total batterie est réellement mesuré : IPROPI ne mesure que les moteurs et le chargeur ne garantit pas une mesure du courant de décharge ESC. Le fusible F101 existant 12 A est sur la branche commutée VBAT et ne protégera pas l’ESC connecté sur VPACK. Une protection pack/ESC dimensionnée selon les cellules et son I²t reste nécessaire. Une valeur seule sans courbe de fusion ne constitue pas une validation.

L’empreinte ne valide pas le routage de puissance. Il faudra une arrivée large et pleine sur les pads 1/3, plusieurs couches reliées sans étranglement, cuivre et métallisation des trous spécifiés au fabricant PCB ; aucun diamètre ni nombre de vias universel n’est attribué avant le dessin des zones. Les pastilles traversantes et leur liaison pleine préparent cette étape, sans prétendre que le cuivre absent peut déjà porter 24 A.

## Modèles 3D et hypothèses visibles

Le STEP précis 2002411133 est référencé dans les catalogues Molex/Mouser, mais les téléchargements directs ont échoué (délais réseau/accès refusé). Aucun STEP d’un autre nombre de contacts n’a été incorporé. Deux enveloppes ont été créées sous FreeCAD PartDesign, puis relues avec Part : géométries valides.

- `kicad-lib/3d/Molex_2002411133_simplified.step` : embase, 7 solides, hors-tout X −3,18…14,57, Y3D −3,32…7,28, Z −3,23…17,50 mm. Associée à l’empreinte.
- `kicad-lib/3d/Molex_2002411133_mated_plug_envelope.step` : volume de la prise accouplée, Z15,30…30,90 mm, prévu pour contrôle de collision avec le modèle précédent, offset et rotations nuls.
- `.FCStd` et générateur `build_megafit_envelope.py` conservés dans `integration-review/battery-sources/`.

Le modèle utilise X3D = X empreinte, Y3D = −Y empreinte et Z0 = face supérieure du PCB principal. Ainsi les tétons placés à Y=+1,34 sur l’empreinte sont à Y3D=−1,34 ; le verrou au nord de l’empreinte, Y<0, est à Y3D>0. Les contacts 3/2/1 sont aux X0/5,70/11,40 mm, exactement comme les perçages.

Approximations explicites : section carrée des contacts 1,14 mm et extrémité supérieure estimées ; diamètre des tétons 2,90 mm et longueur 2 mm estimés, tandis que leurs axes et les perçages suivent le plan ; largeur du verrou non cotée, donc enveloppe volontairement étendue à toute la largeur du corps et jusqu’à Z0 ; position latérale exacte du volume accouplé non cotée, donc profondeur conservatrice 12,00 mm au lieu des 11,30 mm publiés (0,70 mm ajoutés de chaque côté du corps 10,60 mm). Cavités internes et détails de clips omis. Ces volumes peuvent surestimer une collision, pas justifier une interférence réelle. Dégagement du faisceau et accessibilité au verrou restent à examiner dans l’assemblage mécanique.

## Recharge et autonomie : points non déterminés par le connecteur

Le chargeur existant BQ25887 est un chargeur élévateur USB 2S avec équilibrage, sortie maximale 2 A et plage de tension batterie 6,8–9,2 V. Le fabricant le présente pour Li-ion/Li-polymère. [TI BQ25887](https://www.ti.com/product/BQ25887).

Le schéma actuel inhibe la charge avec CD tiré haut tant que le MCU n’active pas Q101 ; il neutralise aussi la mesure de température pack avec un diviseur fixe. Le dépôt firmware ne contient qu’un `.ioc`, aucun profil de charge exécuté ni validation réelle du réglage LiFePO4. Puisque les cellules ne sont pas choisies, ne pas activer la charge ni prétendre valider leur chimie à partir de la plage de tension du chargeur. Le point milieu sert au BQ25887 via R106/R107 ; il ne faut alimenter aucune charge normale depuis une seule cellule. La revue a trouvé R10710Ω/1W sous-dimensionnée pour~382mA à4.2V. Le schéma et la netlist ont été corrigés à **47Ω/1W,2512** :~87.5mA et0.360W avec Rds typ1Ω ; borne conservatrice0.450W à4.6V sans Rds. Cette baisse de courant allonge la phase d’équilibrage des cellules déséquilibrées, pas nécessairement la charge principale. Protéger le conducteur MID près des cellules en conservant ce courant d’équilibrage ; vérifier l’effet de la protection et de sa résistance sur la mesure. Le seuil automatique d’équilibrage3.7V ne valide pas l’ancien packLiFePO4 ; le futur profilLi-ion/LiPo doit correspondre aux cellules. [TI,§8.3.4.3](https://www.ti.com/lit/ds/symlink/bq25887.pdf).

Aucune autonomie numérique cible ni cellule précise n’est encore confirmée. Pour une fraction utilisable de 80 %, capacité nécessaire Q[Ah] = I_moyen[A] × durée[min] /48. Exemples purement budgétaires pour 5 minutes : 5 A →0,52 Ah ;10 A →1,04 Ah ;19,5 A →2,03 Ah. Les cellules choisies devront assurer le courant commun, leurs pointes, la chute de tension, la masse et le régime de charge ; le « pack1000mAh15C » des anciennes simulations ne valide pas une enveloppe20A. Sous USB5V limité~2,4A, la puissance disponible impose aussi une charge réelle inférieure au maximum2A du circuit à pleine tension2S.
