# Analyse placement alimentation, MCU, moteurs, IHM et communications

Lecture seule du schéma et du PCB `UsainBot/electronics`, netlist exportée par KiCad CLI. Les fichiers du projet n'ont pas été modifiés par cette analyse. Données calculables : `/tmp/usain-components.json`, `/tmp/usain-positions.json`, `/tmp/usain_functional_constraints.json` (161 contraintes). Les coordonnées de référence sont celles du PCB au début de cette revue.

## Décisions électriques prioritaires

- U201 possède onze broches VDD (17,30,39,52,62,72,84,108,121,131,144), en plus de VBAT6 et VDD33USB95. Affectation précise des onze 100nF génériques dans le JSON; C222 est explicitement USB95 dans le schéma, C208/C209 sont VDDA33, C210/C211 VREF32, C212 VCAP71, C213 VCAP106. Orienter pad1 vers sa broche dédiée et pad2 vers un retour court au plan de masse. Une couronne uniforme basée uniquement sur distance au centre STM32 serait incorrecte.
- Réserver quatre groupes autour de U201 : alimentation analogique32/33, horloge23/24/Y201, VCAP71, VCAP106. NRST25 a C214 à l'entrée STM32 même si SW603 est éloigné. R204 est une résistance série dans OSC_OUT24; C215/C216 sont charges des deux bornes du quartz. Ces trois condensateurs ne se traitent pas comme VDD.
- C2064.7uF sert de réserve VDD, mais aucun condensateur dédié VBAT6 n'existe. Le JSON le place près de6 par compromis. Ajouter C223100nF et C2241uF +3V3-GND près de6 est cohérent avec AN5419 et permet de réaffecter C206 à l'arrivée principale VDD. Cette suggestion est un changement de schéma explicite, pas un déplacement implicite d'un condensateur dédié ailleurs.
- R119/R120/C121 doivent être groupés côté U201.26 VBAT_SENSE: le diviseur et la capacité chargent une entrée ADC et ne doivent pas être laissés près des MOSFETs de puissance. Prélèvement de VBAT par une piste de mesure, éloignée des branches de puissance.
- R307/R3571k convertissent les courants IPROPI au plus près U301/U351.6; les paires R308/C302 et R358/C352 filtrent en aval et doivent terminer près ADC U201.49 et53 respectivement.
- C301 découple VREF_MOT mais cette référence dessert deux drivers séparés de107mm. Ajouter C351100nF entre VREF_MOT etGND près U351.5 est recommandé. Une piste commune filtrée localement aux deux extrémités est possible; il n'est pas nécessaire de changer les résistances de réglage.
- R117/R118 forment le feedback buck à U103.8. Les rapprocher du FB, avec le point de prélèvement +3V3 pris après L102/C116/C117; C115 est SS, R116 est RT. Aucun de ces composants ne doit être intercalé dans le couloir SW5-L102.1.
- C104 est le bootstrap chargeur entre BTST12 et SW17/18, C114 celui du buck BST6/SW5. C305/C355 sont des réserves de pompe VCP-VM; C306/C356 sont les capacités volantes CPH-CPL. Aucun ne retourne simplement àGND.
- C607 est une liaison AC sur BUZZER (BUZZER→C607→BZAC→R609→Q601.G). D610 limite l'excursion négative de BZAC. Le tout doit être compact près deQ601, distinct de la boucle de puissance BZ601/Q601/D601.

## Organisation physique

Chargeur U102 et son alimentation restent dans la bande arrière gauche; boucle SNS15/16-C106/C107-GND prioritaire, puis PMID21/22-C102/C103-GND et SW17/18-L101.2. Placer le réseau TS/ILIM/MID au sud côté pins7/8/9 et garder MID à distance deL101. R10710R2512 est une résistance dissipative d'équilibrage, donc proche CBSET10 mais avec espace thermique et hors boucle analogique TS.

Le déplacement proposé de U103 vers l'épaule ouest (vers123,163) éloigne sa self et le cuivre SW de TM541. Conserver un petit îlot buck complet: C113+entréeC111/C112 d'un côté VIN3/GND4, L102 de l'autre côté SW5, sortieC116/C117 après self, feedback sur le bord calme. FB101 et C118/C119/C120 devraient être au point d'entrée du domaine analogique près STM32/AOP; cet ensemble est un filtre de distribution et non un passif à coller à la self buck.

U101 ESD doit être sur le trajet USB connecteur→STM32, immédiatement à la sortie du connecteur. Son angle -90° met les pins1/3 au nord vers J101 et les pins6/4 au sud vers STM32. R101/R102 sont les terminaisons CC et doivent atteindre J101.A5/B5 sans traverser la paire USB. La nécessité de rester hors turbine peut imposer un contournement à la paire en aval; ne pas déplacer J101.

U301 et U351 sont verrouillés à90°. Leurs pins9..16 sont au nord y124.225, et les pins1..8 au sud y129.775. Les pompes doivent donc rester au nord; les composants de mode/courant et la référence au sud. Pour les deux drivers, C306/C356 orientés180° permettent de faire correspondre pad1CPH (plus à droite) et pad2CPL (plus à gauche); C305/C355 à0° font correspondre pad1VCP à gauche et pad2VM à droite; C303/C353 à0° font correspondre pad1VM à gauche et pad2GND à droite. Ce sont des orientations initiales à tester contre les obstacles, pas des positions imposées.

C307/C357100nF entre sorties moteur se placent contre J301/J351 pins1/2. Les deux RC encodeurs par moteur (R309/C308,R310/C309 et équivalents +50) se groupent côté pins5/6 des connecteurs, avec chemin des encodeurs indépendant du passage des sorties moteur. Les retours GND des drivers et des pompes doivent permettre un rattachement direct au plan et au pad thermique; éviter une boucle de retour à travers la masse analogique STM32.

Q102/Q103 sont verrouillés à200.4,123.6/130.2. Leurs sources sont àx197.925, drains àx202.875 et grilles àx197.925. Le groupe F101 doit alimenter leur côté gauche; TVS D102 et réserve VBAT vers le côté droit sans obstruer U351. Le groupe Q104/R124/R126/R114/C123/D106 près des grilles évite une longue ligne PWR_G. R127/R128/C122 peuvent être séparés de ce groupe pour filtrer PWR_BTN au STM32. Les connecteurs batterie et ESC conservent les positions verrouillées et les seules exceptions mécaniques autorisées.

U701 doit suivre le groupe SPI STM32 pins111/112/113/116, après décision d'angle MCU. C701 contreVCC8 etGND4; R701/R702 contreWP3 etHOLD7. Q701/Q702/R703/R704/R705 sont le commutateur du module BLE; C702/C703 contre les pins d'alimentation J701. Une réserve BLE près du MCU ne remplace pas ce découplage côté module.

## Rotation STM32, comparaison chiffrée

Distance euclidienne cumulée entre broches U201 et centres des éléments verrouillés correspondants (indicateur de ratsnest, sans obstacles ni routage). Les capteurs ligne sont douze, les moteurs incluent commandes/sommeil/défauts/encodeurs. Une rotation de180° conserve exactement l'enveloppe mécanique actuelle du MCU.

| Angle U201 | Laser RX→TM | Ligne12ADC→U401..412 | Moteurs | USB→J101 | IMU→U503 | IHM | Debug→J201 |
|---|---:|---:|---:|---:|---:|---:|---:|
|-135° initial|135.4|963.6|1334.5|210.4|154.2|202.0|64.7|
|-45°|162.3|808.7|1279.3|193.4|175.9|293.2|91.4|
|+45°|158.7|693.2|1199.7|161.8|145.7|288.7|113.3|
|+135°|138.2|866.3|1258.7|181.7|95.2|196.8|90.8|

+45° procure un gain clair pour les douze lignes ADC, l'USB et les moteurs, avec une somme laser augmentée d'environ23mm. +135° est une alternative conservant des trajets laser proches de l'initial et raccourcissant l'IMU, au prix de lignes plus longues. Pour trancher la chaîne laser, utiliser les sorties des nouveaux AOP régionaux comme extrémités RX, plutôt que les centres TM comme dans ce premier calcul. Les nets photodiodes sensibles restent impérativement locaux aux capteurs, indépendamment de cette comparaison ADC.

## Limites imposées par les verrous

- L'orientation de U301 place OUT1 à droite/sud et OUT2 à droite/nord alors que J301 est à gauche. Il faut préserver des voies de contournement pour ces deux nets; faire tourner le driver serait interdit.
- U351 et Q102/Q103 sont serrés dans la bande arrière droite. Ne pas placer un gros réservoir entre leurs boîtiers au détriment du couloir de cuivre batterie et moteur; prioriser les petits bypass côté nord puis déplacer le bulk à la place la plus proche encore libre.
- Le long trajet analogique entre TM501 frontal et STM32 ne peut disparaître par simple rotation; conditionner au capteur et acheminer uniquement le signal de sortie basse impédance vers ADC.
- Les cibles de proximité du JSON ne prouvent pas les clearances ni les réserves mécaniques. Elles doivent être soumises au moteur d'obstacles et au contrôle KiCad global du parent.

## Références constructeur consultées

Les affectations de références/broches proviennent du schéma et non des exemples constructeur. Les priorités de boucles se fondent sur les sections de placement:

- [TI BQ25887, §11 p74](https://www.ti.com/lit/ds/symlink/bq25887.pdf): priorité condensateurs SNS puis PMID puis inductance; retour analogique et puissance convergeant au pad thermique, mesure MID hors commutation.
- [TI TPS62933, §12 p40](https://www.ti.com/lit/ds/symlink/tps62933.pdf): boucle VIN/GND et100nF très courte, SW court, bootstrap local, feedback et SS/RT au calme.
- [TI DRV8874, §10 p31](https://www.ti.com/lit/gpn/DRV8874): capacités VM,VCP,CPH/CPL et bulk près CI; PGND etGND au plan commun, cuivre thermique disponible.
- [ST AN5419, tableau2 et figure3 p7–9](https://www.st.com/resource/en/application_note/an5419-getting-started-with-stm32h723733-stm32h725735-and-stm32h730-mcu-hardware-development-stmicroelectronics.pdf):100nF parVDD avec4.7uF global,100nF+1uF pourVDDA etVBAT, condensateurs VCAP locaux; le schéma affecte lui-même les pairesVDDA/VREF.

## Tableau complet des contraintes

| Réf | Valeur | Groupe | Ancre | Pad concerné | Priorité | Rôle/placement |
|---|---|---|---|---|---:|---|
|C101|1uF|charger_input|U102.23|1|9|VBUS bypass 1uF, près VBUS et GND|
|C102|22uF|charger|U102.21|1|10|Découplage PMID|
|C103|22uF|charger|U102.22|1|10|Découplage PMID|
|C104|47nF|charger|U102.12|1|10|Bootstrap BTST-SW: pad2 vers pins17/18, très petit circuit fermé|
|C105|4u7F|charger|U102.11|1|10|REGN bypass|
|C106|22uF|charger|U102.15|1|10|Découplage SNS prioritaire|
|C107|22uF|charger|U102.16|1|10|Découplage SNS prioritaire|
|C108|10uF|charger|U102.13|1|8|BAT reservoir|
|C109|100uF|main_power|Q103.5|1|8|Réservoir / TVS sur VBAT côté drains, dégager cuivre haute intensité|
|C110|100nF|main_power|Q103.5|1|8|Réservoir / TVS sur VBAT côté drains, dégager cuivre haute intensité|
|C111|10uF|buck|U103.3|1|9|VIN-GND boucle entrée minimale; C113 au plus près pins3/4|
|C112|10uF|buck|U103.3|1|9|VIN-GND boucle entrée minimale; C113 au plus près pins3/4|
|C113|100nF|buck|U103.3|1|10|VIN-GND boucle entrée minimale; C113 au plus près pins3/4|
|C114|100nF|buck|U103.6|1|10|Bootstrap pad1 BST6 et pad2 SW5, adjacent côté SW|
|C115|10nF|buck_quiet|U103.7|1|9|SS10nF côté calme, loin cuivre SW/L102|
|C116|22uF|buck|L102.2|1|9|Sortie22uF après inductance, boucle retour GND vers entrée/CI compacte|
|C117|22uF|buck|L102.2|1|9|Sortie22uF après inductance, boucle retour GND vers entrée/CI compacte|
|C118|100nF|analog_rail|FB101.1|1|9|Découplage avant ferrite +3V3|
|C119|10uF|analog_rail|FB101.2|1|9|Filtrage après ferrite +3V3A, GND continue, forme filtre compact|
|C120|100nF|analog_rail|FB101.2|1|9|Filtrage après ferrite +3V3A, GND continue, forme filtre compact|
|C121|100nF|battery_ADC|U201.26|1|10|Pont/filtre VBAT_SENSE entier côté ADC; prélever VBAT par piste sense séparée puissance|
|C122|100nF|power_button_filter|U201.142|1|8|Pont/filtre PWR_BTN à récepteur MCU; BTN_N peut être long|
|C123|1uF|main_power|Q102.4|1|8|Commande commune PWR_G Q102/Q103: près des gates côté x197.925|
|C201|100nF|MCU_VDD|U201.17|1|10|100nF local dédié VDD. Pad1 dirigé vers broche, pad2 masse via directe; réserver escape des IO voisines.|
|C202|100nF|MCU_VDD|U201.30|1|10|100nF local dédié VDD. Pad1 dirigé vers broche, pad2 masse via directe; réserver escape des IO voisines.|
|C203|100nF|MCU_VDD|U201.39|1|10|100nF local dédié VDD. Pad1 dirigé vers broche, pad2 masse via directe; réserver escape des IO voisines.|
|C204|100nF|MCU_VDD|U201.52|1|10|100nF local dédié VDD. Pad1 dirigé vers broche, pad2 masse via directe; réserver escape des IO voisines.|
|C205|100nF|MCU_VDD|U201.62|1|10|100nF local dédié VDD. Pad1 dirigé vers broche, pad2 masse via directe; réserver escape des IO voisines.|
|C206|4u7F|MCU_VDD|U201.6|1|8|4.7uF réservoir VDD placé près VBAT faute découplage VBAT distinct; voir recommandation C223/C224 dans rapport.|
|C207|100nF|MCU_VDD|U201.72|1|10|100nF local dédié VDD. Pad1 dirigé vers broche, pad2 masse via directe; réserver escape des IO voisines.|
|C208|100nF|MCU_analog|U201.33|1|10|VDDA/VREF local|
|C209|1uF|MCU_analog|U201.33|1|9|VDDA/VREF local|
|C210|100nF|MCU_analog|U201.32|1|10|VDDA/VREF local|
|C211|1uF|MCU_analog|U201.32|1|9|VDDA/VREF local|
|C212|2u2F|MCU_supply_reset|U201.71|1|10|Découplage local broche précise; VCAP C212/C213 ne sont pas +3V3.|
|C213|2u2F|MCU_supply_reset|U201.106|1|10|Découplage local broche précise; VCAP C212/C213 ne sont pas +3V3.|
|C214|100nF|MCU_supply_reset|U201.25|1|10|Découplage local broche précise; VCAP C212/C213 ne sont pas +3V3.|
|C215|10pF|MCU_clock|Y201.1|1|10|Charge quartz OSC_IN; masse commune courte|
|C216|10pF|MCU_clock|Y201.3|1|10|Charge quartz XTAL_OUT; masse commune courte|
|C217|100nF|MCU_VDD|U201.84|1|10|100nF local dédié VDD. Pad1 dirigé vers broche, pad2 masse via directe; réserver escape des IO voisines.|
|C218|100nF|MCU_VDD|U201.108|1|10|100nF local dédié VDD. Pad1 dirigé vers broche, pad2 masse via directe; réserver escape des IO voisines.|
|C219|100nF|MCU_VDD|U201.121|1|10|100nF local dédié VDD. Pad1 dirigé vers broche, pad2 masse via directe; réserver escape des IO voisines.|
|C220|100nF|MCU_VDD|U201.131|1|10|100nF local dédié VDD. Pad1 dirigé vers broche, pad2 masse via directe; réserver escape des IO voisines.|
|C221|100nF|MCU_VDD|U201.144|1|10|100nF local dédié VDD. Pad1 dirigé vers broche, pad2 masse via directe; réserver escape des IO voisines.|
|C222|100nF|MCU_supply_reset|U201.95|1|10|Découplage local broche précise; VCAP C212/C213 ne sont pas +3V3.|
|C301|100nF|motor_reference|U301.5|1|9|Référence moteurs commune (drivers distants107mm); recommander ajout C351100nF près U351.5|
|C302|1nF|motor_left_ADC|U201.49|1|10|C1nF de filtrage après100R juste avant entrée ADC, GND calme|
|C303|100nF|motor_left|U301.11|1|10|Bypass VM-PGND près pins11/9, nord du CI|
|C304|100uF|motor_left|U301.11|1|9|Bulk VM proche mais après céramique; réserve cuivre puissance|
|C305|100nF|motor_left|U301.12|1|10|Réserve pompe VCP-VM pins12/11|
|C306|22nF|motor_left|U301.13|1|10|Flying capacitor CPH-CPL pins13/14 pad1 vers13 pad2 vers14|
|C307|100nF|motor_left|J301.2|1|9|Condensateur suppression parasites entre les sorties moteur au connecteur; boucle entre pads2/1 courte|
|C308|1nF|motor_left_encoder|R309.2|1|8|1nF après résistance100R, pin2 GND|
|C309|1nF|motor_left_encoder|R310.2|1|8|1nF après résistance100R, pin2 GND|
|C352|1nF|motor_right_ADC|U201.53|1|10|C1nF de filtrage après100R juste avant entrée ADC, GND calme|
|C353|100nF|motor_right|U351.11|1|10|Bypass VM-PGND près pins11/9, nord du CI|
|C354|100uF|motor_right|U351.11|1|9|Bulk VM proche mais après céramique; réserve cuivre puissance|
|C355|100nF|motor_right|U351.12|1|10|Réserve pompe VCP-VM pins12/11|
|C356|22nF|motor_right|U351.13|1|10|Flying capacitor CPH-CPL pins13/14 pad1 vers13 pad2 vers14|
|C357|100nF|motor_right|J351.2|1|9|Condensateur suppression parasites entre les sorties moteur au connecteur; boucle entre pads2/1 courte|
|C358|1nF|motor_right_encoder|R359.2|1|8|1nF après résistance100R, pin2 GND|
|C359|1nF|motor_right_encoder|R360.2|1|8|1nF après résistance100R, pin2 GND|
|C601|100nF|joystick|SW601.1|1|8|Filtre anti-rebond100nF, petites paires locales autour switch sans obstruer mécanique joystick|
|C602|100nF|joystick|SW601.2|1|8|Filtre anti-rebond100nF, petites paires locales autour switch sans obstruer mécanique joystick|
|C603|100nF|joystick|SW601.3|1|8|Filtre anti-rebond100nF, petites paires locales autour switch sans obstruer mécanique joystick|
|C604|100nF|joystick|SW601.4|1|8|Filtre anti-rebond100nF, petites paires locales autour switch sans obstruer mécanique joystick|
|C605|100nF|joystick|SW601.5|1|8|Filtre anti-rebond100nF, petites paires locales autour switch sans obstruer mécanique joystick|
|C606|100nF|start_button|SW602.1|1|8|Filtre START|
|C607|100nF|buzzer_gate|R609.1|2|8|Couplage AC BUZZER: ce 100nF n est PAS un bypass alimentation|
|C701|100nF|flash|U701.8|1|10|Bypass flash VCC|
|C702|10uF|BLE_power|J701.2|1|8|Réservoir BLE à arrivée module pins2(+)/1(GND)|
|C703|100nF|BLE_power|J701.2|1|10|Réservoir BLE à arrivée module pins2(+)/1(GND)|
|C704|220uF|ESC_supply|J103.1|1|8|Réservoir ESC hors keepout turbine, exception réservée connecteurs uniquement|
|C705|100nF|ESC_supply|J103.1|1|8|Réservoir ESC hors keepout turbine, exception réservée connecteurs uniquement|
|D101|vert - charge|charger_led|U102.2|1|4|Témoin STAT facultatif visuel près USB|
|D102|SMBJ9.0A|main_power|Q103.5|1|9|Réservoir / TVS sur VBAT côté drains, dégager cuivre haute intensité|
|D106|BAT54|main_power|Q102.4|1|8|Commande commune PWR_G Q102/Q103: près des gates côté x197.925|
|D601|BAT54|buzzer|BZ601.2|2|9|Roue libre directement entre bornes BZ601 (cathode +3V3)|
|D610|BAT54|buzzer_gate|R609.1|1|8|Clamp négatif du noeud BZAC vers GND|
|D701|bleue|BLE_indicator|J701.2|2|3|Témoin BLE près module|
|F101|12 A|main_power|Q102.1|2|8|Fusible VPACK vers sources MOSFET, côté entrée gauche|
|FB101|600R @ 100 MHz|analog_rail|U201.33|2|8|Placer à entrée domaine analogique près VDDA et départ AOP, pas à côté inductance buck|
|L101|1uH / 4 A|charger|U102.17|2|10|Inductance SW/PMID: pad2 SW vers17/18; pad1 vers21/22 et C102/C103, boucle compacte|
|L102|4u7H / 3 A|buck|U103.5|1|10|Inductance pad1 SW5 au plus près; pad2 +3V3 vers sortie|
|Q101|AO3400A|charger_control|U102.3|3|6|Transistor commande CD chargeur|
|Q104|AO3400A|main_power|Q102.4|3|8|Commande commune PWR_G Q102/Q103: près des gates côté x197.925|
|Q601|AO3400A|buzzer|BZ601.2|3|8|Boucle courant buzzer compacte|
|Q602|AO3400A|track_lights|U201.4|1|5|Commande commune LEDs réparties D606/D608/D609; placer plutôt zone centrale/digitale, pas capteurs analogiques|
|Q701|SI2301CDS|BLE_power|J701.2|3|7|Switch rail BLE placé avant réservoir C702/C703|
|Q702|AO3400A|BLE_power|Q701.1|3|7|Commande NMOS grille PMOS|
|R101|5k1|USB|J101.A5|1|8|Terminaison CC au connecteur, pad2 GND|
|R102|5k1|USB|J101.B5|1|8|Terminaison CC au connecteur, pad2 GND|
|R103|383R|charger|U102.8|1|7|ILIM programmation|
|R104|5k23|charger|U102.7|2|7|TS pont côté REGN|
|R105|30k1|charger|U102.7|1|7|TS pont côté GND|
|R106|300R|charger|U102.9|2|7|Mesure MID après série300R; à proximité MID CI, trajet PACK_MID séparé du SW|
|R107|10R|charger|U102.10|2|7|Résistance équilibrage10R forte dissipation, CBSET; ne pas coller aux autres passifs thermosensibles|
|R108|10k|charger|U102.2|2|7|Pullup STAT|
|R109|10k|charger|U102.1|2|7|Pullup PG|
|R110|2k2|charger_led|D101.2|2|5|Limitation courant LED|
|R111|100k|charger|U102.3|2|7|Pullup CD|
|R112|100R|charger_control|Q101.1|2|8|Série grille et pulldown locaux|
|R113|100k|charger_control|Q101.1|1|8|Série grille et pulldown locaux|
|R114|100k|main_power|Q102.4|1|8|Commande commune PWR_G Q102/Q103: près des gates côté x197.925|
|R115|100k|buck_quiet|U103.2|2|7|Pullup EN|
|R116|42k2|buck_quiet|U103.1|1|8|Réglage RT proche pin1, loin SW|
|R117|100k|buck_feedback|U103.8|2|10|FB pont haut, prélèvement Kelvin sortie +3V3 après C116/C117, hors SW|
|R118|31k6|buck_feedback|U103.8|1|10|FB pont bas près pin8, masse calme du CI|
|R119|22k|battery_ADC|U201.26|2|8|Pont/filtre VBAT_SENSE entier côté ADC; prélever VBAT par piste sense séparée puissance|
|R120|10k|battery_ADC|U201.26|1|8|Pont/filtre VBAT_SENSE entier côté ADC; prélever VBAT par piste sense séparée puissance|
|R124|100R|main_power_control|Q104.1|2|8|Série grille/pulldown locaux|
|R125|10k|main_power_control|SW101.1|2|6|Pullup bouton sur VBAT_SW_IN|
|R126|100k|main_power_control|Q104.1|1|8|Série grille/pulldown locaux|
|R127|470k|power_button_filter|U201.142|2|6|Pont/filtre PWR_BTN à récepteur MCU; BTN_N peut être long|
|R128|220k|power_button_filter|U201.142|1|6|Pont/filtre PWR_BTN à récepteur MCU; BTN_N peut être long|
|R201|10k|MCU_reset|U201.25|2|7|Pullup NRST; C214 doit être encore plus près U201 que R201. SW603 reste verrouillé.|
|R202|10k|MCU_boot|U201.138|1|7|Pulldown BOOT0|
|R203|10k|MCU_boot|U201.138|2|6|Pullup BOOT0 option non montée selon schéma|
|R204|220R|MCU_clock|U201.24|2|10|Série OSC_OUT côté source STM32; pin1 rejoint Y201.3|
|R301|10k|motor_reference|U301.5|2|7|Référence moteurs commune (drivers distants107mm); recommander ajout C351100nF près U351.5|
|R302|6k8|motor_reference|U301.5|1|7|Référence moteurs commune (drivers distants107mm); recommander ajout C351100nF près U351.5|
|R303|100k|motor_left|U301.3|1|7|Pulldown nSLEEP|
|R304|10k|motor_left|U301.4|2|6|Pullup nFAULT|
|R305|20k|motor_left|U301.7|1|8|Mode courant IMODE|
|R306|10k|motor_left|U301.16|2|8|PMODE pullup|
|R307|1k|motor_left|U301.6|1|10|RIPROPI1k conversion courant, sensible près pin6, retour GND calme|
|R308|100R|motor_left_ADC|U201.49|2|9|Filtre courant 100R série proche récepteur ADC, relié à RIPROPI par signal basse impédance|
|R309|100R|motor_left_encoder|J301.6|1|7|Série100R encodeur placé sortie connecteur; paire RC compacte hors puissance|
|R310|100R|motor_left_encoder|J301.5|1|7|Série100R encodeur placé sortie connecteur; paire RC compacte hors puissance|
|R353|100k|motor_right|U351.3|1|7|Pulldown nSLEEP|
|R354|10k|motor_right|U351.4|2|6|Pullup nFAULT|
|R355|20k|motor_right|U351.7|1|8|Mode courant IMODE|
|R356|10k|motor_right|U351.16|2|8|PMODE pullup|
|R357|1k|motor_right|U351.6|1|10|RIPROPI1k conversion courant, sensible près pin6, retour GND calme|
|R358|100R|motor_right_ADC|U201.53|2|9|Filtre courant 100R série proche récepteur ADC, relié à RIPROPI par signal basse impédance|
|R359|100R|motor_right_encoder|J351.6|1|7|Série100R encodeur placé sortie connecteur; paire RC compacte hors puissance|
|R360|100R|motor_right_encoder|J351.5|1|7|Série100R encodeur placé sortie connecteur; paire RC compacte hors puissance|
|R601|4k7|I2C|J601.4|2|6|Pullup bus I2C partagé chargeur OLED LEDs, près branche numérique de J601|
|R602|4k7|I2C|J601.3|2|6|Pullup bus I2C partagé chargeur OLED LEDs, près branche numérique de J601|
|R603|10k|joystick|SW601.1|2|6|Pullup10k bouton, voisin cap filtre|
|R604|10k|joystick|SW601.2|2|6|Pullup10k bouton, voisin cap filtre|
|R605|10k|joystick|SW601.3|2|6|Pullup10k bouton, voisin cap filtre|
|R606|10k|joystick|SW601.4|2|6|Pullup10k bouton, voisin cap filtre|
|R607|10k|joystick|SW601.5|2|6|Pullup10k bouton, voisin cap filtre|
|R608|10k|start_button|SW602.1|2|6|Pullup START|
|R609|100R|buzzer_gate|Q601.1|2|8|Série grille après C607|
|R610|100k|buzzer_gate|Q601.1|1|8|Pulldown grille|
|R615|220R|track_lights|D606.2|2|7|Limitation courant LED nez|
|R619|100R|track_lights|Q602.1|2|8|Série grille/pulldown|
|R620|100k|track_lights|Q602.1|1|8|Série grille/pulldown|
|R701|10k|flash|U701.3|2|7|Pullup dédié WP/HOLD|
|R702|10k|flash|U701.7|2|7|Pullup dédié WP/HOLD|
|R703|100k|BLE_power|Q701.1|2|7|Pullup grille PMOS vers source +3V3|
|R704|100R|BLE_power|Q702.1|2|8|Grille NMOS série100R/pulldown100k|
|R705|100k|BLE_power|Q702.1|1|8|Grille NMOS série100R/pulldown100k|
|R706|1k|BLE_indicator|D701.2|2|6|Résistance LED|
|R707|100R|ESC_signal|U201.139|1|8|Série100R à source ESC_PWM, peut éviter de traverser mécanique avec stub|
|SW101|MARCHE / ARRET|main_power_control|Q104.3|1|3|Bouton marche arrêt accès opérateur, hors mécanique|
|U101|USBLC6-2SC6|USB|J101.A6|1|9|ESD entre USB connecteur et STM32, pins1/3 côté J101; pins6/4 côté MCU. Si J101 au nord, angle -90 donne ports1/3 au nord et4/6 au sud.|
|U701|W25Q128JVSIQ|flash|U201.111|6|8|Flash proche groupe pins111/112/113/116, CLK6 côté STM32, déduire orientation nets|
|Y201|25 MHz / 10 ppm|MCU_clock|U201.23|1|10|Regrouper quartz C215 C216 R204 contre pins23/24; pas de signaux rapides traversant boucle.|
