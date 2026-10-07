"""Largeurs IPC-2152, vias et chutes de tension de calculs.md. Lancer : python3 calc.py"""
import math

MIL = 0.0254  # mm

# Figure 5-2 d'IPC-2152 (3 oz, 0,070 in, air calme, sans plan), ajustement de L. Rozenblat
# (smps.us/pcb-calculator.html) sur les coefficients de J. Olson.
def ipc2152_area_sqmil(I, dT):
    return (117.555 * dT**-0.913 + 1.15) * I**(0.84 * dT**-0.108 + 1.159)

# Correcteurs d'Olson (HowTo2152, p. 5-9) : cuivre 1 oz, FR-4, carte de 0,062 in.
K_OLSON = 0.84 * 1.02 * 1.08

def width_mm(I, dT, t_um, plane=1.0):
    """Largeur (mm) et section (mil²) pour I ampères, échauffement dT, cuivre de t_um µm."""
    A = ipc2152_area_sqmil(I, dT) * K_OLSON * plane
    return A / (t_um / 25.4) * MIL, A

def ipc2221_width_mm(I, dT, t_um, k=0.048):
    A = (I / (k * dT**0.44))**(1 / 0.725)
    return A / (t_um / 25.4) * MIL

# Cuivre : IPC-TM-650 2.5.14A.
RHO20, ALPHA = 1.7241e-8, 0.00393

def r_mohm(L_mm, w_mm, t_um, T=40.0):
    rho = RHO20 * (1 + ALPHA * (T - 20))
    return rho * (L_mm * 1e-3) / (w_mm * 1e-3 * t_um * 1e-6) * 1e3

def via_area_sqmil(drill_mm=0.3, plating_um=18.0):
    t = plating_um / 1000
    return math.pi * t * (drill_mm - t) / MIL**2

def ipc2221_via_A(drill_mm=0.3, plating_um=18.0, dT=10):
    """Formule de via_current.cpp du fork (section pi * d * t, constante externe)."""
    A = math.pi * drill_mm * plating_um / 1000 / MIL**2
    return 0.048 * dT**0.44 * A**0.725

if __name__ == "__main__":
    print("I (A) | dT 10 : ext 1 oz, int 0,5 oz | dT 20 : ext, int | IPC-2221 ext 10 °C  (mm)")
    for I in [0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6.5, 10, 13]:
        e10, _ = width_mm(I, 10, 35); i10, _ = width_mm(I, 10, 15.2)
        e20, _ = width_mm(I, 20, 35); i20, _ = width_mm(I, 20, 15.2)
        print(f"{I:5} | {e10:6.2f} {i10:6.2f} | {e20:6.2f} {i20:6.2f} | {ipc2221_width_mm(I, 10, 35):6.2f}")
    print(f"via 0,3 mm / 18 µm : section {via_area_sqmil():.1f} mil², fork {ipc2221_via_A():.2f} A")
