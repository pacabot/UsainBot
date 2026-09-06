# -*- coding: utf-8 -*-
"""
Roue et tension de bus : le couple (diametre, tension) est un rapport de boite.

Question posee le 01/09 : les machines qui gagnent ont des roues plus petites et
plus larges — peut-on suralimenter (2S LiPo au lieu de 2S LiFePO4) pour recuperer
la pointe et gagner du couple ?

Physique reprise de turbineEDF27_dimensionnement.py (memes constantes). Le point
central est la nature du moteur : 1524T006SR = 5,55 ohm au total et 1 A de plafond
(nappe IE2). Au demarrage le courant est deja limite a 1 A quel que soit le bus
(bloque : 6,4/5,55 = 1,15 A) — la surtension n'ajoute RIEN sous ~1 m/s. Ce qu'elle
fait : elle repousse la vitesse a laquelle la force d'appui moteur s'effondre
(I = (V - kE*w)/R), donc du couple en milieu de bande et de la pointe.

    python3 roue_tension_opt.py
"""

import math

RHO, G = 1.204, 9.81
M = 0.329            # kg, robot complet turbine comprise
MU, MU_PATIN = 0.90, 0.20
REP, CHI = 0.80, 0.93   # poids sur l'essieu ; part d'appui sur l'essieu (plenum +10)
CRR, CD, A_F = 0.05, 0.80, 0.0036
R_VIR = 0.200

KM = 5.99e-3         # Nm/A = V.s/rad
R_MOT = 5.55         # ohm, bobinage + nappe
I_MAX = 1.00         # A, plafond nappe IE2
RED, ETA = 3.33, 0.90
R_PACK = 0.040       # ohm
N_MAX_MOT = 13000.0  # tr/min, limite moteur
N_GEAR = 6000.0      # tr/min, entree reducteur en continu (depassement assume)

GARDE_MINI = 0.0117 + 0.003   # m : axe a 11,7 mm du dessous de carte (0 entretoise)
                              # + 3 mm d'optique -> rayon de roue minimal


def i_turbine(v_bus):
    return 11.0 * (v_bus / 8.4) ** 2


def appui_jupe2mm(v_bus_eff):
    """Depression sous jupe a 2 mm, loi en V^2 depuis 4,04 N a 6,4 V."""
    return 4.04 * (v_bus_eff / 6.4) ** 2


def f_lat(appui):
    return (MU * (REP * M * G + CHI * appui)
            + MU_PATIN * ((1 - REP) * M * G + (1 - CHI) * appui))


def v_courbe(appui):
    return math.sqrt(f_lat(appui) * R_VIR / M)


def f_traction(v, r, v_eff):
    om = v / r * RED
    i = max(0.0, min(I_MAX, (v_eff - KM * om) / R_MOT))
    return 2.0 * KM * i * RED * ETA / r


def f_frein(v, r, v_eff):
    om = v / r * RED
    i = max(0.0, min(I_MAX, KM * om / R_MOT))
    return 2.0 * KM * i * RED * ETA / r


def f_res(v, appui):
    return CRR * (M * G + appui) + 0.5 * RHO * CD * A_F * v * v


def temps_segment(longueur, appui, r, v_eff, arc=0.314):
    vc = v_courbe(appui)
    a_grip = MU * (REP * M * G + CHI * appui) / M
    n = int(longueur * 1000)
    dx = longueur / n
    avant = [vc] + [0.0] * n
    for i in range(n):
        a = min(a_grip, (f_traction(avant[i], r, v_eff) - f_res(avant[i], appui)) / M)
        avant[i + 1] = math.sqrt(max(1e-6, avant[i] ** 2 + 2 * a * dx))
    arriere = [0.0] * n + [vc]
    for i in range(n, 0, -1):
        d = min(a_grip, (f_frein(arriere[i], r, v_eff) + f_res(arriere[i], appui)) / M)
        arriere[i - 1] = math.sqrt(max(1e-6, arriere[i] ** 2 + 2 * d * dx))
    prof = [min(a, b) for a, b in zip(avant, arriere)]
    t = sum(dx / (0.5 * (prof[i] + prof[i + 1])) for i in range(n))
    return t + arc / vc, max(prof)


def main():
    print("Rayon minimal de roue (0 entretoise, 3 mm d'optique) : %.1f mm -> Ø >= %.0f mm"
          % (GARDE_MINI * 1000, 2000 * GARDE_MINI))
    print("Force aux roues a 1 A : 2*kM*I*red*eta/r — bloquee par le courant, pas la tension.")
    print()
    for nom_pack, v_bus in (("2S LiFePO4 (6,4 V)", 6.4), ("2S LiPo (7,4 V nom.)", 7.4)):
        v_eff = v_bus - (i_turbine(v_bus) + 2 * I_MAX) * R_PACK
        print("=== %s — bus effectif %.2f V, turbine %.1f A ===" % (nom_pack, v_eff, i_turbine(v_bus)))
        for nom_app, appui in (("paliers frittes, 2,1 N", 2.1),
                               ("15/10K, jupe 2 mm", appui_jupe2mm(v_eff))):
            vc = v_courbe(appui)
            print("  appui %-24s -> virage %.2f m/s" % ("%s (%.1f N)" % (nom_app, appui), vc))
            print("    Ø     F(0-1m/s)  F(2m/s)  pointe   n_mot@pointe   t segment 6m+virage")
            for d_mm in (32, 36, 40, 43):
                r = d_mm / 2000.0
                t, vmax = temps_segment(6.0, appui, r, v_eff)
                n_mot = vmax / r * RED * 60 / (2 * math.pi)
                flag = " !> n_max" if n_mot > N_MAX_MOT else (" (red. %d%%)" % (100 * n_mot / N_GEAR))
                f0 = 2 * KM * I_MAX * RED * ETA / r
                f2 = f_traction(2.0, r, v_eff)
                print("    %2d mm  %5.2f N   %5.2f N  %4.2f m/s  %6.0f tr/min%s  %6.3f s"
                      % (d_mm, f0, f2, vmax, n_mot, flag, t))
        print()


main()
