# Classes de nets

Écrites dans `UsainBot.kicad_pro` le 2 octobre 2026. Les courants viennent de
[courants.md](courants.md), les largeurs et isolements de [calculs.md](calculs.md), les
minimums de fabrication de [capacites-jlcpcb.md](capacites-jlcpcb.md).

## Tableau

| Classe | Piste | Isolement | Via (pastille / trou) | Paire (largeur / écart) | Courant (A) | Étape | Couleur | Rôle |
|---|---|---|---|---|---|---|---|---|
| PACK | 1,2 | 0,20 | 0,6 / 0,3 | — | 2,2 | 1 | rouge | bus du pack ; tronc 10 A en zones |
| VBAT | 0,5 | 0,20 | 0,6 / 0,3 | — | 3,9 | 1 | orange | après l'interrupteur ; tronc en zone In2 |
| MOTEUR | 0,5 | 0,20 | 0,6 / 0,3 | — | 1,5 | 1 | magenta | sorties des ponts |
| CHARGEUR | 2,0 | 0,20 | 0,6 / 0,3 | — | 3,0 | 1 | brun | entrée USB et sortie du boost |
| COMMUTATION | 2,0 | 0,20 | 0,6 / 0,3 | — | — | 1 | rouge vif | nœuds SW ; F.Cu seule, sans via |
| AMORCAGE | 0,3 | 0,20 | 0,5 / 0,3 | — | — | 1 | rose | bootstrap, pompes de charge |
| ALIM_LOGIQUE | 0,3 | 0,15 | 0,6 / 0,3 | — | 1,2 | 1 | jaune | +3V3, +3V3A, +3V3_BLE, REGN, 5 V des codeurs ; plan In2 |
| GND | 0,3 | 0,15 | 0,6 / 0,3 | — | — | 1 | gris | plan In1 ; raccords de pastille |
| IMPULSION | 0,3 | 0,15 | 0,5 / 0,3 | — | — | 1 | violet | émetteurs pulsés, buzzer |
| ANALOGIQUE | 0,2 | 0,15 | 0,5 / 0,3 | — | — | 2 | vert | mesures, références, retours |
| HORLOGE | 0,2 | 0,15 | 0,5 / 0,3 | — | — | 2 | cyan | quartz 25 MHz |
| USB | 0,34 | 0,15 | 0,5 / 0,3 | 0,34 / 0,20 (via 0,25) | — | 2 | bleu | paire 90 Ω |
| Default | 0,2 | 0,15 | 0,5 / 0,3 | — | — | 3 | — | numérique lent |

Dimensions en mm. Toutes sont au-dessus des minimums JLCPCB (piste et isolement 0,10 sans
surcoût, via gratuite trou ≥ 0,3 / pastille ≥ 0,4, anneau de via 0,05) : contrôle par
`check_classes.py`.

**Isolements.** 0,15 mm pour les classes routées fin (≤ 0,34 mm) ; 0,20 mm pour les
classes larges (≥ 0,5 mm), où le cuivre épais et les zones demandent plus de marge de
gravure. Aucune contrainte de tension : la carte ne dépasse pas 8,4 V, et IPC-2221
(tableau 6-1, 0–15 V) demande 0,1 mm entre conducteurs externes nus et 0,13 mm entre
pattes de composants. Les écarts de pastilles des empreintes (0,15 au LGA-14 de l'IMU, 0,20
au LQFP-144, au QFN du chargeur, à l'USB-C, au SOT-583) restent tous ≥ aux isolements des
classes qui s'y raccordent : le DRC ne relève aucune violation pastille-pastille, et
aucune règle d'exception n'a été nécessaire.

**Courant (A).** Colonne « Current (A) » de l'autorouteur du fork : il pose à côté de
chaque via routé d'un net autant de vias que le courant en demande (1,41 A par via de
0,3 mm, IPC-2221). Valeur = courant du raccord le plus chargé qui change de couche. GND,
COMMUTATION et les classes de signal n'en ont pas : leurs vias ne portent qu'une broche
(GND : chaque pastille a sa via vers le plan), ou ils n'ont pas de via du tout.

**Étape.** Colonne « Stage » : 1 = puissance, commutation, alimentations, GND, émetteurs
pulsés (boucles de courant à garder courtes, routées d'abord) ; 2 = analogique, quartz,
paire USB ; 3 = le reste.

## Réglages de l'autorouteur du fork

Écrits dans `pcbnew.native_autorouter` du `.kicad_pro` :

- étape et courant de chaque net, selon sa classe (le fork les stocke net par net) ;
  les 279 nets ont une entrée, contrôlée par `check_classes.py` ;
- COMMUTATION limitée à F.Cu, sans nouvelle via : le nœud SW reste sur la couche des
  composants (U102, L101, U103, L102 sont tous sur F.Cu), surface minimale ;
- In1.Cu fermée au routage (plan GND plein, rôle des couches accepté le 02/10/2026).

Onglet « Rules » : les deux règles d'étranglement sont lues pendant le routage (largeurs
sous les composants denses) ; l'isolement analogique contre bruit aussi (isolement entre
classes) ; les trois règles de perçage ne concernent que les pastilles et sont vues à la
validation. À vérifier à l'ouverture du dialogue.

## Motifs d'affectation

Jokers KiCad (`*`, `?`, ancrés, sensibles à la casse) sur les noms complets.

| Classe | Motifs |
|---|---|
| PACK | `VPACK` |
| VBAT | `VBAT`, `/Alimentation/VBAT_SW_IN` |
| MOTEUR | `/Moteurs/MOT_*_OUT?` |
| CHARGEUR | `/Alimentation/VBUS_IN`, `/Alimentation/PMID`, `/Alimentation/SNS_CHG` |
| COMMUTATION | `/Alimentation/SW_CHG`, `/Alimentation/SW_BUCK` |
| AMORCAGE | `/Alimentation/BTST`, `/Alimentation/BST_BUCK`, `/Moteurs/CP?_?`, `/Moteurs/VCP_?` |
| ALIM_LOGIQUE | `/Alimentation/REGN`, `+3V3*`, `/Moteurs/ENC_5V` |
| GND | `GND` |
| IMPULSION | `/Barrette/IR_*`, `/Capteurs/LAS_*`, `/IHM/BUZZ_D` |
| ANALOGIQUE | `/Capteurs/PD_*`, `/Capteurs/TIA_*`, `/Capteurs/FB_*`, `/Capteurs/G_*`, `/Capteurs/CG_*`, `/Capteurs/AMP_*`, `/Capteurs/VREF_*`, `/Capteurs/U50?_SPARE*`, `RX_*`, `/Moteurs/IPROPI_*`, `IPROPI_?`, `/Moteurs/VREF_MOT`, `VBAT_SENSE`, `LINE_??`, `/Alimentation/FB_BUCK`, `/Alimentation/RT_BUCK`, `/Alimentation/SS_BUCK`, `/Alimentation/ILIM`, `/Alimentation/TS`, `/Alimentation/MID_R` |
| HORLOGE | `/MCU/OSC_*`, `/MCU/XTAL_OUT` |
| USB | `USB_D_?`, `/Alimentation/USB_C_D_?` |
| Default | tous les autres nets |

Contrôles faits le 2 octobre 2026 :

- un net → une classe, aucun motif mort, aucun net d'une classe de puissance oublié dans
  Default (`check_classes.py`) ;
- **affectation relue par KiCad lui-même** : sur une copie, chaque classe à tour de rôle
  reçoit une largeur de 50 mm ; le contrôle « pad_no_room_at_class_width » cite alors
  chaque pastille avec la classe que KiCad lui attribue. Résultat identique à la liste
  ci-dessous pour les 11 classes testées (GND et Default exceptées, déduites) ; seules
  J101.B4/B9, superposées à A9/A4 sur le même net VBUS_IN, ne sont citées qu'une fois.
  Ce contrôle a fait corriger un motif `/Moteurs/CP[HL]_?` : les crochets ne sont pas
  des jokers KiCad, le motif est devenu `/Moteurs/CP?_?`.
- après les modifications du 07/10/2026, ALIM_LOGIQUE relue de la même façon (143
  pastilles, dont J301.4, J351.4, U302.3/5, C311.1) ; USB relue par un isolement de classe
  sondé à 3 mm, car le contrôle d'échappement ne cite plus les pastilles d'une paire
  reconnue : les quatre nets renommés sont bien dans USB.

Paires USB renommées le 07/10/2026 (`USB_D_P`/`USB_D_N`, `/Alimentation/USB_C_D_P`/`USB_C_D_N`) :
KiCad les reconnaît désormais comme paires, et le routeur de paires du fork peut les tirer
couplées à 0,34 / 0,20 mm.

## Liste exhaustive net → classe

Default contient 117 nets numériques lents et 55 broches non connectées. Il est utilisé
volontairement comme classe « numérique » : chaque net de la liste Default ci-dessous a
été relu (SPI, I²C, GPIO, grilles des MOSFET, LED témoins, codeurs, SWD, BOOT0, NRST,
VCAP1/2 du MCU, équilibrage des cellules à 75–88 mA au plus).

### PACK — 1 nets

`VPACK`

### VBAT — 2 nets

`/Alimentation/VBAT_SW_IN`, `VBAT`

### MOTEUR — 4 nets

`/Moteurs/MOT_L_OUT1`, `/Moteurs/MOT_L_OUT2`, `/Moteurs/MOT_R_OUT1`, `/Moteurs/MOT_R_OUT2`

### CHARGEUR — 3 nets

`/Alimentation/PMID`, `/Alimentation/SNS_CHG`, `/Alimentation/VBUS_IN`

### COMMUTATION — 2 nets

`/Alimentation/SW_BUCK`, `/Alimentation/SW_CHG`

### AMORCAGE — 8 nets

`/Alimentation/BST_BUCK`, `/Alimentation/BTST`, `/Moteurs/CPH_L`, `/Moteurs/CPH_R`, `/Moteurs/CPL_L`, `/Moteurs/CPL_R`, `/Moteurs/VCP_L`, `/Moteurs/VCP_R`

### ALIM_LOGIQUE — 5 nets

`+3V3`, `+3V3A`, `+3V3_BLE`, `/Alimentation/REGN`, `/Moteurs/ENC_5V`

### GND — 1 nets

`GND`

### IMPULSION — 21 nets

`/Barrette/IR_A00`, `/Barrette/IR_A01`, `/Barrette/IR_A02`, `/Barrette/IR_A03`, `/Barrette/IR_A04`, `/Barrette/IR_A05`, `/Barrette/IR_A06`, `/Barrette/IR_A07`, `/Barrette/IR_A08`, `/Barrette/IR_A09`, `/Barrette/IR_A10`, `/Barrette/IR_A11`, `/Barrette/IR_BANK_A_N`, `/Barrette/IR_BANK_B_N`, `/Capteurs/LAS_FL_A`, `/Capteurs/LAS_FL_K`, `/Capteurs/LAS_F_A`, `/Capteurs/LAS_F_K`, `/Capteurs/LAS_L_A`, `/Capteurs/LAS_L_K`, `/IHM/BUZZ_D`

### ANALOGIQUE — 53 nets

`/Alimentation/FB_BUCK`, `/Alimentation/ILIM`, `/Alimentation/MID_R`, `/Alimentation/RT_BUCK`, `/Alimentation/SS_BUCK`, `/Alimentation/TS`, `/Capteurs/AMP_F`, `/Capteurs/AMP_FL`, `/Capteurs/AMP_L`, `/Capteurs/CG_F`, `/Capteurs/CG_FL`, `/Capteurs/CG_L`, `/Capteurs/FB_F`, `/Capteurs/FB_FL`, `/Capteurs/FB_L`, `/Capteurs/G_F`, `/Capteurs/G_FL`, `/Capteurs/G_L`, `/Capteurs/PD_F`, `/Capteurs/PD_FL`, `/Capteurs/PD_L`, `/Capteurs/TIA_F`, `/Capteurs/TIA_FL`, `/Capteurs/TIA_L`, `/Capteurs/U501_SPARE_3`, `/Capteurs/U502_SPARE`, `/Capteurs/U502_SPARE_3`, `/Capteurs/U504_SPARE_3`, `/Capteurs/U504_SPARE_4`, `/Capteurs/VREF_MID`, `/Capteurs/VREF_MID_R`, `/Capteurs/VREF_RX`, `/Moteurs/IPROPI_L_RAW`, `/Moteurs/IPROPI_R_RAW`, `/Moteurs/VREF_MOT`, `IPROPI_L`, `IPROPI_R`, `LINE_00`, `LINE_01`, `LINE_02`, `LINE_03`, `LINE_04`, `LINE_05`, `LINE_06`, `LINE_07`, `LINE_08`, `LINE_09`, `LINE_10`, `LINE_11`, `RX_F`, `RX_FL`, `RX_L`, `VBAT_SENSE`

### HORLOGE — 3 nets

`/MCU/OSC_IN`, `/MCU/OSC_OUT`, `/MCU/XTAL_OUT`

### USB — 4 nets

`/Alimentation/USB_C_D_N`, `/Alimentation/USB_C_D_P`, `USB_D_N`, `USB_D_P`

### Default — 172 nets

`/Alimentation/BTN_N`, `/Alimentation/CBSET_R`, `/Alimentation/CC1`, `/Alimentation/CC2`, `/Alimentation/CD`, `/Alimentation/CHG_LED_A`, `/Alimentation/CHG_PG`, `/Alimentation/CHG_STAT`, `/Alimentation/EN_BUCK`, `/Alimentation/PACK_MID`, `/Alimentation/PWR_G`, `/Alimentation/Q101_G`, `/Alimentation/Q104_G`, `/Barrette/Q401_G`, `/Barrette/Q402_G`, `/Capteurs/Q501_G`, `/Capteurs/Q521_G`, `/Capteurs/Q541_G`, `/Capteurs/TXAC_F`, `/Capteurs/TXAC_FL`, `/Capteurs/TXAC_L`, `/IHM/BZAC`, `/IHM/D606_A`, `/IHM/D608_A`, `/IHM/D609_A`, `/IHM/Q601_G`, `/IHM/Q602_G`, `/IHM/TRACK_SW`, `/MCU/BOOT0`, `/MCU/NRST`, `/MCU/SWCLK`, `/MCU/SWDIO`, `/MCU/SWO`, `/MCU/VCAP1`, `/MCU/VCAP2`, `/Moteurs/ENC_L_A_RAW`, `/Moteurs/ENC_L_B_RAW`, `/Moteurs/ENC_R_A_RAW`, `/Moteurs/ENC_R_B_RAW`, `/Moteurs/IMODE_L`, `/Moteurs/IMODE_R`, `/Moteurs/PMODE_L`, `/Moteurs/PMODE_R`, `/Temoins de ligne/LGN00`, `/Temoins de ligne/LGN00_A`, `/Temoins de ligne/LGN01`, `/Temoins de ligne/LGN01_A`, `/Temoins de ligne/LGN02`, `/Temoins de ligne/LGN02_A`, `/Temoins de ligne/LGN03`, `/Temoins de ligne/LGN03_A`, `/Temoins de ligne/LGN04`, `/Temoins de ligne/LGN04_A`, `/Temoins de ligne/LGN05`, `/Temoins de ligne/LGN05_A`, `/Temoins de ligne/LGN06`, `/Temoins de ligne/LGN06_A`, `/Temoins de ligne/LGN07`, `/Temoins de ligne/LGN07_A`, `/Temoins de ligne/LGN08`, `/Temoins de ligne/LGN08_A`, `/Temoins de ligne/LGN09`, `/Temoins de ligne/LGN09_A`, `/Temoins de ligne/LGN10`, `/Temoins de ligne/LGN10_A`, `/Temoins de ligne/LGN11`, `/Temoins de ligne/LGN11_A`, `/Traces et turbine/BLE_LED_A`, `/Traces et turbine/BLE_PG`, `/Traces et turbine/ESC_SIG`, `/Traces et turbine/FLASH_nHOLD`, `/Traces et turbine/FLASH_nWP`, `/Traces et turbine/Q702_G`, `BLE_PWR_EN`, `BLE_RX`, `BLE_TX`, `BUZZER`, `CHG_CD_EN`, `CHG_INT`, `ENC_L_A`, `ENC_L_B`, `ENC_R_A`, `ENC_R_B`, `ESC_PWM`, `FLASH_MISO`, `FLASH_MOSI`, `FLASH_SCK`, `FLASH_nCS`, `IMU_INT1`, `IMU_MISO`, `IMU_MOSI`, `IMU_SCK`, `IMU_nCS`, `IR_BANK_A`, `IR_BANK_B`, `MOT_L_IN1`, `MOT_L_IN2`, `MOT_L_nFAULT`, `MOT_L_nSLEEP`, `MOT_R_IN1`, `MOT_R_IN2`, `MOT_R_nFAULT`, `MOT_R_nSLEEP`, `PWR_BTN`, `PWR_HOLD`, `SCL2`, `SDA2`, `START_BTN`, `SW_DOWN`, `SW_LEFT`, `SW_PUSH`, `SW_RIGHT`, `SW_UP`, `TRACK_EN`, `TX_F`, `TX_FL`, `TX_L`

Plus 55 broches non connectées (`unconnected-…`, une pastille chacune, rien à router).
