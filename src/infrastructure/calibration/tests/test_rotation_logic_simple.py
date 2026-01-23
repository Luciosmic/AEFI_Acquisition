"""
Test simple pour vérifier la logique de rotation.
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
from scipy.spatial.transform import Rotation as R

def test_rotation_logic():
    """Test simple de la logique de rotation."""
    
    print("="*60)
    print("TEST: Logique de Rotation Simple")
    print("="*60)
    
    # Angles connus
    theta_x, theta_y, theta_z = 10.0, 15.0, 20.0
    angles = np.array([theta_x, theta_y, theta_z])
    rotation = R.from_euler('XYZ', angles, degrees=True)
    
    E_0 = 10.0
    
    # Test 1: Transformation bench -> probe
    print(f"\nTest 1: Transformation bench -> probe")
    v_bench = np.array([E_0, 0.0, 0.0])
    v_probe = rotation.inv().apply(v_bench)  # bench -> probe
    print(f"  v_bench = {v_bench}")
    print(f"  v_probe = R^-1 * v_bench = {v_probe}")
    
    # Test 2: Transformation probe -> bench (retour)
    print(f"\nTest 2: Transformation probe -> bench (retour)")
    v_bench_recovered = rotation.apply(v_probe)  # probe -> bench
    print(f"  v_bench_recovered = R * v_probe = {v_bench_recovered}")
    print(f"  Erreur: {np.abs(v_bench_recovered - v_bench)}")
    
    # Test 3: Vérifier que les composantes Y et Z sont zéro
    print(f"\nTest 3: Vérification composantes Y et Z")
    print(f"  Y component: {v_bench_recovered[1]} (devrait être 0)")
    print(f"  Z component: {v_bench_recovered[2]} (devrait être 0)")
    
    # Test 4: Avec la fonction de résidu
    print(f"\nTest 4: Simulation fonction de résidu")
    # La fonction de résidu fait: rotation.apply(v_probe) pour obtenir v_bench
    # Puis prend les composantes Y et Z
    v_bench_from_residual = rotation.apply(v_probe)
    residual_y = v_bench_from_residual[1]
    residual_z = v_bench_from_residual[2]
    print(f"  Residual Y: {residual_y} (devrait être 0)")
    print(f"  Residual Z: {residual_z} (devrait être 0)")

if __name__ == '__main__':
    test_rotation_logic()
