"""
Test pour vérifier la convention de rotation (intrinsèque vs extrinsèque).
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
from scipy.spatial.transform import Rotation as R
import math

def test_rotation_conventions():
    """Test pour comprendre la différence entre XYZ et xyz."""
    
    theta_x, theta_y, theta_z = 10.0, 15.0, 20.0  # degrés
    
    print("="*60)
    print("TEST: Convention de Rotation")
    print("="*60)
    print(f"\nAngles: theta_x={theta_x}°, theta_y={theta_y}°, theta_z={theta_z}°")
    
    # Test avec 'XYZ' (extrinsèque - axes fixes)
    rotation_XYZ = R.from_euler('XYZ', [theta_x, theta_y, theta_z], degrees=True)
    
    # Test avec 'xyz' (intrinsèque - axes mobiles)
    rotation_xyz = R.from_euler('xyz', [theta_x, theta_y, theta_z], degrees=True)
    
    # Test avec 'ZYX' (extrinsèque - ordre inverse)
    rotation_ZYX = R.from_euler('ZYX', [theta_x, theta_y, theta_z], degrees=True)
    
    # Vecteur de test
    v_test = np.array([1.0, 0.0, 0.0])
    
    print(f"\nVecteur de test: {v_test}")
    
    v_XYZ = rotation_XYZ.apply(v_test)
    v_xyz = rotation_xyz.apply(v_test)
    v_ZYX = rotation_ZYX.apply(v_test)
    
    print(f"\nRésultats:")
    print(f"  'XYZ' (extrinsèque): {v_XYZ}")
    print(f"  'xyz' (intrinsèque): {v_xyz}")
    print(f"  'ZYX' (extrinsèque): {v_ZYX}")
    
    # Vérifier la composition manuelle
    print(f"\nComposition manuelle R_z * R_y * R_x:")
    tx = math.radians(theta_x)
    ty = math.radians(theta_y)
    tz = math.radians(theta_z)
    
    # Matrices de rotation individuelles
    Rx = np.array([
        [1, 0, 0],
        [0, math.cos(tx), -math.sin(tx)],
        [0, math.sin(tx), math.cos(tx)]
    ])
    
    Ry = np.array([
        [math.cos(ty), 0, math.sin(ty)],
        [0, 1, 0],
        [-math.sin(ty), 0, math.cos(ty)]
    ])
    
    Rz = np.array([
        [math.cos(tz), math.sin(tz), 0],
        [-math.sin(tz), math.cos(tz), 0],
        [0, 0, 1]
    ])
    
    # Composition R_z * R_y * R_x (de droite à gauche)
    R_composite = Rz @ Ry @ Rx
    v_manual = R_composite @ v_test
    
    print(f"  Résultat manuel: {v_manual}")
    print(f"  Correspond à 'XYZ'? {np.allclose(v_XYZ, v_manual, atol=1e-10)}")
    print(f"  Correspond à 'xyz'? {np.allclose(v_xyz, v_manual, atol=1e-10)}")
    print(f"  Correspond à 'ZYX'? {np.allclose(v_ZYX, v_manual, atol=1e-10)}")
    
    # Test inverse
    print(f"\nTest inverse (R^-1 * v):")
    v_inv_XYZ = rotation_XYZ.inv().apply(v_test)
    v_inv_xyz = rotation_xyz.inv().apply(v_test)
    v_inv_manual = np.linalg.inv(R_composite) @ v_test
    
    print(f"  'XYZ'.inv(): {v_inv_XYZ}")
    print(f"  'xyz'.inv(): {v_inv_xyz}")
    print(f"  Manuel (R^-1): {v_inv_manual}")
    print(f"  'XYZ'.inv() correspond à R^-1? {np.allclose(v_inv_XYZ, v_inv_manual, atol=1e-10)}")
    
    # Test avec la formule du document
    print(f"\nTest avec formule du document (X_DIR, theta_x=0):")
    theta_x_doc = 0.0
    theta_y_doc = 30.0
    theta_z_doc = 45.0
    
    ty_doc = math.radians(theta_y_doc)
    tz_doc = math.radians(theta_z_doc)
    E_0 = 10.0
    
    # Formule du document: E_probe = E_0 * [cos(θ_y)*cos(θ_z), cos(θ_y)*sin(θ_z), -sin(θ_y)]
    v_probe_doc = np.array([
        E_0 * math.cos(ty_doc) * math.cos(tz_doc),
        E_0 * math.cos(ty_doc) * math.sin(tz_doc),
        -E_0 * math.sin(ty_doc)
    ])
    
    print(f"  E_probe (formule doc): {v_probe_doc}")
    
    # Vérifier avec rotation - tester différentes conventions
    rotation_doc_XYZ = R.from_euler('XYZ', [theta_x_doc, theta_y_doc, theta_z_doc], degrees=True)
    rotation_doc_xyz = R.from_euler('xyz', [theta_x_doc, theta_y_doc, theta_z_doc], degrees=True)
    rotation_doc_ZYX = R.from_euler('ZYX', [theta_x_doc, theta_y_doc, theta_z_doc], degrees=True)
    rotation_doc_zyx = R.from_euler('zyx', [theta_x_doc, theta_y_doc, theta_z_doc], degrees=True)
    
    v_bench = np.array([E_0, 0.0, 0.0])
    
    # Tester avec rotation directe et inverse
    print(f"\n  Avec rotation inverse (E_bench -> E_probe):")
    v_probe_XYZ_inv = rotation_doc_XYZ.inv().apply(v_bench)
    v_probe_xyz_inv = rotation_doc_xyz.inv().apply(v_bench)
    v_probe_ZYX_inv = rotation_doc_ZYX.inv().apply(v_bench)
    v_probe_zyx_inv = rotation_doc_zyx.inv().apply(v_bench)
    
    print(f"    'XYZ'.inv(): {v_probe_XYZ_inv}")
    print(f"    'xyz'.inv(): {v_probe_xyz_inv}")
    print(f"    'ZYX'.inv(): {v_probe_ZYX_inv}")
    print(f"    'zyx'.inv(): {v_probe_zyx_inv}")
    
    print(f"\n  Avec rotation directe (E_probe -> E_bench, puis inverser):")
    # Si E_probe = R^-1 * E_bench, alors E_bench = R * E_probe
    # Donc pour obtenir E_probe, on fait R^-1 * E_bench
    # Mais testons aussi l'inverse
    v_probe_XYZ_dir = rotation_doc_XYZ.apply(v_bench)
    v_probe_xyz_dir = rotation_doc_xyz.apply(v_bench)
    
    print(f"    'XYZ' direct: {v_probe_XYZ_dir}")
    print(f"    'xyz' direct: {v_probe_xyz_dir}")
    
    # Vérifier les correspondances
    print(f"\n  Correspondances:")
    print(f"    'XYZ'.inv() = formule? {np.allclose(v_probe_XYZ_inv, v_probe_doc, atol=1e-6)}")
    print(f"    'xyz'.inv() = formule? {np.allclose(v_probe_xyz_inv, v_probe_doc, atol=1e-6)}")
    print(f"    'ZYX'.inv() = formule? {np.allclose(v_probe_ZYX_inv, v_probe_doc, atol=1e-6)}")
    print(f"    'zyx'.inv() = formule? {np.allclose(v_probe_zyx_inv, v_probe_doc, atol=1e-6)}")
    
    # Vérifier avec signes inversés
    print(f"\n  Avec signes inversés:")
    print(f"    -'XYZ'.inv() = formule? {np.allclose(-v_probe_XYZ_inv, v_probe_doc, atol=1e-6)}")
    print(f"    [x, -y, -z] = formule? {np.allclose([v_probe_XYZ_inv[0], -v_probe_XYZ_inv[1], -v_probe_XYZ_inv[2]], v_probe_doc, atol=1e-6)}")

if __name__ == '__main__':
    test_rotation_conventions()
