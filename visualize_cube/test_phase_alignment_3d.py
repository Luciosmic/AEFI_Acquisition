"""
Test visuel de l'alignement de phase via visualisation 3D.

Ce script teste le module SignalPostProcessor en visualisant des vecteurs (I, Q)
avant et après rotation de phase dans un cube 3D.
"""

import sys
import os
from pathlib import Path

# Ajouter le chemin src pour les imports
# Le script est dans visualize_cube/, donc parent = AEFI_Acquisition/
project_root = Path(__file__).parent.parent
src_dir = project_root / "AEFI_Acquisition" / "src"
if not src_dir.exists():
    # Essayer un autre chemin possible
    src_dir = project_root / "src"
if src_dir.exists():
    sys.path.insert(0, str(src_dir))
    print(f"[DEBUG] Added to path: {src_dir}")
else:
    print(f"[ERREUR] Cannot find src directory. Tried: {project_root / 'AEFI_Acquisition' / 'src'} and {project_root / 'src'}")
    sys.exit(1)

try:
    import pyvista as pv
    import numpy as np
except ImportError as e:
    print(f"ERREUR: Module manquant: {e}")
    print("\nPour installer les dépendances, exécutez:")
    print("  pip install pyvista numpy")
    print("\nOu depuis le dossier visualize_cube:")
    print("  pip install -r requirements.txt")
    sys.exit(1)

import math
from interface.presenters.signal_processor import SignalPostProcessor

def create_test_vectors():
    """
    Crée des vecteurs de test à différents angles pour tester la rotation de phase.
    
    Returns:
        List of (I, Q, angle_deg, label) tuples
    """
    vectors = []
    
    # Vecteur de référence à 45° pour la calibration
    vectors.append((1.0, 1.0, 45.0, "Ref (45°)"))
    
    # Vecteurs de test à différents angles
    angles_deg = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
    for angle_deg in angles_deg:
        angle_rad = math.radians(angle_deg)
        # Créer un vecteur unitaire à cet angle
        i = math.cos(angle_rad)
        q = math.sin(angle_rad)
        vectors.append((i, q, angle_deg, f"{angle_deg}°"))
    
    return vectors

def visualize_phase_alignment():
    """
    Visualise l'alignement de phase dans un cube 3D.
    """
    # Créer le processeur de signal
    processor = SignalPostProcessor()
    
    # Créer des vecteurs de test
    test_vectors = create_test_vectors()
    
    # 1. Calibrer la phase avec le vecteur de référence (45°)
    ref_vector = test_vectors[0]  # (1, 1, 45°, "Ref")
    ref_sample = {
        "Ux In-Phase": ref_vector[0],
        "Ux Quadrature": ref_vector[1],
        "Uy In-Phase": 0.0,
        "Uy Quadrature": 0.0,
        "Uz In-Phase": 0.0,
        "Uz Quadrature": 0.0,
    }
    processor.calibrate_phase(ref_sample)
    print(f"Phase calibrée avec vecteur de référence: (I={ref_vector[0]}, Q={ref_vector[1]}) à {ref_vector[2]}°")
    
    # 2. Créer le plotter PyVista
    plotter = pv.Plotter()
    plotter.set_background('white')
    
    # 3. Créer un cube pour le contexte
    cube = pv.Cube(x_length=3, y_length=3, z_length=3, center=(0, 0, 0))
    plotter.add_mesh(cube, color='lightgray', style='wireframe', 
                    line_width=1, opacity=0.3)
    
    # 4. Visualiser les vecteurs AVANT rotation (plan I-Q)
    print("\n=== Vecteurs AVANT rotation ===")
    origin = np.array([0, 0, 0])
    
    for i, (i_val, q_val, angle_deg, label) in enumerate(test_vectors):
        # Positionner les vecteurs dans l'espace 3D
        # On les place sur un cercle dans le plan I-Q (z=0)
        radius = 1.5
        x_pos = radius * math.cos(math.radians(angle_deg))
        y_pos = radius * math.sin(math.radians(angle_deg))
        z_pos = 0.0
        
        start_point = np.array([x_pos, y_pos, z_pos])
        
        # Direction du vecteur (I, Q) dans le plan
        # On projette (I, Q) sur le plan XY
        vector_2d = np.array([i_val, q_val, 0])
        vector_norm = np.linalg.norm(vector_2d)
        if vector_norm > 0:
            vector_2d = vector_2d / vector_norm * 0.3  # Normaliser et réduire
        else:
            vector_2d = np.array([0, 0, 0])
        
        end_point = start_point + vector_2d
        
        # Ajouter la flèche AVANT rotation (en rouge)
        plotter.add_arrows(
            start_point.reshape(1, -1),
            vector_2d.reshape(1, -1),
            mag=1.0,
            color='red',
            opacity=0.7
        )
        
        # Ajouter un point à l'origine du vecteur
        plotter.add_mesh(
            pv.Sphere(radius=0.05, center=start_point),
            color='red',
            opacity=0.8
        )
        
        print(f"  {label}: (I={i_val:.3f}, Q={q_val:.3f})")
    
    # 5. Visualiser les vecteurs APRÈS rotation
    print("\n=== Vecteurs APRÈS rotation ===")
    
    for i, (i_val, q_val, angle_deg, label) in enumerate(test_vectors):
        # Traiter le vecteur avec le processeur
        sample = {
            "Ux In-Phase": i_val,
            "Ux Quadrature": q_val,
            "Uy In-Phase": 0.0,
            "Uy Quadrature": 0.0,
            "Uz In-Phase": 0.0,
            "Uz Quadrature": 0.0,
        }
        
        processed = processor.process_sample(sample)
        i_new = processed["Ux In-Phase"]
        q_new = processed["Ux Quadrature"]
        
        # Positionner les vecteurs transformés (décalés en Z)
        radius = 1.5
        x_pos = radius * math.cos(math.radians(angle_deg))
        y_pos = radius * math.sin(math.radians(angle_deg))
        z_pos = 1.5  # Décaler vers le haut pour voir la différence
        
        start_point = np.array([x_pos, y_pos, z_pos])
        
        # Direction du vecteur transformé
        vector_2d = np.array([i_new, q_new, 0])
        vector_norm = np.linalg.norm(vector_2d)
        if vector_norm > 0:
            vector_2d = vector_2d / vector_norm * 0.3
        else:
            vector_2d = np.array([0, 0, 0])
        
        end_point = start_point + vector_2d
        
        # Ajouter la flèche APRÈS rotation (en vert)
        plotter.add_arrows(
            start_point.reshape(1, -1),
            vector_2d.reshape(1, -1),
            mag=1.0,
            color='green',
            opacity=0.7
        )
        
        # Ajouter un point à l'origine du vecteur
        plotter.add_mesh(
            pv.Sphere(radius=0.05, center=start_point),
            color='green',
            opacity=0.8
        )
        
        # Calculer l'angle résultant
        angle_result_deg = math.degrees(math.atan2(q_new, i_new))
        print(f"  {label}: (I={i_new:.3f}, Q={q_new:.3f}) -> Angle: {angle_result_deg:.2f}°")
    
    # 6. Ajouter des axes et une grille
    plotter.add_axes(
        xlabel='I (In-Phase)',
        ylabel='Q (Quadrature)',
        zlabel='Z',
        line_width=5,
        labels_off=False
    )
    plotter.show_grid()
    
    # 7. Ajouter une légende
    plotter.add_text(
        "Rouge: Avant rotation | Vert: Après rotation",
        position='upper_left',
        font_size=12,
        color='black'
    )
    plotter.add_text(
        "Plan z=0: Avant | Plan z=1.5: Après",
        position='upper_right',
        font_size=12,
        color='black'
    )
    
    # 8. Ajouter un titre
    plotter.add_title("Test d'Alignement de Phase - Signal Processing", font_size=16)
    
    # 9. Définir une position de caméra
    plotter.camera_position = [(5, -5, 3), (0, 0, 0.75), (0, 0, 1)]
    
    # 10. Afficher
    print("\n=== Visualisation ===")
    print("Rouge: Vecteurs avant rotation")
    print("Vert: Vecteurs après rotation")
    print("Les vecteurs verts devraient être alignés sur l'axe I (Q≈0)")
    print("\nOuverture de la fenêtre 3D...")
    print("(Fermez la fenêtre pour terminer)")
    plotter.show()

if __name__ == "__main__":
    visualize_phase_alignment()

