"""
Visualisation de la reconstruction DGP des 4 spheres : schema a l'echelle
+ ecart au carre parfait.

Les 4 spheres sont mesurees comme placees aux coins d'un carre : S1<->S2 et
S3<->S4 sont les deux diagonales, {S1,S3,S2,S4} (dans cet ordre) trace le
perimetre. Le "carre parfait le mieux ajuste" est calcule par decomposition
harmonique (DFT a 4 points) : la composante de frequence 1 est la partie du
quadrilatere qui a une symetrie de rotation d'ordre 4 (= un carre), le reste
est l'ecart. Voir fit_square() ci-dessous.

Usage : uv run python external_modules/source_geometry/visualize_square_deviation.py
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

from source_geometry.source_geometry import SourceGeometry
from source_geometry.source_frame_solver import SourceFrameSolver

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config_templates" / "aefi_device_config.json"

# S1,S3,S2,S4 traces the square perimeter (S1<->S2 and S3<->S4 are the diagonals)
PERIMETER_ORDER = (0, 2, 1, 3)


def load_geometry(config_path) -> tuple[SourceGeometry, dict]:
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    sg = config["excitation"]["sources_geometry"]
    labels = sg["sphere_labels"]
    diam = sg["sphere_diameters"]
    dist = sg["pairwise_distances_ext"]
    geometry = SourceGeometry(
        D_12=dist["D_S1_S2"]["value"], D_13=dist["D_S1_S3"]["value"], D_14=dist["D_S1_S4"]["value"],
        D_23=dist["D_S2_S3"]["value"], D_24=dist["D_S2_S4"]["value"], D_34=dist["D_S3_S4"]["value"],
        phi_1=diam["S1"]["value"], phi_2=diam["S2"]["value"],
        phi_3=diam["S3"]["value"], phi_4=diam["S4"]["value"],
    )
    return geometry, labels


def to_physical_frame(result):
    """Centroid-centered, quadrant-aligned frame for display.

    SourceFrameSolver anchors S1 at the origin and S2 on the x axis — an
    arbitrary computational convenience, not a meaningful frame to plot in
    (S1 always sits on the axis regardless of which quadrant it's actually
    in). This instead puts the origin at the spheres' centroid, with +x/+y
    pointing through the side midpoints (right-left, top-bottom) rather than
    through the diagonal corners, so each sphere lands in the quadrant its
    label promises (S1=x_neg_y_pos ends up at x<0,y>0, etc).

    A true rigid rotation (Gram-Schmidt orthogonalized from the two
    independently-derived side-bisector directions, which are only
    approximately orthogonal on real, imperfectly-square data) — so
    distances and fit_square's residuals are unchanged, only the viewing
    frame is. Checked numerically: residual norms match the solver-frame
    computation exactly once orthogonalized; without it they were inflated
    by the same ~1.4deg defect fit_square separately reports.
    """
    P = [np.array(p[:2]) for p in result.positions]  # S1..S4
    centroid = sum(P) / 4
    top_mid, bottom_mid = (P[0] + P[2]) / 2, (P[1] + P[3]) / 2  # S1S3 / S2S4
    left_mid, right_mid = (P[0] + P[3]) / 2, (P[2] + P[1]) / 2  # S1S4 / S3S2

    phys_x = _normalize(right_mid - left_mid)
    phys_y_raw = top_mid - bottom_mid
    phys_y = _normalize(phys_y_raw - np.dot(phys_y_raw, phys_x) * phys_x)  # Gram-Schmidt

    def project(p):
        rel = p - centroid
        return (float(np.dot(rel, phys_x)), float(np.dot(rel, phys_y)))

    return [project(p) for p in P]


def _normalize(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)


def fit_square(corners_xy):
    """Best-fit perfect square (least squares) through 4 points given in
    perimeter order, via a 4-point DFT: the harmonic matching the corners'
    own winding direction is the unique rotationally-symmetric-by-90deg
    square that minimizes the sum of squared corner errors; the rest is the
    deviation from that square. Returns (center, side_length,
    orientation_deg, ideal_corners, residuals) — residuals are actual-ideal,
    same units as corners_xy.

    S1,S3,S2,S4 (our PERIMETER_ORDER) winds *clockwise* in the solver's
    (x,y) frame — checked numerically, not assumed — so the square generator
    is w=-i (each next corner is the previous one rotated -90deg), and
    z0 = mean(zc[k] * i^{+k}) is the projection onto that harmonic (the
    conjugate-w convention). Using the CCW convention (w=+i) here silently
    picks up the near-zero harmonic instead and produces nonsense (checked:
    ~1mm "side length" and ~45mm "residuals" on real device data).
    """
    z = [complex(x, y) for x, y in corners_xy]
    center = sum(z) / 4
    zc = [zk - center for zk in z]
    z0 = sum(zk * (1j) ** k for k, zk in enumerate(zc)) / 4
    ideal = [center + z0 * (1j) ** (-k) for k in range(4)]
    residuals = [zk - iz for zk, iz in zip(zc, [i - center for i in ideal])]
    side_length = abs(z0) * math.sqrt(2)
    orientation_deg = math.degrees(math.atan2(z0.imag, z0.real)) - 45
    ideal_xy = [(c.real, c.imag) for c in ideal]
    residual_xy = [(r.real, r.imag) for r in residuals]
    return (center.real, center.imag), side_length, orientation_deg, ideal_xy, residual_xy


def print_report(geometry: SourceGeometry, result) -> None:
    mm = 1000
    print("--- Grandeurs mesurees (pied a coulisse) ---")
    for pair in ("12", "13", "14", "23", "24", "34"):
        D = getattr(geometry, f"D_{pair}") * mm
        d = getattr(geometry, f"d_{pair}") * mm
        print(f"  D_{pair} = {D:7.3f} mm (extremite-a-extremite)  ->  d_{pair} = {d:7.3f} mm (centre-a-centre)")

    print("\n--- Residu du round-trip DGP (distance reconstruite vs mesuree) ---")
    pairs = {"12": (0, 1), "13": (0, 2), "14": (0, 3), "23": (1, 2), "24": (1, 3), "34": (2, 3)}
    for name, (i, j) in pairs.items():
        expected = getattr(geometry, f"d_{name}")
        actual = math.dist(result.positions[i], result.positions[j])
        print(f"  d_{name}: attendu={expected*mm:7.3f}mm  reconstruit={actual*mm:7.3f}mm  residu={(actual-expected)*1e6:+.1f} um")

    physical = to_physical_frame(result)  # S1..S4, quadrant-aligned, centroid at origin
    print("\n--- Positions reconstruites (repere physique : origine = centroide, S_i dans son cadrant) ---")
    for i, (x, y) in enumerate(physical, start=1):
        print(f"  S{i}: x={x*mm:+8.3f}mm  y={y*mm:+8.3f}mm")

    corners = [physical[i] for i in PERIMETER_ORDER]  # S1,S3,S2,S4, (x,y)
    center, side, angle, ideal, residual = fit_square(corners)
    rms_um = math.sqrt(sum(rx**2 + ry**2 for rx, ry in residual) / 4) * 1e6
    max_um = max(math.hypot(rx, ry) for rx, ry in residual) * 1e6
    print("\n--- Ecart au carre parfait (meilleur ajustement, moindres carres) ---")
    print(f"  cote du carre ajuste = {side*mm:.3f} mm, orientation = {angle:.2f} deg")
    print(f"  ecart RMS = {rms_um:.1f} um, ecart max = {max_um:.1f} um")
    for label, (rx, ry) in zip(("S1", "S3", "S2", "S4"), residual):
        print(f"  {label}: ecart = ({rx*1e6:+.1f}, {ry*1e6:+.1f}) um, norme = {math.hypot(rx,ry)*1e6:.1f} um")


def plot_geometry(geometry: SourceGeometry, result, labels: dict) -> None:
    mm = 1000
    fig, ax = plt.subplots(figsize=(7, 7))

    physical = to_physical_frame(result)  # S1..S4, quadrant-aligned, centroid at origin
    radii = [geometry.r_1, geometry.r_2, geometry.r_3, geometry.r_4]
    for i, ((x, y), r) in enumerate(zip(physical, radii), start=1):
        x, y = x * mm, y * mm
        ax.add_patch(Circle((x, y), r * mm, fill=False, edgecolor="C0", linewidth=1.5, zorder=3))
        ax.plot(x, y, "o", color="C0", zorder=3)
        ax.annotate(f"S{i} ({labels.get(f'S{i}', '?')})", (x, y), textcoords="offset points", xytext=(8, 8), zorder=3)

    # quadrant boundaries through the centroid (origin)
    ax.axhline(0, color="0.85", linewidth=1, zorder=1)
    ax.axvline(0, color="0.85", linewidth=1, zorder=1)
    ax.plot(0, 0, "+", color="black", zorder=3)

    # actual quadrilateral (solid) vs best-fit perfect square (dashed)
    corners = [physical[i] for i in PERIMETER_ORDER]
    center, side, angle, ideal, residual = fit_square(corners)
    actual_loop = [(x*mm, y*mm) for x, y in corners] + [(corners[0][0]*mm, corners[0][1]*mm)]
    ideal_loop = [(x*mm, y*mm) for x, y in ideal] + [(ideal[0][0]*mm, ideal[0][1]*mm)]
    ax.plot(*zip(*actual_loop), "-", color="C0", label="quadrilatere reconstruit")
    ax.plot(*zip(*ideal_loop), "--", color="gray", label=f"carre ajuste ({side*mm:.2f}mm)")

    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    rms_um = math.sqrt(sum(rx**2 + ry**2 for rx, ry in residual) / 4) * 1e6
    ax.set_title(f"Positions reconstruites des 4 spheres (DGP) — ecart RMS au carre : {rms_um:.1f} um")
    ax.set_aspect("equal")
    ax.grid(True, linestyle=":")
    ax.legend(loc="upper right", fontsize=8)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    geometry, labels = load_geometry(CONFIG_PATH)
    result = SourceFrameSolver.solve(geometry)
    print_report(geometry, result)
    plot_geometry(geometry, result, labels)
