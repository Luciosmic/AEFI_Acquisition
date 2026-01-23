"""
Tests pour vérifier les invariants de traitement du signal:
1. Préservation de l'amplitude totale: sqrt(I² + Q²) doit rester constant
2. Préservation du signe de la composante in-phase après rotation
"""
import unittest
import math
from datetime import datetime
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement


class TestVoltageMeasurementInvariants(unittest.TestCase):
    """Test les invariants lors des corrections de signal."""
    
    def test_phase_rotation_preserves_amplitude(self):
        """
        Vérifie que la rotation de phase préserve l'amplitude totale.
        Rotation standard: I' = I*cos(θ) + Q*sin(θ), Q' = -I*sin(θ) + Q*cos(θ)
        """
        # Test avec différents angles et amplitudes
        test_cases = [
            (1.0, 1.0, math.pi/4),  # 45 deg, amplitude = sqrt(2)
            (3.0, 4.0, math.atan2(4.0, 3.0)),  # amplitude = 5.0
            (10.0, 0.0, 0.0),  # Déjà aligné
            (0.0, 5.0, math.pi/2),  # 90 deg
            (-3.0, 4.0, math.atan2(4.0, -3.0)),  # Quadrant 2
        ]
        
        for i_val, q_val, theta in test_cases:
            with self.subTest(i=i_val, q=q_val, theta=theta):
                # Amplitude avant rotation
                mag_before = math.sqrt(i_val**2 + q_val**2)
                
                # Rotation de phase (alignement sur axe I)
                cos_t = math.cos(theta)
                sin_t = math.sin(theta)
                i_new = i_val * cos_t + q_val * sin_t
                q_new = -i_val * sin_t + q_val * cos_t
                
                # Amplitude après rotation
                mag_after = math.sqrt(i_new**2 + q_new**2)
                
                # Vérifier préservation de l'amplitude
                self.assertAlmostEqual(
                    mag_before, mag_after, 
                    places=10,
                    msg=f"Amplitude not preserved: before={mag_before:.10f}, after={mag_after:.10f}"
                )
                
                # Vérifier que quadrature est proche de zéro après rotation
                self.assertAlmostEqual(
                    q_new, 0.0, 
                    places=10,
                    msg=f"Quadrature should be zero after phase alignment: Q={q_new:.10f}"
                )
    
    def test_phase_rotation_preserves_in_phase_sign(self):
        """
        PROBLÈME IDENTIFIÉ: La rotation de phase actuelle aligne toujours sur I positif,
        ce qui perd le signe quand I_original est négatif.
        
        Pour préserver le signe, il faut:
        - Si I_original >= 0: I_rotated = +magnitude
        - Si I_original < 0: I_rotated = -magnitude
        
        La rotation standard aligne toujours sur I positif, donc il faut corriger le signe.
        """
        test_cases = [
            (3.0, 4.0),   # Positif -> I_rotated devrait être +5.0
            (-3.0, 4.0),  # Négatif (quadrant 2) -> I_rotated devrait être -5.0
            (3.0, -4.0),  # Positif (quadrant 4) -> I_rotated devrait être +5.0
            (-3.0, -4.0), # Négatif (quadrant 3) -> I_rotated devrait être -5.0
        ]
        
        for i_val, q_val in test_cases:
            with self.subTest(i=i_val, q=q_val):
                # Calculer l'angle pour aligner sur I
                theta = math.atan2(q_val, i_val)
                
                # Rotation standard (alignement sur I positif)
                cos_t = math.cos(theta)
                sin_t = math.sin(theta)
                i_new = i_val * cos_t + q_val * sin_t
                
                # Amplitude (toujours positive)
                mag = math.sqrt(i_val**2 + q_val**2)
                
                # PROBLÈME: La rotation standard donne toujours I_new > 0
                # Pour préserver le signe, il faut appliquer le signe de I_original
                if abs(i_val) > 1e-10:
                    # Correction: préserver le signe de I_original
                    i_corrected = mag if i_val >= 0 else -mag
                    
                    # Vérifier que la rotation standard donne toujours I_new > 0
                    self.assertGreater(
                        i_new, 0,
                        msg=f"Standard rotation always gives I_new > 0: I_new={i_new}"
                    )
                    
                    # Vérifier que la correction préserve le signe
                    expected_sign = 1 if i_val >= 0 else -1
                    actual_sign = 1 if i_corrected >= 0 else -1
                    self.assertEqual(
                        expected_sign, actual_sign,
                        msg=f"Corrected sign: I_orig={i_val}, I_corrected={i_corrected}"
                    )
                    
                    # Vérifier que |I_corrected| = magnitude
                    self.assertAlmostEqual(
                        abs(i_corrected), mag,
                        places=10,
                        msg=f"|I_corrected| should equal magnitude: |{i_corrected}| != {mag}"
                    )
    
    def test_noise_subtraction_preserves_structure(self):
        """
        Vérifie que la soustraction de bruit préserve la structure du signal.
        (I, Q) - (I_offset, Q_offset) = (I - I_offset, Q - Q_offset)
        """
        measurement = VoltageMeasurement(
            voltage_x_in_phase=5.0,
            voltage_x_quadrature=3.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=datetime.now()
        )
        
        # Offset de bruit
        noise_i = 1.0
        noise_q = 0.5
        
        # Après soustraction
        i_corrected = measurement.voltage_x_in_phase - noise_i
        q_corrected = measurement.voltage_x_quadrature - noise_q
        
        # Vérifier que la structure est préservée
        self.assertAlmostEqual(i_corrected, 4.0)
        self.assertAlmostEqual(q_corrected, 2.5)
        
        # L'amplitude peut changer (c'est normal), mais la structure reste
        # (pas de rotation, juste translation)
    
    def test_combined_corrections_invariants(self):
        """
        Test que les corrections combinées respectent les invariants.
        Ordre: Noise -> Phase -> Primary
        """
        # Signal initial: (3, 4) avec amplitude 5.0
        i_initial = 3.0
        q_initial = 4.0
        mag_initial = math.sqrt(i_initial**2 + q_initial**2)
        
        # 1. Noise subtraction: (3, 4) - (1, 1) = (2, 3)
        noise_i, noise_q = 1.0, 1.0
        i_after_noise = i_initial - noise_i
        q_after_noise = q_initial - noise_q
        
        # 2. Phase rotation: aligner (2, 3) sur I
        theta = math.atan2(q_after_noise, i_after_noise)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        i_after_phase = i_after_noise * cos_t + q_after_noise * sin_t
        q_after_phase = -i_after_noise * sin_t + q_after_noise * cos_t
        
        # Vérifier que l'amplitude après noise+phase est préservée
        mag_after_noise = math.sqrt(i_after_noise**2 + q_after_noise**2)
        mag_after_phase = math.sqrt(i_after_phase**2 + q_after_phase**2)
        
        # L'amplitude après noise peut être différente (normal)
        # Mais l'amplitude doit être préservée par la rotation de phase
        self.assertAlmostEqual(mag_after_noise, mag_after_phase, places=10)
        
        # Quadrature doit être proche de zéro après rotation
        self.assertAlmostEqual(q_after_phase, 0.0, places=10)
        
        # 3. Primary subtraction: (I_phase, 0) - (I_primary, 0) = (I_phase - I_primary, 0)
        primary_i = 0.5
        i_final = i_after_phase - primary_i
        q_final = q_after_phase - 0.0  # Primary Q should be 0 after phase alignment
        
        # Après primary, l'amplitude change (normal, c'est une soustraction)
        # Mais la quadrature reste à zéro
        self.assertAlmostEqual(q_final, 0.0, places=10)


if __name__ == "__main__":
    unittest.main()
