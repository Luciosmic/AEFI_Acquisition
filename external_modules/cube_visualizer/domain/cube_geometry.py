"""
Canonical geometry of the AEFI sensor cube — Domain layer.

Naming conventions (body frame, cube half-side a = size / 2):

  Faces (6):   {x,y,z}_{pos,neg}
  Vertices (8): V_αβγ  with α,β,γ ∈ {P=+, N=−}
  Edges (12):  Eδ_σ₁σ₂  where δ is the parallel axis and σ₁,σ₂ are the signs
               of the two constant coordinates (y,z for δ=x; x,z for δ=y; x,y for δ=z)

See _docs/CUBE_GEOMETRY.md for the full reference with adjacency tables.
"""
import numpy as np


def vertex_positions(size: float = 1.0) -> dict[str, np.ndarray]:
    """8 vertices of the cube, keyed by canonical name V_αβγ."""
    a = size / 2.0
    return {
        'V_PPP': np.array([ a,  a,  a]),
        'V_PPN': np.array([ a,  a, -a]),
        'V_PNP': np.array([ a, -a,  a]),
        'V_PNN': np.array([ a, -a, -a]),
        'V_NPP': np.array([-a,  a,  a]),
        'V_NPN': np.array([-a,  a, -a]),
        'V_NNP': np.array([-a, -a,  a]),
        'V_NNN': np.array([-a, -a, -a]),
    }


def edge_midpoints(size: float = 1.0) -> dict[str, np.ndarray]:
    """Midpoints of the 12 edges, keyed by canonical name Eδ_σ₁σ₂."""
    a = size / 2.0
    return {
        # Parallel to x — constant (y, z)
        'Ex_PP': np.array([0.0,  a,  a]),
        'Ex_PN': np.array([0.0,  a, -a]),
        'Ex_NP': np.array([0.0, -a,  a]),
        'Ex_NN': np.array([0.0, -a, -a]),
        # Parallel to y — constant (x, z)
        'Ey_PP': np.array([ a, 0.0,  a]),
        'Ey_PN': np.array([ a, 0.0, -a]),
        'Ey_NP': np.array([-a, 0.0,  a]),
        'Ey_NN': np.array([-a, 0.0, -a]),
        # Parallel to z — constant (x, y)
        'Ez_PP': np.array([ a,  a, 0.0]),
        'Ez_PN': np.array([ a, -a, 0.0]),
        'Ez_NP': np.array([-a,  a, 0.0]),
        'Ez_NN': np.array([-a, -a, 0.0]),
    }


def face_centers(size: float = 1.0) -> dict[str, np.ndarray]:
    """Centers of the 6 faces, keyed by canonical name."""
    a = size / 2.0
    return {
        'x_pos': np.array([ a, 0.0, 0.0]),
        'x_neg': np.array([-a, 0.0, 0.0]),
        'y_pos': np.array([0.0,  a, 0.0]),
        'y_neg': np.array([0.0, -a, 0.0]),
        'z_pos': np.array([0.0, 0.0,  a]),
        'z_neg': np.array([0.0, 0.0, -a]),
    }


# ---- Adjacency tables (static, size-independent) ----

FACE_VERTICES: dict[str, list[str]] = {
    'x_pos': ['V_PPP', 'V_PPN', 'V_PNP', 'V_PNN'],
    'x_neg': ['V_NPP', 'V_NPN', 'V_NNP', 'V_NNN'],
    'y_pos': ['V_PPP', 'V_PPN', 'V_NPP', 'V_NPN'],
    'y_neg': ['V_PNP', 'V_PNN', 'V_NNP', 'V_NNN'],
    'z_pos': ['V_PPP', 'V_PNP', 'V_NPP', 'V_NNP'],
    'z_neg': ['V_PPN', 'V_PNN', 'V_NPN', 'V_NNN'],
}

FACE_EDGES: dict[str, list[str]] = {
    'x_pos': ['Ey_PP', 'Ey_PN', 'Ez_PP', 'Ez_PN'],
    'x_neg': ['Ey_NP', 'Ey_NN', 'Ez_NP', 'Ez_NN'],
    'y_pos': ['Ex_PP', 'Ex_PN', 'Ez_PP', 'Ez_NP'],
    'y_neg': ['Ex_NP', 'Ex_NN', 'Ez_PN', 'Ez_NN'],
    'z_pos': ['Ex_PP', 'Ex_NP', 'Ey_PP', 'Ey_NP'],
    'z_neg': ['Ex_PN', 'Ex_NN', 'Ey_PN', 'Ey_NN'],
}

EDGE_FACES: dict[str, list[str]] = {
    'Ex_PP': ['y_pos', 'z_pos'],
    'Ex_PN': ['y_pos', 'z_neg'],
    'Ex_NP': ['y_neg', 'z_pos'],
    'Ex_NN': ['y_neg', 'z_neg'],
    'Ey_PP': ['x_pos', 'z_pos'],
    'Ey_PN': ['x_pos', 'z_neg'],
    'Ey_NP': ['x_neg', 'z_pos'],
    'Ey_NN': ['x_neg', 'z_neg'],
    'Ez_PP': ['x_pos', 'y_pos'],
    'Ez_PN': ['x_pos', 'y_neg'],
    'Ez_NP': ['x_neg', 'y_pos'],
    'Ez_NN': ['x_neg', 'y_neg'],
}

VERTEX_FACES: dict[str, list[str]] = {
    'V_PPP': ['x_pos', 'y_pos', 'z_pos'],
    'V_PPN': ['x_pos', 'y_pos', 'z_neg'],
    'V_PNP': ['x_pos', 'y_neg', 'z_pos'],
    'V_PNN': ['x_pos', 'y_neg', 'z_neg'],
    'V_NPP': ['x_neg', 'y_pos', 'z_pos'],
    'V_NPN': ['x_neg', 'y_pos', 'z_neg'],
    'V_NNP': ['x_neg', 'y_neg', 'z_pos'],
    'V_NNN': ['x_neg', 'y_neg', 'z_neg'],
}
