> Proposition désormais implémentée : voir [le compte rendu MR30](../mr30-review/README.md). Les paragraphes ci-dessous décrivent la phase de proposition et ses hypothèses.

# Proposition de réduction du connecteur batterie — 6 septembre 2026

Proposition seulement, aucun changement du schéma ou du PCB dans cette passe.

## Résultat — budget corrigé après confirmation utilisateur

L'utilisateur confirme **1 A réel par moteur DC**. Le candidat retenu pour l'intégration compacte et les essais est donc AMASS MR30PB-M (embase verticale) + MR30-F côté pack, puissance en cuivre multibrin AWG16 pour environ 5 cm par conducteur, point milieu en AWG24.

Budget d'exploitation : **15,5 A permanents / 18,5 A pointe**, soit ESC 12/15 A + deux moteurs DC de 1 A + provision batterie de 1,5 A pour l'électronique. Les courants ESC et électronique restent des enveloppes de dimensionnement, pas des consommations mesurées. L'ancien budget 19,5/22,5 A additionnait les seuils des drivers DC ; il est remplacé pour le fonctionnement réel confirmé. Les seuils matériels actuels proches de 3 A ne sont pas modifiés : surcharge, blocage moteur et protection restent à traiter séparément. La confirmation de consommation réelle ne constitue pas une limitation matérielle de courant.

Le MR30 reste limité à 20 A selon le critère constructeur de hausse de température pouvant atteindre 85 K. La marge de courant nominale est de 4,5 A en permanent et 1,5 A en pointe, avant tolérances. Cela justifie ce candidat compact, mais ne qualifie pas sa température dans le robot ni une surcharge non documentée. Vérifier le montage complet (deux voies puissance chargées, MID à faible courant), les soudures et l'échauffement.

Pour deux fils AWG16 de 5 cm à 20 °C : R boucle = 1,317 mΩ. À 15,5 A : chute 20,4 mV et pertes 0,316 W dans les deux fils ; à 18,5 A : 24,4 mV et 0,451 W. Avec l'hypothèse de 1,5 mΩ par contact accouplé, les deux contacts ajoutent respectivement 0,721 W et 1,027 W. Total prévisionnel câble+contacts : 1,04 W / 1,48 W, hors soudures et cuivre PCB. Ces pertes ne permettent pas seules de calculer une température sans caractérisation thermique.

Le corps MR30PB est d'environ12 ×5,3 mm et10,5 mm haut au-dessus de la carte, hors femelle et courbure des fils. Le catalogue cite11,9 ×5,3 ×10,4 mm ; le dessin actuel de la page constructeur MR30PB-M (632) indique11,7 ×5,3 ×10,6 mm, trousØ1,8 +0,2/0 et entraxes3,5 ±0,05 mm. Révision à figer avant création d'empreinte. Ne pas extrapoler l'enveloppe accouplée depuis l'embase seule.

## Calcul des fils

Hypothèse explicite :5 cm pour B+ et5 cm pour GND, donc10 cm électriques aller-retour. Cuivre à20°C, résistivité0,017241 ohm.mm²/m ; hors soudures et contacts. R=rho*2L/S ; U=IR ; P=I²R. Sections nominales géométriques AWG.

| Fil | Section mm² | R boucle mΩ | Chute à20 A mV | P boucle à20 A W | P boucle à22,5 A W |
|---|---:|---:|---:|---:|---:|
| AWG12 |3,309|0,521|10,4|0,208|0,264|
| AWG14 |2,081|0,829|16,6|0,331|0,419|
| AWG16 |1,309|1,317|26,3|0,527|0,667|
| AWG18 |0,823|2,095|41,9|0,838|1,060|

À10 cm par conducteur, tous ces résultats doublent. À60°C, la résistance du cuivre augmente d'environ16%. L'AWG16 est un candidat raisonnable pour un faisceau de5 cm dégagé ; l'AWG14 réduit la chauffe pour10 cm ou un régime proche20 A prolongé. Cette analyse ohmique n'attribue pas une température ou une intensité admissible certifiée au câble : isolation, regroupement et températures des terminaisons comptent.

Le point milieu ne transporte que l'équilibrage actuel (~87,5 mA) et la mesure :5 cm AWG24 donnent environ4,21 mΩ, soit0,37 mV de chute et0,032 mW sous87,5 mA. AWG26 serait électriquement suffisant ; AWG24 est proposé pour la robustesse de manipulation et la soudure, avec retenue mécanique. R10747Ω/1W ne change pas.

## Contacts et comparaison

Calcul préliminaire avec1,5 mΩ par voie accouplée MR30 (à confirmer sur la révision commandée), deux voies de puissance en série :3 mΩ. À15,5 A :0,721 W dans les deux contacts ; à20 A :1,20 W et60 mV ; à22,5 A :1,519 W, au-delà du calibre continu publié. Les fils courts ne font pas disparaître ces pertes. Avec5 cm de puissance AWG16 par conducteur à20 A, total fils+contacts =86 mV et1,73 W, hors joints/PCB. Le courant du troisième contact MID est négligeable pour la dissipation, mais cela ne justifie pas de majorer arbitrairement le courant autorisé de chaque autre contact.

Autres produits examinés :
- MR60PB-M : fiche spécifique2023V0 annonce30 A à30 K,35 A à85 K,1,2 mΩ, mais boîtier20,2 ×9,8 mm et16,9 mm haut : il n'apporte pas une réduction franche face au Mega-Fit. Les pages génériques et le catalogue contiennent des valeurs contradictoires ; privilégier les spécifications exactes et confirmer le montage complet avec la femelle et son AWG.
- Mini-Fit Max3 circuits :18,5 A AWG14 et15,5 A AWG16 (cette dernière valeur marquée provisoire), pas les20,5 A de tête de catalogue. Avec le budget utilisateur corrigé, il constitue une alternative en AWG14 sous conditions de déclassement, mais impose des fils plus gros et ne correspond pas au gain maximal recherché avec MR30.
- XT30(2+2) : compact et pourrait ajouter NTC, mais4 contacts physiques, même limite20 A/85 K ; il ne résout pas le plafond de courant du MR30.
- LCC30 : données courant plus détaillées mais dimensions trop élevées pour constituer le gain recherché.

## Sources primaires

- AMASS MR30PB-M : https://www.china-amass.com/biao/632.html ; dessin https://www.china-amass.com/public/upload/20260713/图片1(1)(1)(1).png
- AMASS catalogue2026, pages9/12 : https://www.china-amass.com/public/upload/20260207/7fa24f5a6f35ec66c7a115c07a34ab06.pdf
- AMASS MR60PB-M2023V0 : https://www.china-amass.com/public/upload/20240530/3d2a67318f4422e8338a68c4299cfe2f.pdf
- Molex Mini-Fit Max2125150000-PS révisionC4, pages6–8 : https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/productspecificationpdf/212/212515/2125150000-PS-000.pdf
- Données locales : battery-sources/README.md ; documentation/architecture-usainbot.html (ancienne intention1 A moteur, ses autres hypothèses de batterie/ESC sont obsolètes).
