"""
Tests unitaires pour les fonctions de rotation par quaternions.
"""
import numpy as np
import pytest
from cube_geometry_quaternion import (
    quaternion_from_euler_xyz,
    euler_xyz_from_quaternion,
    quaternion_multiply,
    quaternion_slerp,
    quaternion_identity,
    get_default_quaternion,
    create_rotation_from_quaternion,
)


class TestQuaternionConversions:
    """Tests de conversion Euler <-> Quaternion."""
    
    def test_euler_to_quaternion_identity(self):
        """Test: angles nuls = quaternion identité."""
        quat = quaternion_from_euler_xyz(0, 0, 0)
        expected = quaternion_identity()
        assert np.allclose(quat, expected, atol=1e-10)
    
    def test_quaternion_to_euler_identity(self):
        """Test: quaternion identité = angles nuls."""
        quat = quaternion_identity()
        theta_x, theta_y, theta_z = euler_xyz_from_quaternion(quat)
        assert np.allclose([theta_x, theta_y, theta_z], [0, 0, 0], atol=1e-10)
    
    def test_euler_quaternion_roundtrip(self):
        """Test: Euler -> Quaternion -> Euler préserve les angles."""
        test_cases = [
            (45.0, 30.0, 60.0),
            (90.0, 0.0, 0.0),
            (0.0, 90.0, 0.0),
            (0.0, 0.0, 90.0),
            (30.0, 45.0, 60.0),
            (-45.0, -30.0, -60.0),
        ]
        
        for theta_x, theta_y, theta_z in test_cases:
            quat = quaternion_from_euler_xyz(theta_x, theta_y, theta_z)
            theta_x2, theta_y2, theta_z2 = euler_xyz_from_quaternion(quat)
            
            assert np.allclose([theta_x, theta_y, theta_z], 
                             [theta_x2, theta_y2, theta_z2], atol=1e-8), \
                f"Roundtrip failed for ({theta_x}, {theta_y}, {theta_z})"
    
    def test_gimbal_lock_case(self):
        """Test: Gimbal lock (theta_y = ±90°) est géré correctement."""
        # Configuration problématique avec Euler
        theta_x, theta_y, theta_z = 30.0, 90.0, 45.0
        
        quat = quaternion_from_euler_xyz(theta_x, theta_y, theta_z)
        
        # Vérifier que le quaternion est valide (norme = 1)
        norm = np.linalg.norm(quat)
        assert np.isclose(norm, 1.0, atol=1e-10)
        
        # Vérifier qu'on peut reconstruire une rotation
        rot = create_rotation_from_quaternion(quat)
        v = np.array([1, 0, 0])
        v_rotated = rot.apply(v)
        
        # La rotation doit avoir un effet
        assert not np.allclose(v, v_rotated, atol=1e-6)


class TestQuaternionOperations:
    """Tests des opérations sur les quaternions."""
    
    def test_quaternion_identity_is_neutral(self):
        """Test: quaternion identité est neutre pour la multiplication."""
        q = quaternion_from_euler_xyz(45, 30, 60)
        q_id = quaternion_identity()
        
        # q * identity = q
        q_result = quaternion_multiply(q, q_id)
        assert np.allclose(q, q_result, atol=1e-10)
        
        # identity * q = q
        q_result2 = quaternion_multiply(q_id, q)
        assert np.allclose(q, q_result2, atol=1e-10)
    
    def test_quaternion_multiply_composition(self):
        """Test: multiplication de quaternions = composition de rotations."""
        # Rotation de 90° autour de X
        q_x = quaternion_from_euler_xyz(90, 0, 0)
        
        # Rotation de 90° autour de Y
        q_y = quaternion_from_euler_xyz(0, 90, 0)
        
        # Composition: d'abord X, puis Y
        q_composed = quaternion_multiply(q_y, q_x)
        
        # Vérifier que la composition est correcte
        rot_composed = create_rotation_from_quaternion(q_composed)
        
        # Appliquer à un vecteur
        v = np.array([1, 0, 0])
        v_result = rot_composed.apply(v)
        
        # Résultat attendu: [1,0,0] -> X90° -> [1,0,0] (inchangé car autour de X)
        #                           -> Y90° -> [0,0,-1]
        expected = np.array([0, 0, -1])
        assert np.allclose(v_result, expected, atol=1e-10)
    
    def test_quaternion_norm_preserved(self):
        """Test: les quaternions ont toujours une norme de 1."""
        test_angles = [
            (0, 0, 0),
            (45, 30, 60),
            (90, 90, 90),
            (180, 0, 0),
            (-45, -30, -60),
        ]
        
        for theta_x, theta_y, theta_z in test_angles:
            quat = quaternion_from_euler_xyz(theta_x, theta_y, theta_z)
            norm = np.linalg.norm(quat)
            assert np.isclose(norm, 1.0, atol=1e-10), \
                f"Quaternion norm != 1 for angles ({theta_x}, {theta_y}, {theta_z})"


class TestQuaternionSlerp:
    """Tests de l'interpolation sphérique (SLERP)."""
    
    def test_slerp_endpoints(self):
        """Test: SLERP aux extrémités retourne les quaternions de départ/arrivée."""
        q1 = quaternion_identity()
        q2 = quaternion_from_euler_xyz(90, 0, 0)
        
        # t=0 -> q1
        q_start = quaternion_slerp(q1, q2, 0.0)
        assert np.allclose(q_start, q1, atol=1e-10)
        
        # t=1 -> q2
        q_end = quaternion_slerp(q1, q2, 1.0)
        assert np.allclose(q_end, q2, atol=1e-10)
    
    def test_slerp_midpoint(self):
        """Test: SLERP à mi-chemin donne une rotation intermédiaire."""
        q1 = quaternion_identity()
        q2 = quaternion_from_euler_xyz(90, 0, 0)
        
        # Interpoler à mi-chemin
        q_mid = quaternion_slerp(q1, q2, 0.5)
        
        # Convertir en Euler pour vérifier
        theta_x, theta_y, theta_z = euler_xyz_from_quaternion(q_mid)
        
        # Devrait être proche de 45° autour de X
        assert np.isclose(theta_x, 45.0, atol=1.0)
        assert np.isclose(theta_y, 0.0, atol=1.0)
        assert np.isclose(theta_z, 0.0, atol=1.0)
    
    def test_slerp_smoothness(self):
        """Test: SLERP produit une interpolation fluide."""
        q1 = quaternion_identity()
        q2 = quaternion_from_euler_xyz(90, 45, 30)
        
        # Interpoler à plusieurs points
        t_values = np.linspace(0, 1, 11)
        quats = [quaternion_slerp(q1, q2, t) for t in t_values]
        
        # Vérifier que tous les quaternions ont une norme de 1
        for quat in quats:
            norm = np.linalg.norm(quat)
            assert np.isclose(norm, 1.0, atol=1e-10)
        
        # Vérifier que l'interpolation est monotone (angles croissants)
        angles = [euler_xyz_from_quaternion(q) for q in quats]
        
        # Les angles doivent varier de manière continue
        for i in range(len(angles) - 1):
            # Pas de saut brusque
            diff = np.array(angles[i+1]) - np.array(angles[i])
            assert np.all(np.abs(diff) < 20), "Saut brusque détecté dans SLERP"


class TestDefaultQuaternion:
    """Tests du quaternion par défaut."""
    
    def test_default_quaternion_matches_default_euler(self):
        """Test: quaternion par défaut correspond aux angles par défaut."""
        from cube_geometry_quaternion import get_default_theta_y
        
        q_default = get_default_quaternion()
        theta_x, theta_y, theta_z = euler_xyz_from_quaternion(q_default)
        
        expected_theta_y = get_default_theta_y()
        
        assert np.isclose(theta_x, 0.0, atol=1e-10)
        assert np.isclose(theta_y, expected_theta_y, atol=1e-8)
        assert np.isclose(theta_z, 0.0, atol=1e-10)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
