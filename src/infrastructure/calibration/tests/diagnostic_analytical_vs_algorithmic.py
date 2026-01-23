"""
Script de diagnostic pour comparer prédictions théoriques vs résultats algorithmiques.
"""

import sys
import numpy as np
from scipy.spatial.transform import Rotation as R
from datetime import datetime

# Ajouter src au path
sys.path.insert(0, 'src')

from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from infrastructure.calibration.scipy_sensor_frame_calibration_optimizer import (
    ScipySensorFrameCalibrationOptimizer
)

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_analytical_prediction():
    """Test avec prédiction analytique exacte."""
    print_section("TEST 1: Prédiction Analytique - Cas Simple")
    
    optimizer = ScipySensorFrameCalibrationOptimizer()
    
    # Angles connus (simples pour vérification)
    theta_x, theta_y, theta_z = 0.0, 30.0, 45.0  # degrés
    known_angles = np.array([theta_x, theta_y, theta_z])
    
    print(f"\nAngles theoriques: theta_x={theta_x}deg, theta_y={theta_y}deg, theta_z={theta_z}deg")
    
    E_0 = 10.0
    
    # Use 'XYZ' extrinsic rotations (matching TransformationService)
    rotation = R.from_euler('XYZ', known_angles, degrees=True)
    
    # For X_DIR excitation: E_bench = [E_0, 0, 0]
    # With 'XYZ' extrinsic: E_probe = R^-1 * E_bench
    v_bench_x = np.array([E_0, 0.0, 0.0])
    v_probe_x = rotation.inv().apply(v_bench_x)  # Analytically compute E_probe
    
    print(f"\nVecteur E_probe (X_DIR) calculé analytiquement avec 'XYZ' extrinsèque:")
    print(f"  v_probe_x = {v_probe_x}")
    
    # Vérification: E_bench = R * E_probe (rotation directe)
    v_transformed = rotation.apply(v_probe_x)  # Transform probe -> bench
    
    print(f"\nVecteur transformé R * v_probe_x (devrait être [E_0, 0, 0]):")
    print(f"  v_transformed = {v_transformed}")
    print(f"  Attendu: [{E_0}, 0, 0]")
    print(f"  Erreur: {np.abs(v_transformed - np.array([E_0, 0.0, 0.0]))}")
    
    # Créer la mesure
    x_measurement = VoltageMeasurement(
        voltage_x_in_phase=v_probe_x[0],
        voltage_x_quadrature=0.0,
        voltage_y_in_phase=v_probe_x[1],
        voltage_y_quadrature=0.0,
        voltage_z_in_phase=v_probe_x[2],
        voltage_z_quadrature=0.0,
        timestamp=datetime.now()
    )
    
    # Calculer les résidus avec les bons angles
    residuals = optimizer._residual_function(known_angles, [x_measurement], [])
    
    print(f"\nRésidus calculés (devraient être [0, 0]):")
    print(f"  residuals = {residuals}")
    print(f"  Erreur: {np.abs(residuals)}")

def test_rotation_consistency():
    """Test de cohérence de la rotation."""
    print_section("TEST 2: Cohérence Rotation Inverse/Directe")
    
    theta_x, theta_y, theta_z = 10.0, 15.0, 20.0
    angles = np.array([theta_x, theta_y, theta_z])
    rotation = R.from_euler('XYZ', angles, degrees=True)
    
    E_0 = 10.0
    v_bench_x = np.array([E_0, 0.0, 0.0])
    
    print(f"\nVecteur dans repère banc: v_bench = {v_bench_x}")
    
    # Transformation banc -> capteur
    v_probe = rotation.inv().apply(v_bench_x)
    print(f"Vecteur dans repère capteur (R_inv * v_bench): v_probe = {v_probe}")
    
    # Transformation capteur -> banc
    v_bench_recovered = rotation.apply(v_probe)
    print(f"Vecteur retour banc (R * v_probe): v_bench_recovered = {v_bench_recovered}")
    print(f"Erreur de reconstruction: {np.abs(v_bench_recovered - v_bench_x)}")
    
    # Maintenant testons avec notre fonction de résidu
    optimizer = ScipySensorFrameCalibrationOptimizer()
    x_measurement = VoltageMeasurement(
        voltage_x_in_phase=v_probe[0],
        voltage_x_quadrature=0.0,
        voltage_y_in_phase=v_probe[1],
        voltage_y_quadrature=0.0,
        voltage_z_in_phase=v_probe[2],
        voltage_z_quadrature=0.0,
        timestamp=datetime.now()
    )
    
    residuals = optimizer._residual_function(angles, [x_measurement], [])
    print(f"\nRésidus avec angles corrects: {residuals}")
    print(f"  (devraient être [0, 0] car Y et Z composantes de v_bench_recovered sont 0)")

def test_optimization_convergence():
    """Test de convergence de l'optimisation."""
    print_section("TEST 3: Convergence Optimisation")
    
    optimizer = ScipySensorFrameCalibrationOptimizer()
    
    # Known rotation angles (in degrees)
    known_angles = (10.0, 15.0, 20.0)
    theta_x, theta_y, theta_z = known_angles
    
    E_0 = 10.0
    
    # Create rotation using 'XYZ' extrinsic convention (matching TransformationService)
    rotation = R.from_euler('XYZ', known_angles, degrees=True)
    
    # For X_DIR excitation: E_bench = [E_0, 0, 0]
    # With 'XYZ' extrinsic: E_probe = R^-1 * E_bench
    v_bench_x = np.array([E_0, 0.0, 0.0])
    v_probe_x = rotation.inv().apply(v_bench_x)
    
    x_measurement = VoltageMeasurement(
        voltage_x_in_phase=v_probe_x[0],
        voltage_x_quadrature=0.0,
        voltage_y_in_phase=v_probe_x[1],
        voltage_y_quadrature=0.0,
        voltage_z_in_phase=v_probe_x[2],
        voltage_z_quadrature=0.0,
        timestamp=datetime.now()
    )
    
    # For Y_DIR excitation: E_bench = [0, E_0, 0]
    v_bench_y = np.array([0.0, E_0, 0.0])
    v_probe_y = rotation.inv().apply(v_bench_y)
    
    y_measurement = VoltageMeasurement(
        voltage_x_in_phase=v_probe_y[0],
        voltage_x_quadrature=0.0,
        voltage_y_in_phase=v_probe_y[1],
        voltage_y_quadrature=0.0,
        voltage_z_in_phase=v_probe_y[2],
        voltage_z_quadrature=0.0,
        timestamp=datetime.now()
    )
    
    print(f"\nAngles théoriques: {known_angles}")
    print(f"Vecteurs E_probe calculés analytiquement avec 'XYZ' extrinsèque:")
    print(f"  X_DIR: {v_probe_x}")
    print(f"  Y_DIR: {v_probe_y}")
    
    # Optimiser
    print(f"\nOptimisation en cours...")
    try:
        optimized = optimizer.optimize_angles(
            [x_measurement],
            [y_measurement],
            initial_angles=(0.0, 0.0, 0.0)
        )
        
        print(f"\nAngles optimisés: {optimized}")
        print(f"Angles théoriques: {known_angles}")
        print(f"Différence: {np.array(optimized) - np.array(known_angles)}")
        
        # Vérifier les résidus finaux
        residuals = optimizer._residual_function(
            np.array(optimized),
            [x_measurement],
            [y_measurement]
        )
        print(f"\nRésidus finaux: {residuals}")
        print(f"Norme des résidus: {np.linalg.norm(residuals)}")
        
    except Exception as e:
        print(f"ERREUR lors de l'optimisation: {e}")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  DIAGNOSTIC: Comparaison Prédictions Théoriques vs Algorithmiques")
    print("="*60)
    
    test_analytical_prediction()
    test_rotation_consistency()
    test_optimization_convergence()
    
    print("\n" + "="*60)
    print("  FIN DU DIAGNOSTIC")
    print("="*60 + "\n")
