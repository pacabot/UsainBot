# -*- coding: utf-8 -*-
"""
Dimensionnement de la turbine d'appui d'UsainBot (EDF 27 mm AEORC).

Repond a trois questions, dans cet ordre :
  1. de quelle force d'appui a-t-on besoin pour tenir R = 200 mm a la vitesse visee ?
  2. qu'est-ce que cette turbine sait produire, en poussee directe puis en depression ?
  3. qu'est-ce qui limite reellement le chrono une fois l'appui installe ?

Cotes et parametres robot repris de electronics/kicad-lib/faulhaber_geom.py et du
document d'architecture. Modele du ventilateur reconstruit a partir des deux points
de fonctionnement publies par le revendeur (7,4 V et 8,4 V) : voir HYPOTHESES.

    python3 turbineEDF27_dimensionnement.py
"""

import math

# ==========================================================================
# HYPOTHESES  — tout ce qui n'est pas mesure est ici, et signale
# ==========================================================================

RHO      = 1.204     # kg/m3, air a 20 C
G        = 9.81

# --- robot -----------------------------------------------------------------
M_NU     = 0.280     # kg, masse balayee 250-300 g dans l'optimisation de roue
M_TURBO  = 0.011 + 0.008 + 0.030   # turbine + ESC + surdimensionnement du pack
M        = M_NU + M_TURBO
MU       = 0.90      # silicone Shore A20 sur bache PVC, plage retenue 0,7-1,1
MU_EXP   = 0.00      # sensibilite a la charge : mu = mu0 * (N/N0)^-MU_EXP
R_VIRAGE = 0.200     # m, rayon minimal du reglement
CLEAR    = 0.005     # m, garde au sol actuelle (faulhaber_geom.CLEARANCE)
CRR      = 0.05      # roulement silicone tendre sur bache, 0,03 a 0,08

# --- motorisation Faulhaber 1524T006SR + 15/10K 3,33:1 ---------------------
KM       = 5.99e-3   # Nm/A, vaut aussi kE en V.s/rad
R_MOT    = 5.15 + 0.40   # ohm, bobinage + les 0,4 ohm de la nappe du codeur
I_MAX    = 1.00      # A, limite imposee par la nappe du codeur IE2
RED      = 3.33
ETA_RED  = 0.90
R_ROUE   = 0.0215    # m, JSumo JS4311 ø43

# --- turbine : deux points publies (AEO RC POWER-X 27 mm, M1204-14500KV) ---
V_REF    = 8.4       # V
T_REF    = 0.104 * G # N, 104 g
I_REF    = 11.0      # A
V_BUS    = 6.4       # V, 2S LiFePO4 en service
D_VEINE  = 0.0274    # m
D_MOYEU  = 0.0130    # m
K_SHUTOFF = 1.6      # Dp a debit nul / pression dynamique a debit libre (1,2 a 2,2)

# --- jupe et plenum --------------------------------------------------------
# --- limite mecanique de la chaine de traction ------------------------------
# faulhaber_geom.py : reducteur 15/10 a PALIERS FRITTES, 4 N a 6,5 mm de la face,
# porte-a-faux de roue 8,50 mm -> 3,06 N admissibles au contact de la roue.
F_RADIAL_ROUE = 3.06     # N par roue, version frittee
F_RADIAL_K    = 30.0 * 6.5 / 8.5   # N par roue, si version K a roulements
REPART_ESSIEU = 0.80     # part statique du poids sur les roues motrices
MU_PATIN      = 0.20     # patin avant, PTFE sur bache : il glisse, il n'adhere pas

# --- variateur candidat : Turnigy Multistar 6A V2 (BLHeli, OPTO) ------------
ESC_I_CONT = 6.0     # A continu, fiche HobbyKing
ESC_I_PIC  = 10.0    # A en pointe (donnee de la V3 BLHeli_S, la V2 ne la publie pas)
ESC_ERPM   = 240000  # tr/min electriques, "240 000 rpm pour un moteur 2 poles"
ESC_LVC    = 3.00    # V/cellule, coupure basse tension BLHeli par defaut

# --- turbine sur son propre pack 2S LiPo -----------------------------------
V_LIPO_NOM = 7.4     # V nominal
V_LIPO_MAX = 8.4     # V pleine charge
POLE_PAIRS = 3       # 9 bobines / 6 aimants, releve sur le moteur
RPM_REF_84 = 64200.0 # tr/min publies a 8,4 V pour la version 10000 KV

# --- implantation ----------------------------------------------------------
VOIE      = 0.155    # m, largeur hors-tout sur roues — elargie le 31/08 pour
                     # passer la turbine entre les codeurs (levre 36,7 + jeu)
Y_ENC_IN  = 0.0268   # m, le moteur+codeur depasse de 26,8 mm vers l'interieur
Y_WHEEL_O = 0.0305   # m, face externe de roue depuis l'origine de l'equerre
BR_DEMI_X = 0.0120   # m, demi-longueur de l'equerre dans l'axe du robot
X_PATIN   = 0.140    # m, patin avant sous la rangee de capteurs (d = 140 mm)

CD_FUITE = 0.60      # coefficient de decharge du jeu de jupe
CD_AERO  = 0.80      # trainee de forme du robot
A_FRONT  = 0.0036    # m2, maitre-couple estime 120 x 30 mm
R_PACK   = 0.040     # ohm, resistance interne du pack 2S
CHI      = 0.93      # part de l'appui sur les roues : plenum 100x110 decale de
                     # +10 mm (paroi arriere a -45) pour raccourcir la queue

A_DUCT   = math.pi / 4 * (D_VEINE**2 - D_MOYEU**2)
A_TROU   = math.pi / 4 * 0.0284**2     # decoupe de carte, outil DecoupeAir


# ==========================================================================
# Modele du ventilateur
# ==========================================================================

def ventilateur(v_bus):
    """Courbe du ventilateur ramenee a la tension de bus, par les lois de similitude.

    N ~ V, donc Q ~ V, Dp ~ V^2, P ~ V^3, poussee ~ V^2.
    Retourne (Q0, Dp0, poussee, courant, puissance) : Q0 = debit a Dp nul,
    Dp0 = depression a debit nul.
    """
    r = v_bus / V_REF
    v_ej = math.sqrt(T_REF / (RHO * A_DUCT))     # vitesse d'ejection a 8,4 V
    q_ref = A_DUCT * v_ej
    dp_ref = K_SHUTOFF * 0.5 * RHO * v_ej**2
    return (q_ref * r, dp_ref * r**2, T_REF * r**2, I_REF * r**2,
            V_REF * I_REF * r**3)


def point_de_fonctionnement(dp0, q0, perimetre, jeu):
    """Intersection de la courbe ventilateur et de la fuite sous la jupe.

    Ventilateur : Dp = Dp0 * (1 - (Q/Q0)^2)
    Fuite       : Q  = Cd * L * h * sqrt(2*Dp/rho)   =  C * sqrt(Dp)
    -> solution analytique  Dp = Dp0 / (1 + Dp0*C^2/Q0^2)
    """
    c = CD_FUITE * perimetre * jeu * math.sqrt(2.0 / RHO)
    dp = dp0 / (1.0 + dp0 * c * c / (q0 * q0))
    q = c * math.sqrt(dp)
    return dp, q


def jeu_pour_appui(dp0, q0, aire_plenum, perimetre, f_cible):
    """Jeu de jupe qui donne exactement f_cible, par dichotomie."""
    lo, hi = 0.05e-3, 20e-3
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        dp, q = point_de_fonctionnement(dp0, q0, perimetre, mid)
        if sum(appui(dp, q, aire_plenum)) > f_cible:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def appui(dp, q, aire_plenum):
    """Appui total = depression sur le fond + reaction du jet d'echappement."""
    f_depression = dp * (aire_plenum - A_TROU)
    v_ej = q / A_DUCT
    f_jet = RHO * q * v_ej
    return f_depression, f_jet


# ==========================================================================
# Dynamique
# ==========================================================================

def mu_charge(n):
    """Coefficient d'adherence corrige de la sensibilite a la charge."""
    if MU_EXP == 0.0:
        return MU
    return MU * (n / (M * G)) ** (-MU_EXP)


def charges(f_appui):
    """Repartition de la charge verticale entre l'essieu moteur et le patin.

    Le poids se repartit selon REPART_ESSIEU, l'appui selon CHI (position du
    centre de surface de la jupe par rapport a l'essieu).
    """
    n_essieu = REPART_ESSIEU * M * G + CHI * f_appui
    n_patin = (1.0 - REPART_ESSIEU) * M * G + (1.0 - CHI) * f_appui
    return n_essieu, n_patin


def f_lateral_max(f_appui):
    """Effort lateral disponible. Le patin frotte, mais dix fois moins bien."""
    n_essieu, n_patin = charges(f_appui)
    return mu_charge(n_essieu) * n_essieu + MU_PATIN * n_patin


def v_courbe(f_appui, rayon=R_VIRAGE):
    """Vitesse maximale en courbe, limitee par l'adherence."""
    return math.sqrt(f_lateral_max(f_appui) * rayon / M)


def f_requis(v, rayon=R_VIRAGE):
    """Appui necessaire pour tenir v dans un rayon donne, par dichotomie."""
    lo, hi = 0.0, 200.0
    if v_courbe(0.0) >= v:
        return 0.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if v_courbe(mid) < v:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def traction_moteurs():
    """Force longitudinale disponible aux deux roues, limitee par le courant."""
    couple_roue = KM * I_MAX * RED * ETA_RED
    return 2.0 * couple_roue / R_ROUE


def i_moteur(v, v_bus_eff):
    """Courant par moteur a la vitesse v, plafonne par la limite du codeur."""
    omega_mot = v / R_ROUE * RED
    i_dispo = (v_bus_eff - KM * omega_mot) / R_MOT
    return max(0.0, min(I_MAX, i_dispo))


def f_traction(v, v_bus_eff):
    return 2.0 * KM * i_moteur(v, v_bus_eff) * RED * ETA_RED / R_ROUE


def f_frein(v, v_bus_eff):
    """Freinage moteur : le courant vient de la force contre-electromotrice."""
    omega_mot = v / R_ROUE * RED
    i = max(0.0, min(I_MAX, KM * omega_mot / R_MOT))
    return 2.0 * KM * i * RED * ETA_RED / R_ROUE


def f_resistance(v, f_appui):
    return CRR * (M * G + f_appui) + 0.5 * RHO * CD_AERO * A_FRONT * v * v


def v_max_ligne_droite(f_appui, v_bus_eff):
    v = 0.1
    for _ in range(4000):
        net = f_traction(v, v_bus_eff) - f_resistance(v, f_appui)
        if net <= 0:
            return v
        v += 0.005
    return v


def temps_segment(longueur, f_appui, v_bus_eff, arc=0.314):
    """Ligne droite de `longueur`, encadree par deux virages pris a v_courbe.

    Profil avant (acceleration) et profil arriere (freinage) calcules au pas de
    1 mm, on garde le minimum des deux. Chaque acceleration est bornee par
    l'adherence disponible.
    """
    vc = v_courbe(f_appui)
    n_essieu, _ = charges(f_appui)
    a_grip = mu_charge(n_essieu) * n_essieu / M
    n = int(longueur * 1000)
    dx = longueur / n

    avant = [0.0] * (n + 1)
    avant[0] = vc
    for i in range(n):
        v = avant[i]
        a = (f_traction(v, v_bus_eff) - f_resistance(v, f_appui)) / M
        a = min(a, a_grip)
        avant[i + 1] = math.sqrt(max(1e-6, v * v + 2 * a * dx))

    arriere = [0.0] * (n + 1)
    arriere[n] = vc
    for i in range(n, 0, -1):
        v = arriere[i]
        d = (f_frein(v, v_bus_eff) + f_resistance(v, f_appui)) / M
        d = min(d, a_grip)
        arriere[i - 1] = math.sqrt(max(1e-6, v * v + 2 * d * dx))

    profil = [min(a, b) for a, b in zip(avant, arriere)]
    t = sum(dx / (0.5 * (profil[i] + profil[i + 1])) for i in range(n))
    return t + arc / vc, max(profil), vc


def n_essieu_admissible(f_radial):
    """Charge verticale maximale sur l'essieu moteur, imposee par les paliers.

    En courbe au taquet la roue voit sa charge verticale N et un effort lateral
    mu*N : le palier encaisse la resultante N*sqrt(1+mu^2).
    """
    return 2.0 * f_radial / math.sqrt(1.0 + MU * MU)


def appui_admissible(f_radial, chi):
    """Appui total correspondant, une fois le poids statique deduit."""
    reste = n_essieu_admissible(f_radial) - REPART_ESSIEU * M * G
    return max(0.0, reste / chi)


def courbe_depuis_poussee(t_ref_g, v_ref, d_veine, d_moyeu, n_unites=1):
    """Courbe (Q0, Dp0) a 6,4 V deduite de la poussee statique publiee.

    Pour un ventilateur carene : T = rho*A*ve^2, d'ou
        Dp dynamique a debit libre = T / (2A)      -> Dp0 = K_SHUTOFF * T/(2A)
        Q0 = A*ve = sqrt(T*A/rho)
    Deux unites identiques doublent T et A : Dp0 inchange, Q0 double.
    """
    a = n_unites * math.pi / 4 * (d_veine**2 - d_moyeu**2)
    t = n_unites * t_ref_g * 1e-3 * G
    r = V_BUS / v_ref
    dp0 = K_SHUTOFF * t / (2 * a) * r**2
    q0 = math.sqrt(t * a / RHO) * r
    return q0, dp0


# ==========================================================================
# Sortie
# ==========================================================================

def titre(t):
    print("\n" + t)
    print("-" * len(t))


def main():
    global K_SHUTOFF, MU, CHI, MU_EXP

    q0_84, dp0_84, t_84, i_84, p_84 = ventilateur(V_REF)
    q0, dp0, t_bus, i_bus, p_bus = ventilateur(V_BUS)
    v_ej = math.sqrt(T_REF / (RHO * A_DUCT))

    titre("A. Le robot et ce qu'on lui demande")
    print("masse avec turbine, ESC et pack renforce  %6.0f g" % (M * 1000))
    print("adherence retenue                         mu = %.2f" % MU)
    print("rayon minimal du reglement                %6.0f mm" % (R_VIRAGE * 1000))
    print("repartition statique                      %.0f %% essieu / %.0f %% patin"
          % (100 * REPART_ESSIEU, 100 * (1 - REPART_ESSIEU)))
    print("vitesse en courbe sans appui              %6.2f m/s" % v_courbe(0.0))
    print()
    print("  appui necessaire pour tenir la courbe :")
    for v in (1.5, 2.0, 2.5, 3.0):
        f = f_requis(v)
        print("    %.1f m/s  ->  %6.2f N  (%4.0f g, soit %.1f fois le poids)"
              % (v, f, f / G * 1000, f / (M * G)))

    titre("B. Ce que sait faire la turbine, ramene au bus 6,4 V")
    print("section d'ejection                        %6.1f mm2" % (A_DUCT * 1e6))
    print("vitesse d'ejection a 8,4 V                %6.1f m/s" % v_ej)
    print("lois de similitude 6,4/8,4 = %.3f  ->  Q x%.3f, Dp x%.3f, P x%.3f"
          % (V_BUS / V_REF, V_BUS / V_REF, (V_BUS / V_REF)**2, (V_BUS / V_REF)**3))
    print()
    print("                              8,4 V      6,4 V")
    print("debit a contre-pression nulle %6.1f     %6.1f L/s" % (q0_84 * 1000, q0 * 1000))
    print("depression a debit nul        %6.0f     %6.0f Pa"
          % (dp0_84, dp0))
    print("                              %6.0f     %6.0f mm de colonne d'eau"
          % (dp0_84 / 9.81, dp0 / 9.81))
    print("poussee statique              %6.0f     %6.0f g"
          % (t_84 / G * 1000, t_bus / G * 1000))
    print("courant                       %6.1f     %6.1f A" % (i_84, i_bus))
    print("puissance electrique          %6.0f     %6.0f W" % (p_84, p_bus))

    titre("C. Option 1 : poussee directe (la turbine souffle vers le bas)")
    print("appui obtenu       %.2f N = %.0f g" % (t_bus, t_bus / G * 1000))
    print("vitesse en courbe  %.2f m/s  (contre %.2f sans turbine, soit +%.0f %%)"
          % (v_courbe(t_bus), v_courbe(0.0),
             100 * (v_courbe(t_bus) / v_courbe(0.0) - 1)))
    print("verdict : %.0f g pour 41 W et 6,4 A. Le gain ne paie pas le pack."
          % (t_bus / G * 1000))

    titre("D. Option 2 : depression sous jupe — point de fonctionnement")
    print("La turbine aspire le plenum et refoule au-dessus de la carte.")
    print("Fuite modelisee par un jeu constant sur tout le perimetre, Cd = %.2f.\n"
          % CD_FUITE)
    plenums = [("90 x 90", 0.090, 0.090), ("100 x 110", 0.100, 0.110),
               ("110 x 130", 0.110, 0.130)]
    jeux = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0]
    print("            jeu de jupe : " + "".join("%8.1f" % j for j in jeux) + "  mm")
    for nom, a, b in plenums:
        aire = a * b
        perim = 2 * (a + b)
        ligne_f, ligne_v = [], []
        for j in jeux:
            dp, q = point_de_fonctionnement(dp0, q0, perim, j * 1e-3)
            fd, fj = appui(dp, q, aire)
            ligne_f.append(fd + fj)
            ligne_v.append(v_courbe(fd + fj))
        print("  %-10s appui N " % nom + "".join("%8.2f" % f for f in ligne_f))
        print("  %-10s v m/s   " % "" + "".join("%8.2f" % v for v in ligne_v))
    print("\n(rappel : %.2f m/s en courbe sans appui)" % v_courbe(0.0))

    titre("D bis. Detail du plenum retenu 100 x 110 mm")
    aire, perim = 0.100 * 0.110, 2 * (0.100 + 0.110)
    print("  jeu    Dp      Q      Q/Q0   appui plenum  reaction jet   total")
    for j in (0.5, 1.0, 1.5, 2.0, 3.0, 5.0):
        dp, q = point_de_fonctionnement(dp0, q0, perim, j * 1e-3)
        fd, fj = appui(dp, q, aire)
        print("  %.1f mm %5.0f Pa %5.1f L/s %5.0f %%  %8.2f N    %8.2f N   %6.2f N"
              % (j, dp, q * 1000, 100 * q / q0, fd, fj, fd + fj))
    print("\nLa reaction du jet est un bonus de quelques pour cent :")
    print("l'appui vient de la depression, donc du joint, pas de la poussee.")

    titre("E. Ce qui limite vraiment — traction contre adherence")
    f_mot = traction_moteurs()
    print("couple roue a %.1f A            %.2f mNm" % (I_MAX, KM * I_MAX * RED * ETA_RED * 1e3))
    print("force de traction, 2 roues     %.2f N" % f_mot)
    print("acceleration disponible        %.2f m/s2" % (f_mot / M))
    print()
    print("  appui   limite adherence   limite moteurs   ce qui commande")
    for f in (0.0, 1.0, 2.0, 4.0, 8.0):
        n_e, _ = charges(f)
        a_adh = mu_charge(n_e) * n_e / M
        a_mot = f_mot / M
        qui = "moteurs" if a_mot < a_adh else "adherence"
        print("  %4.1f N  %8.2f m/s2      %8.2f m/s2      %s" % (f, a_adh, a_mot, qui))
    print("\nEn ligne droite le couple plafonne avant l'adherence, meme sans appui :")
    print("l'appui n'achete pas d'acceleration, il n'achete que du virage.")
    print()
    print("Cout en roulement (Crr = %.2f) :" % CRR)
    for f in (0.0, 2.0, 4.0, 8.0):
        rr = CRR * (M * G + f)
        print("  appui %4.1f N -> resistance %.3f N, soit %.0f %% de la traction"
              % (f, rr, 100 * rr / f_mot))

    titre("F. Budget electrique")
    i_tot = i_bus + 2 * I_MAX
    print("turbine plein regime           %.1f A" % i_bus)
    print("deux moteurs a la limite       %.1f A" % (2 * I_MAX))
    print("total                          %.1f A" % i_tot)
    print("pack 1000 mAh                  %.1f C  (15 C annonce : OK)" % i_tot)
    print("chute sur 40 mOhm de pack      %.2f V  (bus %.2f V)"
          % (i_tot * 0.040, V_BUS - i_tot * 0.040))
    for t in (20, 30, 45):
        print("tour de %2d s, turbine a fond   %.0f mAh, soit %.0f %% du pack"
              % (t, i_bus * t / 3.6, 100 * i_bus * t / 3600 / 1.0))

    titre("G. Sensibilite aux hypotheses (plenum 100 x 110, jeu 2 mm)")
    ref_k, ref_mu, ref_chi, ref_exp = K_SHUTOFF, MU, CHI, MU_EXP
    for label, setk, setmu, setchi, setexp in [
            ("reference", 1.6, 0.90, 1.00, 0.00),
            ("courbe pessimiste  K=1,2", 1.2, 0.90, 1.00, 0.00),
            ("courbe optimiste   K=2,2", 2.2, 0.90, 1.00, 0.00),
            ("bache glissante    mu=0,7", 1.6, 0.70, 1.00, 0.00),
            ("bache accrocheuse  mu=1,1", 1.6, 1.10, 1.00, 0.00),
            ("plenum en avant    chi=0,7", 1.6, 0.90, 0.70, 0.00),
            ("sensibilite charge exp=0,1", 1.6, 0.90, 1.00, 0.10)]:
        K_SHUTOFF, MU, CHI, MU_EXP = setk, setmu, setchi, setexp
        _, dp0_s, _, _, _ = ventilateur(V_BUS)
        q0_s = ventilateur(V_BUS)[0]
        dp, q = point_de_fonctionnement(dp0_s, q0_s, perim, 2e-3)
        fd, fj = appui(dp, q, aire)
        print("  %-28s appui %5.2f N   v courbe %.2f m/s"
              % (label, fd + fj, v_courbe(fd + fj)))
    K_SHUTOFF, MU, CHI, MU_EXP = ref_k, ref_mu, ref_chi, ref_exp

    titre("H. Est-ce que l'appui paie ? — segment ligne droite 6 m + un virage")
    print("Le gain en virage se paie en roulement sur la ligne droite, et la")
    print("consommation de la turbine fait chuter le bus qui alimente les moteurs.")
    print("Simulation au pas de 1 mm, freinage moteur par force contre-electromotrice.\n")
    print("  config                 bus    v courbe  v pointe  temps   ecart")
    ref = None
    for label, f_app, i_turb in [
            ("turbine coupee", 0.0, 0.0),
            ("jupe 3 mm", 2.48, i_bus),
            ("jupe 2 mm", 4.04, i_bus),
            ("jupe 1,5 mm", 5.44, i_bus),
            ("jupe 1 mm", 7.42, i_bus),
            ("jupe 0,5 mm", 9.65, i_bus)]:
        v_eff = V_BUS - (i_turb + 2 * I_MAX) * R_PACK
        t, vmax, vc = temps_segment(6.0, f_app, v_eff)
        if ref is None:
            ref = t
        print("  %-20s %5.2f V   %5.2f    %6.2f   %6.3f s  %+6.3f s"
              % (label, v_eff, vc, vmax, t, t - ref))
    print()
    print("Vitesse de pointe atteignable en ligne droite libre :")
    for label, f_app, i_turb in [("sans appui", 0.0, 0.0), ("appui 4 N", 4.04, i_bus)]:
        v_eff = V_BUS - (i_turb + 2 * I_MAX) * R_PACK
        print("  %-12s %.2f m/s" % (label, v_max_ligne_droite(f_app, v_eff)))

    titre("K. Quelle taille de turbine — et la limite qui arrive avant")
    f_adm = appui_admissible(F_RADIAL_ROUE, 0.75)
    f_adm_k = appui_admissible(F_RADIAL_K, 0.75)
    print("Avant de comparer les turbines : ce que la chaine de traction accepte.")
    print("La roue est en porte-a-faux de 8,5 mm sur l'arbre du reducteur, et le")
    print("reducteur monte est celui a paliers frittes.\n")
    print("  charge radiale admise par roue      %.2f N" % F_RADIAL_ROUE)
    print("  en courbe la resultante vaut N*sqrt(1+mu2) = %.3f * N" % math.sqrt(1 + MU * MU))
    print("  charge verticale max par roue       %.2f N" % (F_RADIAL_ROUE / math.sqrt(1 + MU * MU)))
    print("  moins le poids deja porte (%.0f %%)    %.2f N" % (100 * REPART_ESSIEU, REPART_ESSIEU * M * G))
    print("  APPUI MAXIMAL ADMISSIBLE            %.2f N   (chi = 0,75)" % f_adm)
    print("  la meme chose avec le reducteur K   %.1f N  (roulements, 30 N)" % f_adm_k)
    print()
    print("Le 27 mm produit deja %.2f N a 2 mm de jeu : la butee n'est pas la turbine."
          % 4.04)
    print("Jeu de jupe qui ramene l'appui sous la limite frittee :")
    for j in (2.0, 2.5, 3.0, 3.5, 4.0):
        dp_j, q_j = point_de_fonctionnement(dp0, q0, perim, j * 1e-3)
        f_j = sum(appui(dp_j, q_j, aire))
        print("  %.1f mm -> %.2f N %s" % (j, f_j, "OK" if f_j <= f_adm else "au-dessus"))

    print()
    print("Comparaison des turbines, ramenees a 6,4 V par leur poussee publiee :")
    print("(plenum 100 x 110 mm, jeu 2 mm — Dp0 = K*T/2A, Q0 = sqrt(T*A/rho))\n")
    print("  %-26s %6s %6s %7s %7s %7s" % ("", "Q0", "Dp0", "Dp", "appui", "v courbe"))
    print("  %-26s %6s %6s %7s %7s %7s" % ("", "L/s", "Pa", "Pa", "N", "m/s"))
    candidats = [
        ("EDF 27 M1204-14500KV 2S", 104.0, 8.4, 0.0274, 0.0130, 1),
        ("EDF 30 MC1306-10600KV 2S", 191.0, 8.4, 0.0300, 0.0142, 1),
        ("2 x EDF 27", 104.0, 8.4, 0.0274, 0.0130, 2),
        ("2 x EDF 30", 191.0, 8.4, 0.0300, 0.0142, 2),
    ]
    for nom, t_g, v_r, dv, dm, n in candidats:
        q0_c, dp0_c = courbe_depuis_poussee(t_g, v_r, dv, dm, n)
        dp_c, q_c = point_de_fonctionnement(dp0_c, q0_c, perim, 2e-3)
        f_c = sum(appui(dp_c, q_c, aire))
        print("  %-26s %6.1f %6.0f %7.0f %7.2f %7.2f%s"
              % (nom, q0_c * 1000, dp0_c, dp_c, f_c, v_courbe(min(f_c, f_adm)),
                 "" if f_c <= f_adm else "  (bride par les paliers)"))
    print()
    print("Au-dessus de 30 mm la gamme est bobinee pour 3S/4S : a 6,4 V elle perd")
    print("de la vitesse peripherique, donc de la pression. Ne pas extrapoler —")
    print("il faut une poussee publiee a 2S, sinon le calcul ci-dessus ne vaut rien.")

    titre("L. Ou la mettre")
    jeu_moteurs = VOIE - 2 * (Y_WHEEL_O + Y_ENC_IN)
    d_levre = 0.0367
    voie_mini = 2 * (Y_WHEEL_O + Y_ENC_IN) + d_levre + 2 * 0.002
    print("Les deux moteurs sont couches sur la ligne d'essieu, culasses face a face.")
    print("  voie hors-tout retenue (fig. 2)     %.0f mm" % (VOIE * 1000))
    print("  chaque ensemble rentre de           %.1f mm vers l'interieur" % (Y_ENC_IN * 1000))
    print("  espace libre entre les deux         %.1f mm" % (jeu_moteurs * 1000))
    print("  diametre du fut / de la levre       %.1f / %.1f mm" % (29.7, d_levre * 1000))
    print("  -> ENTRE LES MOTEURS : %s" % ("possible" if jeu_moteurs > d_levre else "impossible en l'etat"))
    print("     il faudrait elargir la voie a    %.0f mm (reglement : 200 mm)" % (voie_mini * 1000))
    print()
    x_turbine = BR_DEMI_X + d_levre / 2 + 0.002
    print("Devant les moteurs, sur l'axe median :")
    print("  l'equerre occupe                    X +/- %.0f mm autour de l'essieu" % (BR_DEMI_X * 1000))
    print("  centre de turbine au plus pres      X = %.0f mm en avant de l'essieu" % (x_turbine * 1000))
    print("  decoupe air Ø28,4 -> X de %.0f a %.0f mm : degage l'equerre"
          % ((x_turbine - 0.0142) * 1000, (x_turbine + 0.0142) * 1000))
    print("  hauteur : turbine 25,8 mm contre 22,45 mm de haut de berceau,")
    print("  elle depasse de 3,35 mm — refoulement libre au-dessus a prevoir.")
    print()
    print("Ce que la position de la turbine change a l'appui : RIEN.")
    print("L'appui est porte par le centre de surface de la JUPE, pas par la turbine.")
    ref_chi = CHI
    print("  %-34s %5s %8s %9s" % ("", "chi", "appui a", "v courbe"))
    print("  %-34s %5s %8s %9s" % ("", "", "la butee", ""))
    for label, xcp in [("centre de jupe sur l'essieu", 0.0),
                       ("centre de jupe a 20 mm en avant", 0.020),
                       ("centre de jupe a 30 mm en avant", 0.030),
                       ("centre de jupe a 45 mm en avant", 0.045)]:
        CHI = (X_PATIN - xcp) / X_PATIN
        f_max = appui_admissible(F_RADIAL_ROUE, CHI)
        print("  %-34s %5.2f %6.2f N %7.2f m/s" % (label, CHI, f_max, v_courbe(f_max)))
    CHI = ref_chi
    print("  Une jupe avancee laisse mettre plus d'appui total pour la meme charge")
    print("  de palier, mais il part dans le patin : le gain est marginal.")
    print("  (patin avant suppose a %.0f mm de l'essieu ; le reculer degrade tout)" % (X_PATIN * 1000))

    titre("M. Le variateur Turnigy Multistar 6A V2 BLHeli tient-il ?")
    print("Fiche : %.0f A continu, %.0f A pointe, 2-3S LiPo, OPTO sans BEC," % (ESC_I_CONT, ESC_I_PIC))
    print("21 x 11 mm, 2 g, PWM moteur 8 kHz, %d tr/min electriques.\n" % ESC_ERPM)

    f_adm_m = appui_admissible(F_RADIAL_ROUE, CHI)
    s_util = math.sqrt(min(1.0, f_adm_m / 4.04))
    print("1. COURANT — l'appui varie comme le carre du regime, la puissance comme le cube.")
    print("   %-22s %7s %8s %9s %8s" % ("consigne", "appui", "I batt", "I phase", "verdict"))
    for frac in (1.00, 0.90, 0.80, 0.70, 0.60):
        i_bat = i_bus * frac**3
        i_ph = i_bat / frac
        f_f = 4.04 * frac**2
        etat = "OK" if i_ph <= ESC_I_CONT else "au-dessus du continu"
        print("   %-22s %6.2f N %6.1f A %7.1f A   %s"
              % ("%.0f %% du regime" % (100 * frac), f_f, i_bat, i_ph, etat))
    print("   Les paliers frittes imposent %.2f N, soit %.0f %% du regime : %.1f A batterie,"
          % (f_adm_m, 100 * s_util, i_bus * s_util**3))
    print("   %.1f A de phase. On passe — mais a pleine consigne on est a %.1f A, dessus."
          % (i_bus * s_util**3 / s_util, i_bus))

    print("\n2. TENSION — c'est la vraie incompatibilite, et elle se corrige au logiciel.")
    v_sag = V_BUS - (i_bus + 2 * I_MAX) * R_PACK
    print("   Le BLHeli compte les cellules a la mise sous tension. A %.1f V (LiFePO4" % 7.3)
    print("   pleine charge) il conclut 2S LiPo et arme sa coupure a %.1f V." % (2 * ESC_LVC))
    print("   Or le bus tombe a %.2f V turbine + moteurs a fond, et la doc donne 5,0 V" % v_sag)
    print("   pack vide. La coupure se declenche EN COURSE.")
    print("   -> passer 'Low voltage protection' sur OFF dans BLHeliSuite. Obligatoire.")
    print("   -> il faut un linker USB pour ESC, ou le passthrough d'un FC. A prevoir.")

    print("\n3. FREQUENCE DE COMMUTATION — a verifier, on ne connait pas le nombre de poles.")
    rpm_84 = 64200.0
    rpm_bus = rpm_84 * V_BUS / V_REF
    print("   Regime turbine a %.1f V : environ %.0f tr/min." % (V_BUS, rpm_bus))
    print("   %-16s %12s %s" % ("paires de poles", "tr/min elec", "verdict"))
    for pp in (1, 3, 7):
        erpm = rpm_bus * pp
        print("   %-16d %12.0f %s" % (pp, erpm, "OK" if erpm <= ESC_ERPM else "HORS LIMITE"))
    print("   Compter les aimants du rotor : nb aimants / 2 = paires de poles.")
    print("   Un 1204 de drone classique est en 14 aimants — ce serait redhibitoire.")
    print("   A %d KV il est presque surement en 2 poles, mais ca se verifie a l'oeil." % 14500)

    print("\n4. CE QU'ON PERD — le BLHeli d'origine (Atmel/SiLabs) ne fait PAS de DShot.")
    print("   Consigne servo 1-2 ms sur TIM4 CH3, et surtout aucune remontee de regime :")
    print("   le decrochage de turbine annonce au §4 de la doc n'est pas detectable.")
    print("   Un Multistar 6A V3 'BLHeli_S Rev16', meme boitier et meme prix, le ferait.")

    titre("N. Turbine sur son propre pack 2S LiPo")
    print("Le moteur est un 9 bobines / 6 aimants, soit %d paires de poles." % POLE_PAIRS)
    print("La turbine sort du bus LiFePO4 et prend un pack a elle, 7,4 a 8,4 V.\n")

    print("1. FREQUENCE DE COMMUTATION — la question de la section M est tranchee.")
    print("   %-30s %9s %11s %s" % ("", "tr/min", "tr/min elec", ""))
    for lab, v, kv_rpm in [("7,4 V, version 10000 KV", V_LIPO_NOM, RPM_REF_84 * V_LIPO_NOM / V_LIPO_MAX),
                           ("8,4 V, version 10000 KV", V_LIPO_MAX, RPM_REF_84),
                           ("7,4 V, version 14500 KV", V_LIPO_NOM, RPM_REF_84 * 1.45 * V_LIPO_NOM / V_LIPO_MAX),
                           ("8,4 V, version 14500 KV", V_LIPO_MAX, RPM_REF_84 * 1.45)]:
        erpm = kv_rpm * POLE_PAIRS
        marge = 100 * (1 - erpm / ESC_ERPM)
        print("   %-30s %9.0f %11.0f  %s"
              % (lab, kv_rpm, erpm,
                 "OK, %.0f %% de marge" % marge if erpm <= ESC_ERPM else "HORS LIMITE"))
    print("   -> avec la version 10000 KV ca passe. Avec la 14500 KV, non : verifier")
    print("      le KV imprime sur le moteur avant de mettre pleine consigne.")

    print("\n2. COUPURE BASSE TENSION — le probleme disparait.")
    print("   Sur LiPo le BLHeli detecte 2S et coupe a %.1f V, ce qui est exactement" % (2 * ESC_LVC))
    print("   la protection voulue pour du LiPo. Plus rien a reprogrammer.")

    print("\n3. COURANT — c'est la contrainte qui reste, et elle se durcit.")
    print("   %-14s %8s %8s %8s %9s" % ("tension", "I pleine", "appui", "consigne", "I a cette"))
    print("   %-14s %8s %8s %8s %9s" % ("", "consigne", "jupe 2mm", "utile", "consigne"))
    f_adm_n = appui_admissible(F_RADIAL_ROUE, CHI)
    for v_t, i_pub in [(V_BUS, None), (V_LIPO_NOM, 9.6), (V_LIPO_MAX, 11.0)]:
        q0_t, dp0_t, _, i_t, _ = ventilateur(v_t)
        if i_pub is not None:
            i_t = i_pub
        dp_t, q_t = point_de_fonctionnement(dp0_t, q0_t, perim, 2e-3)
        f_t = sum(appui(dp_t, q_t, aire))
        frac = math.sqrt(min(1.0, f_adm_n / f_t))
        print("   %-14s %6.1f A %6.2f N %7.0f %% %7.1f A"
              % ("%.1f V" % v_t, i_t, f_t, 100 * frac, i_t * frac**3))
    print("   L'ESC tient %.0f A en continu : a pleine consigne on est tres au-dessus," % ESC_I_CONT)
    print("   mais a la consigne que les paliers autorisent on reste sous %.0f A." % ESC_I_CONT)
    print("   Brider la consigne DANS LE FIRMWARE avant le premier demarrage.")

    print("\n4. LE VRAI BENEFICE — une jupe beaucoup plus tolerante.")
    print("   Pour les %.2f N que les paliers acceptent, jeu de jupe possible :" % f_adm_n)
    for lab, v_t in [("bus LiFePO4 6,4 V", V_BUS), ("LiPo 7,4 V", V_LIPO_NOM),
                     ("LiPo 8,4 V", V_LIPO_MAX)]:
        q0_t, dp0_t, _, _, _ = ventilateur(v_t)
        j = jeu_pour_appui(dp0_t, q0_t, aire, perim, f_adm_n)
        print("   %-20s %.2f mm" % (lab, j * 1000))
    print("   Passer de %.2f a %.2f mm de jeu, c'est la difference entre une jupe qui"
          % (jeu_pour_appui(*ventilateur(V_BUS)[:2][::-1], aire, perim, f_adm_n) * 1000,
             jeu_pour_appui(*ventilateur(V_LIPO_MAX)[:2][::-1], aire, perim, f_adm_n) * 1000))
    print("   talonne sur les ondulations de la bache et une jupe qui les ignore.")
    q0_h, dp0_h, _, _, _ = ventilateur(V_LIPO_MAX)
    print("   Attention : un 'jeu' egal a la garde au sol (%.0f mm) veut dire un rebord" % (CLEAR * 1000))
    print("   de hauteur nulle, donc pas de plenum du tout — resultat sans objet. Ce qui")
    print("   compte est la HAUTEUR DU REBORD qu'il faut descendre sous la carte :")
    print("   %-12s %6s %9s %10s %9s" % ("rebord", "jeu", "appui max", "consigne", "I a cette"))
    print("   %-12s %6s %9s %10s %9s" % ("", "", "a fond", "utile", "consigne"))
    for h_rebord in (1.0, 2.0, 3.0, 3.5):
        jeu = CLEAR * 1000 - h_rebord
        dp_h, q_h = point_de_fonctionnement(dp0_h, q0_h, perim, jeu * 1e-3)
        f_h = sum(appui(dp_h, q_h, aire))
        frac = math.sqrt(min(1.0, f_adm_n / f_h))
        print("   %-12s %4.1f mm %7.2f N %8.0f %% %7.1f A"
              % ("%.1f mm" % h_rebord, jeu, f_h, 100 * frac, 11.0 * frac**3))
    print("   Un rebord RIGIDE de 2 mm suffit : il s'arrete a %.0f mm du sol, laisse"
          % (CLEAR * 1000 - 2.0))
    print("   3 mm de jeu, et donne deja le double de ce que les paliers acceptent.")
    print("   Une jupe souple descendant a 2 mm de jeu demanderait 3 mm et talonnerait.")
    frac_f = math.sqrt(min(1.0, f_adm_n / sum(appui(*point_de_fonctionnement(dp0_h, q0_h, perim, 3e-3), aire))))
    print("\n   Corollaire sur la commutation : bride a %.0f %% de consigne, le moteur"
          % (100 * frac_f))
    print("   ne monte qu'a %.0f tr/min electriques meme en version 14500 KV : la marge"
          % (RPM_REF_84 * 1.45 * POLE_PAIRS * frac_f))
    print("   ESC ne devient un probleme que si quelqu'un met plein gaz au banc.")

    print("\n5. CE QUE LE PACK SEPARE REND AU RESTE DE LA CARTE.")
    print("   bus moteurs sans la turbine   %.2f V au lieu de %.2f V"
          % (V_BUS - 2 * I_MAX * R_PACK, V_BUS - (i_bus + 2 * I_MAX) * R_PACK))
    print("   le pack LiFePO4 n'a plus a encaisser 6 a 11 A : les 1000 mAh / 15 C")
    print("   du paragraphe 5 de la doc redeviennent surdimensionnes.")
    print("   MAIS : masse d'un 2S LiPo 450 mAh ~ 28 g, et surtout LES DEUX MASSES")
    print("   DOIVENT ETRE RELIEES — le signal de consigne n'a pas de reference sinon.")

    titre("O. Calibre du variateur — sur ce que le moteur PEUT appeler")
    print("Regle : un ESC se dimensionne sur le courant maximal que le moteur peut")
    print("tirer, pas sur la consigne qu'on compte utiliser. Une limite tenue par le")
    print("firmware n'est pas une limite : un parametre mal remis, un essai au banc,")
    print("un demarrage rate, et l'ESC voit le courant plein.\n")

    print("1. Le courant ne baisse PAS quand on met la turbine sur le plenum.")
    q0_o, dp0_o, _, _, _ = ventilateur(V_LIPO_MAX)
    i_libre = 11.0
    p_elec_libre = i_libre * V_LIPO_MAX
    v_ej_o = math.sqrt((0.104 * G) / (RHO * A_DUCT))
    q_libre = A_DUCT * v_ej_o
    p_air_libre = 0.5 * RHO * v_ej_o**2 * q_libre
    eta = p_air_libre / p_elec_libre
    print("   debit libre   Q %.1f L/s, Dp total %4.0f Pa -> %.1f W d'air pour %.0f W"
          % (q_libre * 1000, 0.5 * RHO * v_ej_o**2, p_air_libre, p_elec_libre))
    print("   rendement global de l'ensemble        %.0f %%" % (100 * eta))
    print()
    print("   %-16s %7s %8s %9s %9s %8s" % ("jeu de rebord", "Dp stat", "Q", "Dp total", "P air", "I estime"))
    for j in (2.0, 3.0, 4.0, 5.0):
        dp_o, q_o = point_de_fonctionnement(dp0_o, q0_o, perim, j * 1e-3)
        v_d = q_o / A_DUCT
        dp_tot = dp_o + 0.5 * RHO * v_d * v_d
        p_air = dp_tot * q_o
        print("   %-16s %5.0f Pa %5.1f L/s %6.0f Pa %6.1f W %6.1f A"
              % ("%.0f mm" % j, dp_o, q_o * 1000, dp_tot, p_air, p_air / eta / V_LIPO_MAX))
    print("   La contre-pression du plenum ne soulage pas le moteur : ce qu'il perd en")
    print("   debit, il le regagne en pression. On reste autour de %.0f A." % i_libre)

    print("\n2. Le BLHeli d'origine n'a AUCUNE mesure de courant.")
    print("   Pas de capteur, donc pas de limitation ni de coupure sur surintensite.")
    print("   Un blocage de rotor — debris, contact du rebord, pale ebrechee — n'est")
    print("   arrete par rien. C'est le MOSFET qui sert de fusible.")

    print("\n3. Verdict par calibre, sur les %.0f A de la vraie utilisation :" % i_libre)
    for nom, i_cont, note in [("Multistar 6A V2", 6.0, "celui en main"),
                              ("Multistar 10A V2 LBEC", 10.0, "envisage"),
                              ("Multistar 20A V2 slim", 20.0, "62 x 13 mm, opto"),
                              ("Multistar 20A BLHeli_S V3", 20.0, "opto, DShot")]:
        marge = 100 * (i_cont / i_libre - 1)
        etat = "SOUS-DIMENSIONNE" if i_cont < i_libre else "OK, +%.0f %% de marge" % marge
        print("   %-28s %4.0f A  %-20s %s" % (nom, i_cont, note, etat))
    print("   Le fabricant de la turbine annonce d'ailleurs 15 A minimum.")

    print("\n4. La broche du BEC.")
    print("   Les versions LBEC mettent 5 V sur le fil central du connecteur servo, et")
    print("   la carte y attend du rien (embase marquee NC au paragraphe 8). Prendre")
    print("   une version OPTO, ou couper le fil central AU RAS DE L'ESC — pas")
    print("   simplement le laisser dans le connecteur.")

    titre("I. Les trois mesures qui remplacent ces hypotheses")
    dp_test, _ = point_de_fonctionnement(dp0, q0, perim, 2e-3)
    print("1. Depression a debit nul : turbine sur une boite etanche, manometre")
    print("   en U a l'eau. Attendu %.0f mm de colonne. C'est K_SHUTOFF." % (dp0 / 9.81))
    print("2. Appui reel : robot complet sur une balance de cuisine, turbine a fond,")
    print("   sur un morceau de la vraie bache. Attendu %.0f g au jeu de 2 mm."
          % ((appui(*point_de_fonctionnement(dp0, q0, perim, 2e-3), aire)[0]
              + appui(*point_de_fonctionnement(dp0, q0, perim, 2e-3), aire)[1])
             / G * 1000))
    print("3. Adherence : tirer le robot au dynamometre, turbine coupee puis a fond.")
    print("   Le rapport des deux forces donne mu et verifie la mesure 2.")

    titre("J. Ce qui sort de tout ca")
    dp2, q2 = point_de_fonctionnement(dp0, q0, perim, 2e-3)
    f2 = sum(appui(dp2, q2, aire))
    print("Plenum 100 x 110 mm centre sur l'essieu, jupe reglee a 2 mm :")
    print("  depression %4.0f Pa, debit %.1f L/s, appui %.2f N (%.0f g)"
          % (dp2, q2 * 1000, f2, f2 / G * 1000))
    t_off, _, _ = temps_segment(6.0, 0.0, V_BUS - 2 * I_MAX * R_PACK)
    t_on, vmax_on, _ = temps_segment(6.0, f2, V_BUS - (i_bus + 2 * I_MAX) * R_PACK)
    print("  virage a %.2f m/s au lieu de %.2f, segment 6 m + virage gagne %.2f s"
          % (v_courbe(f2), v_courbe(0.0), t_off - t_on))
    f_adm_j = appui_admissible(F_RADIAL_ROUE, CHI)
    print("  MAIS les paliers frittes du reducteur plafonnent a %.2f N : jupe a 3 mm"
          % f_adm_j)
    print("  et %.2f N reels, soit %.2f m/s en courbe et %.2f s de gain."
          % (2.48, v_courbe(2.48), t_off - temps_segment(6.0, 2.48, V_BUS - (i_bus + 2 * I_MAX) * R_PACK)[0]))
    print()
    print("Trois consequences de conception :")
    print("  1. La poussee directe est hors sujet : 60 g. C'est le joint de jupe")
    print("     qui fait l'appui, pas la turbine. Le jeu est le seul vrai levier.")
    print("  2. Sous 1,5 mm de jeu le gain sature et le risque de talonner explose")
    print("     sur une bache qui ondule : 2 mm est le point de conception.")
    print("  3. La turbine reste allumee en permanence. La couper en ligne droite")
    print("     ne rend que %.2f m/s de pointe sur un troncon ou le robot plafonne"
          % (v_max_ligne_droite(0.0, 6.32) - v_max_ligne_droite(f2, 6.06)))
    print("     de toute facon a %.2f m/s, et il faut la reamorcer avant le virage."
          % vmax_on)
    print("  4. Le vrai plafond n'est pas la turbine mais le reducteur a paliers")
    print("     frittes. Passer a la version K a roulements deverrouille %.0f N"
          % appui_admissible(F_RADIAL_K, CHI))
    print("     d'appui admissible, et c'est seulement la que monter en 30 mm sert.")


main()
