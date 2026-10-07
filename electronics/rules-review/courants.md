# Bilan des courants

Une ligne par net ou groupe de nets, avec la source de chaque chiffre : [courants.csv](courants.csv)
(séparateur `;`, décimales à virgule). Ce document en donne la lecture et les points
restés ouverts. Fiches lues le 2 octobre 2026 chez les fabricants, sauf mention.

## Chemin de la puissance

```
pack 2S LiFePO4 ─ MR30 J102 ─┬─ VPACK ─────────────────────────── ESC J103 (turbine, 10 A)
                             ├─ VPACK ─ BAT du BQ25887 U102 (charge, 1,5 A ; 2,2 A maxi)
                             └─ VPACK ─ F101 ─ VBAT_SW_IN ─ Q102 ∥ Q103 ─ VBAT ─┬─ DRV8874 U301 (moteur gauche)
                                                                               ├─ DRV8874 U351 (moteur droit)
                                                                               ├─ TPS62933 U103 ─ +3V3
                                                                               ├─ TPS70950 U302 ─ ENC_5V (codeurs IE2)
                                                                               └─ LED IHM (R615, R617, R618)
USB-C J101 ─ VBUS_IN ─ U101 ─ U102 VBUS ─ PMID ─ L101 ─ SW_CHG (boost 1,5 MHz) ─ SNS_CHG ─ BAT
```

Le courant de la turbine ne traverse ni le fusible ni l'interrupteur : il va directement de
la MR30 à l'ESC. Le retour GND porte la turbine **et** la branche VBAT.

## Chiffres retenus

| Chemin | Continu | Crête | Base |
|---|---|---|---|
| MR30 → ESC (VPACK) | **10 A** | 15 A (pointe de l'ESC) | décision de l'utilisateur ; aucune donnée de la turbine EDF 27 |
| Branche VBAT (F101, Q102/Q103) | 2,3 A | **3,9 A** | 2 × 1 A + buck + LED ; pire cas : deux moteurs bloqués à 7,3 V |
| GND sous la MR30 | 12,3 A | **13,9 A** | somme des deux |
| Un pont, une sortie moteur | 1,0 A | **1,42 A** | blocage du 1524T006SR à 7,3 V (R = 5,15 Ω) |
| Entrée USB (VBUS, PMID, SW_CHG) | 2,4 A | **3,0 A** (3,5 A crête dans L101) | limite ILIM 2,90 A typ., IINDPM 3,0 A |
| Charge (BAT, SNS) | 1,5 A | 2,2 A | ICHG par défaut / maxi |
| +3V3 | 0,35 A | **1,2 A** | cumul des crêtes ; buck de 3 A |
| SW_BUCK | 0,4 A | 1,6 A | I_out + ondulation/2 ; 4,2–5,8 A en défaut |
| Banc IR (6 LED) | 0,06 A | 0,126 A | un banc à la fois |

## Seuil de courant des ponts : jamais atteint

Le seuil du DRV8874 vaut I_TRIP = V_REF / (A_IPROPI × R_IPROPI) = 1,336 V / (450 µA/A ×
1 kΩ) = **2,97 A**. Le moteur Faulhaber 1524T006SR a une résistance de 5,15 Ω : bloqué sous
7,3 V, il tire 1,42 A (1,36 A avec les 0,2 Ω du pont). La limitation de courant du pont
ne joue donc jamais avec ce moteur : le dimensionnement des pistes suit le **blocage**
(1,42 A), pas le seuil du pont. La note du schéma qui vise 3 A date du moteur GM12-N20.

## Points à confirmer

Chiffres :

1. **Courant de la turbine** : 10 A est une décision, pas une mesure. À mesurer sous
   6,4–7,3 V ; l'ESC accepte 12 A continu et 15 A en pointe.
2. **Buzzer** : modèle non identifié (valeur « 9 × 5,5 mm », empreinte ABI-009-RC de
   12 mm). La note du schéma dit 200 mA ; l'ABI-009 tire 30 mA sous 6 V.
3. **LED IHM** : aucune référence de LED, Vf supposés. Traité le 07/10/2026 : R615, R617,
   R618 passent en 0603 (100 mW) à 390 Ω / 560 Ω / 560 Ω, soit ≈ 10 mA par LED et 47 à
   50 mW à 7,3 V (la moitié de la puissance nominale). Régime de TRACK_SW toujours à préciser.
4. **ESP32-C3** : 335 mA de crête d'émission, comptés dans la crête +3V3. S'il est coupé
   par Q701 en course, la crête tombe à environ 0,9 A.
5. **Moteurs** : le « 1 A réel » dépasse le courant nominal du 1524 (0,545 A) ; tenable
   en intermittent seulement.

Constats hors règles de conception, à traiter dans le schéma :

6. **Codeurs IE2 sous-alimentés** : traité le 07/10/2026. Un TPS70950 (U302, entrée VBAT,
   EN sur +3V3) fournit `ENC_5V` à J301 et J351 broche 4 : ≥ 4,74 V à VBAT 5,0 V. Les
   sorties des codeurs montent alors à > 4,5 V ; elles arrivent sur PC6, PC7, PB4 et PB5
   (broches 96, 97, 134, 135), toutes FT_h (DS13313 p. 66–70), et EN sur +3V3 garantit que
   le 5 V n'apparaît qu'avec l'alimentation du MCU.
7. **F101 sans référence** : valeur « 12 A », empreinte 1206, aucun MPN. Un fusible 12 A
   sur une branche dont le pire cas fait 3,9 A ne coupe un défaut qu'au-delà d'environ
   40 A en quelques secondes (Bourns SF-1206HH12M-2 : coupure en ≤ 5 s à 350 %).
8. **Notes du schéma périmées** : « IIN_max ≈ 2,4 A » (383 Ω donne 2,9 A ; il faudrait
   ≈ 460 Ω), « 3,3 V / 2 A » (le TPS62933 donne 3 A), I_TRIP visant le GM12-N20.
9. **L101 « 4 A » et L102 « 3 A »** : préciser Isat ou Irms ; la limite haute du buck en
   défaut (4,2–5,8 A) dépasse 3 A.

Sources non officielles : la fiche STM32H723 (DS13313 Rev 4) a été lue sur un miroir
(st.com refusait la connexion) ; la consommation du LSM6DSO (0,55 mA) n'a pas été vérifiée
chez ST. Ni l'une ni l'autre ne change une largeur de piste.
