#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Table de placement du PCB — pur Python, sans pcbnew.

Principe de la refonte du 4 septembre : **chaque passif se pose contre son
actif**. Les rangees de resistances alignees loin de leur circuit ont disparu ;
a leur place, une grappe par fonction, posee au contact du boitier qu'elle
sert. Ce qui ne pouvait pas suivre (les passifs lents des deux ponts en H,
coinces derriere l'equerre moteur) est regroupe en un bloc unique, pas
disperse.

Zonage :
  - ARRIERE (y 120 a 133,7, la seule bande libre devant les equerres) :
    ponts en H aux deux angles avec leur decouplage, chargeur au centre
    gauche, USB au milieu, et a droite le trio d'alimentation - pack en
    XT30 VERTICAL, nappe d'equilibrage XH verticale, et les deux gros
    percages ou se soudent les fils de l'ESC, qui se dresse sur la tranche
    juste au-dessus. Le pack se presente derriere le robot, sur la tranche :
    les deux cordons montent a la verticale.
  - COULOIR (x 142,6 a 167,4, y 133,7 a 143) entre les deux equerres et le
    trou de turbine : la centrale inertielle, au plus pres du centre de
    rotation, et la broche unique de commande de l'ESC.
  - EPAULES (y 157 a 182) : a gauche les passifs lents du pont gauche, la
    configuration du chargeur, le buzzer et le module OTA ; a droite le
    convertisseur 3,3 V - DESCENDU dans l'epaule, il ne mange plus la bande
    arriere - l'interrupteur general et la station de telemetrie a 75 deg.
  - IHM (y 179 a 216) : ecran sur entretoises, MCU a 45 deg dessous et son
    decouplage loge dans les quatre poches entre le losange du boitier et
    les bords du module. Manettes A GAUCHE (joystick puis les deux boutons
    dessous), telemetres A DROITE : on regarde l'ecran par l'arriere, la
    main droite tombe sur les optiques, la gauche sur le joystick.
  - AVANT (y 216 a 250) : chaines analogiques des trois telemetres, flash,
    mux de surveillance, temoins.
  - NEZ (y 250 a 285) : la station a 15 deg occupe la passerelle centrale ;
    la moustache et SES PASSIFS sont passes DESSOUS, contre les capteurs,
    ce qui libere toute la face avant de l'arc.

Verifie par fit_layout.py (polygone + collisions), qui ecrit layout_fit.json.
Les positions verrouillees dans pcbnew priment : lock_import.py les releve
dans locked.json, applique ici en dernier.
"""
import json
import math
import os

CX, AXLE, ARC = 155.0, 145.0, 134.6   # capteurs 1 mm en dedans : l'ITR8307
                                      # fait 7,55 mm de haut, coins a r 139
# La turbine EDF 27 est enfin POSEE sur la carte (empreinte
# Pacabot:Turbine_EDF27_dessus, reference M3, cf. place_pcb.py) : elle
# apporte son propre percage d air dia 34 sur Edge.Cuts et ses trois vis M2 a
# 42,5 de BCD, qui manquaient - rien ne la fixait. Le rayon qui compte n est
# plus celui du trou mais celui de son COURTYARD, la levre dia 36,7 qui
# porte sur l anneau de carte : 18,6 mm.
TURBINE_XY = (155.0, 159.0)
TURBINE = TURBINE_XY + (18.6,)
TURBINE_BCD, TURBINE_VIS = 42.50, (-90.0, 30.0, 150.0)   # cf. gen_turbine_footprint

P = {}                                    # ref -> (x, y, rot, side)


def at(ref, x, y, rot=0, side='F'):
    P[ref] = (x, y, rot, side)


def row(refs, x0, y, dx=3.2, rot=0, side='F'):
    for i, r in enumerate(refs):
        at(r, x0 + i * dx, y, rot, side)


def grid(refs, x0, y0, nx, dx=2.7, dy=2.9, rot=0, side='F'):
    """Grappe compacte : la forme naturelle d un paquet de 0402 autour d un CI."""
    for i, r in enumerate(refs):
        at(r, x0 + (i % nx) * dx, y0 + (i // nx) * dy, rot, side)


def mirror(pairs):
    """(ref_ouest, ref_est) : l est recoit la position miroir de l ouest."""
    for w, e in pairs:
        x, y, rot, side = P[w]
        at(e, 2 * CX - x, y, -rot if rot in (90, -90) else rot, side)


# ===================================================== MOUSTACHE (face dessous)
# Les douze capteurs sur l'arc r 134,6 centre sur l'essieu, et - c'est le
# changement - LEURS PASSIFS AVEC EUX, sur la meme face. Ils etaient dessus,
# a l'aplomb : trois vias par capteur pour rien, et surtout toute la face
# avant de l'arc occupee, alors que c'est le seul endroit ou la station de
# telemetrie avant peut tenir. Dessous, ils tombent contre leur capteur.
S_OFF = [-74, -56, -38, -20, -12, -4, 4, 12, 20, 38, 56, 74]


def arc_at(ref, s, r, rot_extra=90, side='B'):
    th = s / 140.0
    at(ref, CX + r * math.sin(th), AXLE + r * math.cos(th),
       rot_extra - math.degrees(th), side)


R_TEMOIN = 137.0                      # LED de presence de ligne : entre le
                                      # capteur (r 134,6, dessous) et le bord
                                      # avant de l arc (r 139,9), sur le
                                      # DESSUS - c'est ce qu'on regarde.
for i, s_ in enumerate(S_OFF):
    th = s_ / 140.0
    rs = ARC + (0.15 if abs(s_) == 74 else 0)   # extremes : 27 um de marge
    at(f'U{401 + i}', CX + rs * math.sin(th), AXLE + rs * math.cos(th),
       -math.degrees(th), 'B')
    # la LED a l aplomb de son capteur, sa resistance juste a cote
    arc_at(f'D{401 + i}', s_ - 2.0, R_TEMOIN, side='F')
    arc_at(f'R{445 + i}', s_ + 2.6, R_TEMOIN, side='F')
    if abs(s_) < 20:                    # capteurs centraux : rangées radiales
        arc_at(f'R{401 + i}', s_, ARC - 6.3)
        arc_at(f'R{421 + i}', s_, ARC - 9.8)
        arc_at(f'C{401 + i}', s_, ARC - 13.3)
    else:                               # exterieurs : en file le long de l arc
        sg = 1 if s_ > 0 else -1
        arc_at(f'R{401 + i}', s_ + 3.2 * sg, ARC - 3.0)
        arc_at(f'R{421 + i}', s_ + 6.2 * sg, ARC - 3.0)
        arc_at(f'C{401 + i}', s_ + 9.2 * sg, ARC - 3.0)

# ====================================================== ARRIERE : puissance
# --- angles : ponts en H (U301 / U351 verrouilles) et leur decouplage.
# Le tantale de reservoir tient a gauche contre son pont ; a droite l angle
# est plein (les deux FET de coupure + l embase moteur), C354 descend dans
# l epaule avec les passifs lents.
at('J301', 96.0, 131.35, 180)
at('D608', 95.0, 121.0)                        # rouge, coin arriere ouest
at('U301', 101.5, 127.0, 90)
row(('C303', 'C305', 'C306'), 106.6, 122.4, 2.6)
at('C307', 114.4, 122.4)                       # 0805 de tete
at('C304', 110.5, 130.6)                       # tantale 7343, a plat
mirror((('D608', 'D609'),))
at('J351', 214.0, 125.0)
at('U351', 208.5, 127.0, 90)
at('C353', 206.0, 132.5); at('C355', 208.6, 132.5)   # seul ce qui tient
                                                    # vraiment contre le pont

# --- chargeur BQ25887 : etage de puissance serre autour du boitier
at('U102', 126.0, 127.0)
row(('C102', 'C103'), 120.6, 122.4, 4.0)       # PMID, deux 1210
at('L101', 129.0, 122.6)
at('C104', 132.6, 122.4)                       # BTST
at('C101', 135.0, 122.4)                       # VBUS
at('R110', 137.6, 122.4); at('D101', 140.4, 122.4)   # temoin de charge
row(('C106', 'C107'), 120.2, 131.4, 4.0)       # SNS, deux 1210
at('C108', 128.0, 131.2); at('C105', 131.0, 131.2)
at('R106', 133.6, 131.2)
at('R107', 137.6, 131.2)                       # 10R / 1W d equilibrage

# --- USB-C : protection ESD et les deux 5,1 k contre l embase
at('J101', 155.0, 124.0, 180)
at('U101', 145.6, 127.4)
at('R101', 144.6, 122.4); at('R102', 147.2, 122.4)

# --- pack, equilibrage et ESC : trois entrees verticales au bord arriere
at('J102', 164.0, 122.5)                       # XT30U-M vertical : B+ / B-
at('J104', 175.5, 122.5)                       # JST-XH : nappe d equilibrage
at('J103', 173.0, 130.0)                       # deux percages 2,6 : fils ESC
at('C704', 188.0, 130.0)                       # 220 uF au pied de l ESC
at('C705', 194.5, 130.2)

# --- coupure generale : fusible, deux FET paralleles (verrouilles)
at('F101', 185.6, 122.0)
at('SW101', 192.0, 123.4)                      # MARCHE / ARRET, sous le pouce
at('R114', 196.2, 122.6)
at('Q102', 200.4, 123.6); at('Q103', 200.4, 130.2)
# Le reste de la gestion de mise sous tension passe DESSOUS, a l aplomb des
# deux FET qu elle commande : ce ne sont que des niveaux de grille, quelques
# microamperes, et la face dessus de cet angle est prise par le reservoir de
# l ESC et l embase moteur.
grid(('R124', 'R125', 'R126', 'R127', 'R128', 'C122', 'C123'),
     184.6, 121.6, 4, 2.8, 2.9, side='B')
at('D106', 185.4, 128.0, 0, 'B'); at('Q104', 190.4, 128.6, 0, 'B')


# ================================== COULOIR : inertie et commande de turbine
# Le couloir s est elargi de 15 mm quand les zones interdites des equerres
# ont ete recalculees sur l empreinte reelle (elles s arretent a 135,05 et
# 174,95, pas a 142,6 et 167,4). Il se referme en revanche par le bas : le
# courtyard de la turbine monte a y 140,4 et sa vis avant tombe en
# (155 ; 137,75). L IMU se decale donc de l axe - 8 mm du centre de rotation,
# ce qui ne coute qu un terme centrifuge negligeable devant le gyrometre.
at('U503', 148.0, 137.4)                       # IMU, aussi pres que la vis permet
at('C566', 143.0, 136.6); at('C567', 143.0, 139.4)
# Broche COUDEE : elle regarde vers l arriere, d ou descend le fil de commande
# du variateur pose debout juste au-dessus. Une broche droite aurait demande
# au fil de faire une boucle par-dessus le corps de l ESC.
at('J702', 170.0, 143.5, 90)
at('R707', 164.5, 141.0)                       # serie de 100 R, contre la broche

# ================================ DESSOUS DE LA BANDE ARRIERE : passifs lents
# Les passifs lents des deux ponts en H et de la configuration du chargeur
# etaient exiles dans les epaules, a trente millimetres de leur circuit :
# l equerre moteur occupe toute la bande y 133,7-156,3 et il n y avait pas
# d autre place SUR LA FACE DESSUS. Il y en avait une dessous, vide, a
# l aplomb exact des boitiers - la barrette de ligne prouvait deja que la
# face arriere s assemble. Trente millimetres deviennent trois via un via.
grid(('R301', 'R302', 'C301', 'C302', 'R303',
      'R304', 'R305', 'R306', 'C308', 'C309',
      'R307', 'R308', 'R309', 'R310'), 100.6, 122.6, 5, side='B')
grid(('R353', 'R354', 'R355', 'R356', 'R357',
      'R358', 'R359', 'R360', 'C352', 'C358', 'C359'), 195.0, 122.6, 4,
     side='B')
at('C354', 204.0, 131.4, 0, 'B')               # tantale du pont droit
at('C356', 195.0, 131.4, 0, 'B'); at('C357', 198.0, 131.4, 0, 'B')
# configuration du chargeur (ILIM, TS, tirages, inhibition), sous le BQ25887
# mais decalee des vias thermiques de son pad
grid(('R103', 'R104', 'R105', 'R108', 'R109',
      'R111', 'R112', 'R113'), 117.0, 131.4, 8, side='B')
at('Q101', 138.4, 131.0, 0, 'B')

# ============================================ EPAULE OUEST (y 157 a 182)
# Liberee des deux blocs precedents, elle respire : buzzer, module OTA et
# filtres du joystick prennent leurs aises et la serigraphie redevient
# lisible - une reference illisible se paie au montage, pas au routage.
at('BZ601', 108.0, 164.0)                      # corps a +3,8 de l origine
at('R608', 122.0, 158.6); at('C606', 124.6, 158.6)
at('Q601', 122.0, 163.4)
at('R609', 125.6, 162.4); at('R610', 128.2, 162.4)
at('C607', 130.8, 162.4)
at('D610', 125.6, 165.6); at('D601', 129.2, 165.6)
# pilote des douze temoins de ligne : dessous, juste derriere l arc, a
# egale distance de ses douze LED
at('U105', 155.0, 246.0, 90, 'B')
at('C124', 155.0, 251.6, 0, 'B')

# module OTA et sa coupure d alimentation
at('J701', 118.0, 175.0, 90)                   # embase 1x04, module dessus
at('Q701', 128.0, 171.0); at('Q702', 128.0, 175.0)
at('C702', 132.0, 171.0); at('C703', 134.6, 171.0)
grid(('R703', 'R704', 'R705', 'R706'), 132.0, 175.0, 3)
at('D701', 137.4, 178.0)

# ============================================ EPAULE EST (y 157 a 182)
# convertisseur 3,3 V : descendu de la bande arriere dans l epaule, boucle
# chaude refermee sur place (entree, boitier, self, sortie en ligne)
# Le courtyard de la turbine (r 18,6) mord jusqu a x 173,6 sur l axe : toute
# la grappe du buck commence apres, en deux rangees serrees le long de la
# bande libre y 157-164 que laisse le courtyard de l equerre droite.
at('C111', 176.8, 158.6); at('C112', 181.8, 158.6)   # entree, deux 1210
at('C116', 186.4, 158.6); at('C117', 189.4, 158.6)   # sortie, deux 0805
at('U103', 177.4, 162.6)
at('L102', 182.4, 162.6)
at('C113', 186.2, 162.6); at('C114', 188.6, 162.6)
at('C115', 191.0, 162.6); at('R116', 193.4, 162.6)
at('C118', 191.4, 158.6)
row(('R115', 'R117', 'R118'), 175.2, 165.8, 2.6)
# filtre du rail analogique, juste sous la sortie du buck
at('FB101', 177.4, 171.6); at('C119', 180.6, 171.6); at('C120', 183.2, 171.6)
# ecretage VBAT et reservoir, au pied des deux FET de coupure
at('D102', 198.6, 158.6); at('C109', 208.0, 160.2); at('C110', 196.4, 163.0)


# ============================================== IHM : ecran, MCU, manettes
at('J601', 155.0, 192.0)                       # module OLED sur entretoises
# Le LQFP144 ne tient plus sous l ecran, et ce n est pas une affaire de
# millimetres : la rangee 1x4 du module traverse la carte a 10,85 mm au-dessus
# de son centre et les quatre entretoises a +/-10,35. La fenetre ou le boitier
# echappe aux trois obstacles ne commence qu a y = 208,4, c est-a-dire hors du
# module. Le LQFP100 s y glissait avec 0,17 mm de reste ; le 144 demande 4 mm
# de plus dans chaque direction.
# Devant, cette place est prise par la station a 45 deg. Le boitier passe donc
# EN FACE ARRIERE, a l aplomb de la zone libre : la face avant garde son
# quartz, ses VCAP et son groupe de reset juste au-dessus, a 1,6 mm par un via
# au lieu de plusieurs millimetres de cuivre en surface.
at('U201', 155.0, 216.0, 0, 'B')               # LQFP144, face dessous

# Decouplage du MCU : les quatre poches entre le losange du boitier et les
# bords du module. C'est la seule place a moins de 4 mm des broches
# d alimentation, et elle etait vide - le module est sur entretoises.
MCU = (155.0, 192.5)
# Les douze condensateurs qui doivent toucher le boitier : les ONZE 100 nF
# des onze broches VDD du LQFP144, plus celui de VDD33USB (broche separee sur
# ce boitier, reliee en interne sur le LQFP100).
DECO_REFS = ('C201', 'C202', 'C203', 'C204', 'C205', 'C207',
             'C217', 'C218', 'C219', 'C220', 'C221', 'C222')


def decouplage_mcu(mcu):
    """Les douze condensateurs dans les quatre poches du losange.

    Douze condensateurs en couronne carree autour du boitier, sur la MEME
    face que lui : onze 100 nF pour les onze broches VDD du LQFP144, plus
    celui de VDD33USB. Trois par cote a 13,5 mm de l axe, soit 2 mm des
    pastilles - c est la distance qui compte pour un decouplage, et elle ne
    depend plus d une geometrie sous l ecran.
    """
    # couronne carree autour du boitier pose a plat : trois par cote, a
    # 13,5 mm de l axe, soit 2 mm des pastilles
    pts = [(mcu[0] + dx, mcu[1] + 13.5 * sy)
           for sy in (-1, 1) for dx in (-7.0, 0.0, 7.0)]
    pts += [(mcu[0] + 13.5 * sx, mcu[1] + dy)
            for sx in (-1, 1) for dy in (-7.0, 0.0, 7.0)]
    for ref, (x, y) in zip(DECO_REFS, pts):
        at(ref, x, y, 0, 'B')


decouplage_mcu(MCU)
at('C212', 149.0, 209.0); at('C213', 161.0, 209.0)     # VCAP
at('R201', 166.0, 206.0); at('C214', 168.6, 206.0)   # tirage NRST
at('R202', 143.0, 206.4); at('R203', 145.6, 206.4)
at('C206', 139.5, 212.6)                       # reservoir 4u7 du rail 3V3
row(('C208', 'C209', 'C210', 'C211'), 138.0, 209.6, 2.6)   # VDDA et VREF+
at('R601', 149.6, 177.0); at('R602', 152.2, 177.0)     # tirage I2C2 de l ecran

# quartz sous l ecran - descendu de 4 mm : le losange du LQFP144 monte a
# 16,5 mm du centre au lieu de 12,4, il mordait sur le boitier du quartz
at('Y201', 155.0, 214.0)
at('C215', 149.6, 214.0, 90); at('C216', 160.4, 214.0, 90)
at('R204', 144.6, 214.0)

# --- manettes A GAUCHE de l ecran, boutons dessous (main gauche ;
#     la droite tombe sur les optiques, de l autre cote)
at('SW601', 131.0, 189.0)                      # joystick SKRHABE010
at('SW602', 132.0, 200.0)                      # START
at('SW603', 134.5, 206.5)                      # RESET
grid(('R603', 'R604', 'R605', 'R606', 'R607',
      'C601', 'C602', 'C603', 'C604', 'C605'), 115.0, 181.0, 10)

# La bande de temoins sous l ecran est vide : les six LED generiques (trois
# rails, trois etats) ont ete rendues le 4 septembre. Ce qu on regarde
# pendant un essai, c est la moustache, et chaque capteur y a maintenant sa
# LED - voir plus bas D401 a D412.

# ================================ AVANT : surveillance, flash, analogique
at('J201', 139.0, 210.0)                       # TC2030, pastilles nues
# Le multiplexeur de surveillance a disparu avec le passage au LQFP144 :
# VBAT_SENSE, IPROPI_L et IPROPI_R ont chacun leur entree d ADC.
at('R119', 164.0, 216.6); at('R120', 164.0, 219.2); at('C121', 164.0, 221.8)
at('U701', 145.0, 231.0)                       # flash SPI
at('R701', 139.6, 235.4); at('R702', 142.2, 235.4); at('C701', 144.8, 235.4)

# Amplis de telemetrie. U501 porte les trois transimpedances : son entree est
# le noeud le plus fragile de la carte (220 k de contre-reaction sur une
# photodiode), donc ce sont ses SIX passifs de contre-reaction qui viennent se
# coller a lui, en rangee immediatement dessous. U502, second etage a basse
# impedance, se contente d etre a cote.
at('U501', 162.0, 228.0); at('U502', 150.5, 228.0)
row(('R504', 'C501', 'R524', 'C521', 'R544', 'C541'), 156.4, 233.4, 2.6)


# trois blocs identiques de chaine analogique : F | FL | L
# (la paire de contre-reaction de chaque station est remontee contre U501)
def bloc(x0, refs):
    for i, r in enumerate(refs):
        at(r, x0 + 2.5 * (i % 3), 239.4 + 3.1 * (i // 3))


bloc(143.5, ('R505', 'R506', 'R507', 'R508', 'C502', 'C503', 'C504'))
bloc(152.5, ('R525', 'R526', 'R527', 'R528', 'C522', 'C523', 'C524'))
bloc(161.5, ('R545', 'R546', 'R547', 'R548', 'C542', 'C543', 'C544'))
# references communes des amplis
row(('R561', 'R562', 'R563', 'R564', 'C561'), 146.6, 249.4, 2.4)
row(('C562', 'C563', 'C564', 'C565'), 148.0, 252.2, 2.4)

# ------------------ stations de telemetrie : 15 / 45 / 75 deg -------------
# L'empreinte Telemetry_Duo_Coude porte les DEUX boitiers couches (VCSEL
# TO-46 + photodiode T-1 3/4) et le pare-soleil imprime qui se visse par le
# dessous. Elle vise +X au repos : un azimut `deg` compte depuis l'avant
# vers la droite de l'ecran demande donc une rotation deg - 90.
# L'origine est l'axe de la vis ; la face avant du pare-soleil est 10 mm plus
# loin dans l'axe de visee. Les faisceaux passent a 6 mm au-dessus de la
# carte : ils survolent sans encombre tout ce qui les separe du bord.
X_AVANT = 10.0


def station(ref, deg, x, y):
    at(ref, x, y, deg - 90)


station('TM501', 15, 155.0, 265.0)             # avant, sur la passerelle
station('TM521', 45, 181.0, 201.0)   # remontee : le LQFP144 lui a
                                     # pris sa place dans le cou
station('TM541', 75, 192.0, 176.0)             # epaule droite
# electronique de chaque station, contre son support
at('Q501', 160.0, 244.0)
at('R501', 163.0, 244.0); at('R502', 165.6, 244.0); at('R503', 165.6, 247.0)
at('C505', 160.0, 247.0); at('D503', 162.8, 247.0); at('D504', 160.0, 250.0)
at('Q521', 177.6, 200.6)
at('R521', 180.6, 199.6); at('R522', 180.6, 202.6); at('R523', 177.6, 197.4)
at('C525', 174.2, 198.2); at('D523', 174.2, 201.0); at('D524', 177.6, 203.8)
at('Q541', 179.0, 180.0)
at('R541', 182.0, 179.0); at('R542', 182.0, 182.0); at('R543', 179.0, 183.0)
at('C545', 176.2, 180.0); at('D543', 176.2, 183.0); at('D544', 179.0, 177.0)

# ============================================ NEZ : emetteurs et eclairage
# La face avant de l arc est libre depuis que les passifs de la moustache
# sont passes dessous : les deux bancs d emetteurs IR y tombent au plus pres
# de leurs douze diodes, et l eclairage de suivi camera au tout devant.
at('Q401', 125.0, 272.0); at('R441', 128.4, 271.4); at('R442', 130.8, 271.4)
at('Q402', 185.0, 272.0); at('R443', 181.6, 271.4); at('R444', 179.2, 271.4)
at('D606', 155.0, 283.0); at('R615', 155.0, 280.0); at('Q602', 172.0, 277.0); at('R619', 175.4, 276.4); at('R620', 177.8, 276.4)
at('R617', 97.5, 121.0, 180); at('R618', 212.5, 121.0)   # series des coins

# ---------------------------------------------------------------- figes
# Ce que pcbnew porte comme verrouille prime sur tout ce qui precede :
# lock_import.py le releve dans locked.json.
LOCKED = set()
_LOCKFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'locked.json')
if os.path.exists(_LOCKFILE):
    for ref, (x, y, rot, side) in json.load(open(_LOCKFILE)).items():
        at(ref, x, y, rot, side)
        LOCKED.add(ref)
# le MCU suit l ecran, sinon le losange sort de sous le module
LOCKED |= {'U201'}
LOCKED |= {'TM501', 'TM521', 'TM541'}   # visee imposee, pas negociable

# boitiers ronds : cercle exact (buzzer)
ROUND = {'BZ601': 6.3}
# Aucune tolerance entre les embases du bord arriere : l ancienne table en
# accordait trois, heritees d un temps ou l ESC arrivait par un XT30 couche.
# Le controleur en profitait pour glisser les percages de l ESC sous l embase
# USB - six pastilles de nets differents en contact.
PAIR_OK = set()
# Pieces dont le corps deborde volontairement du contour : les embases du
# bord arriere, les ensembles moteur (roue comprise), les capteurs de bout de
# moustache poses a la garde cuivre, les temoins de coin - et les trois
# stations de telemetrie, dont le pare-soleil regarde forcement dehors.
OVERHANG = {'J101', 'J102', 'J103', 'J104', 'TM501', 'TM521', 'TM541',
            'M1', 'M2', 'D608', 'D609', 'R617', 'R618',
            'U401', 'U402', 'U411', 'U412'}
# Paires verrouillees dont les boites se recouvrent depuis toujours : les
# courtyards, eux, ne se touchent pas.
PAIR_OK |= {frozenset(('J301', 'U301')), frozenset(('J351', 'U351')),
            frozenset(('J601', 'U201')), frozenset(('D608', 'R617')),
            frozenset(('D609', 'R618')), frozenset(('M1', 'J301')),
            frozenset(('M2', 'J351'))}
