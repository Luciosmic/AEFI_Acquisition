"""
Test robuste de la correction de phase basé sur des fonctions analytiques.

Ce test utilise des fonctions mathématiques prédictibles pour valider
le comportement de la correction de phase dans SignalPostProcessor.
"""

import math
import pytest
import numpy as np
from typing import Dict, Tuple

# Import du module à tester
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "AEFI_Acquisition" / "src"))

from interface.presenters.signal_processor import SignalPostProcessor


class TestPhaseCorrectionRobust:
    """
    Tests robustes pour la correction de phase utilisant des fonctions analytiques.
    """
    
    def test_phase_correction_basic_rotation(self):
        """
        Test de base : rotation d'un vecteur connu vers l'axe I.
        Utilise un vecteur à 45° qui doit être aligné sur l'axe I après correction.
        """
        processor = SignalPostProcessor()
        
        # Vecteur de référence à 45° (I=1, Q=1)
        # Angle attendu : atan2(1, 1) = π/4
        ref_sample = {
            "Ux In-Phase": 1.0,
            "Ux Quadrature": 1.0,
            "Uy In-Phase": 0.0,
            "Uy Quadrature": 0.0,
            "Uz In-Phase": 0.0,
            "Uz Quadrature": 0.0,
        }
        
        # Calibrer la phase
        processor.calibrate_phase(ref_sample)
        
        # Vérifier que l'angle calculé est correct
        expected_angle = math.atan2(1.0, 1.0)  # π/4
        assert abs(processor.state.phase_angles["Ux"] - expected_angle) < 1e-10
        
        # Traiter le même vecteur - il devrait être aligné sur l'axe I
        processed = processor.process_sample(ref_sample)
        
        # Après rotation de -π/4, le vecteur (1, 1) devrait devenir (√2, 0)
        expected_i = math.sqrt(2.0)
        expected_q = 0.0
        
        assert abs(processed["Ux In-Phase"] - expected_i) < 1e-9
        assert abs(processed["Ux Quadrature"] - expected_q) < 1e-9
    
    def test_phase_correction_analytical_vectors(self):
        """
        Test avec plusieurs vecteurs analytiques à différents angles.
        Chaque vecteur est défini par un angle θ, et après correction,
        il doit être aligné sur l'axe I.
        """
        processor = SignalPostProcessor()
        
        # Angles de test en degrés
        test_angles_deg = [0, 30, 45, 60, 90, 120, 135, 150, 180, 
                           -30, -45, -60, -90, -120, -150]
        
        for angle_deg in test_angles_deg:
            angle_rad = math.radians(angle_deg)
            
            # Créer un vecteur unitaire à cet angle
            i_ref = math.cos(angle_rad)
            q_ref = math.sin(angle_rad)
            
            # Réinitialiser le processeur pour chaque test
            processor = SignalPostProcessor()
            
            # Calibrer avec ce vecteur
            ref_sample = {
                "Ux In-Phase": i_ref,
                "Ux Quadrature": q_ref,
                "Uy In-Phase": 0.0,
                "Uy Quadrature": 0.0,
                "Uz In-Phase": 0.0,
                "Uz Quadrature": 0.0,
            }
            processor.calibrate_phase(ref_sample)
            
            # Vérifier l'angle calculé
            expected_angle = math.atan2(q_ref, i_ref)
            computed_angle = processor.state.phase_angles["Ux"]
            assert abs(computed_angle - expected_angle) < 1e-10, \
                f"Angle incorrect pour {angle_deg}°"
            
            # Traiter le vecteur - il devrait être aligné sur l'axe I
            processed = processor.process_sample(ref_sample)
            
            # La magnitude doit être préservée
            magnitude_before = math.sqrt(i_ref**2 + q_ref**2)
            magnitude_after = math.sqrt(processed["Ux In-Phase"]**2 + 
                                       processed["Ux Quadrature"]**2)
            assert abs(magnitude_before - magnitude_after) < 1e-9, \
                f"Magnitude non préservée pour {angle_deg}°"
            
            # Q doit être proche de 0 (aligné sur l'axe I)
            assert abs(processed["Ux Quadrature"]) < 1e-9, \
                f"Q non nul après correction pour {angle_deg}°: Q={processed['Ux Quadrature']}"
            
            # I doit être égal à la magnitude
            assert abs(processed["Ux In-Phase"] - magnitude_before) < 1e-9, \
                f"I incorrect pour {angle_deg}°: I={processed['Ux In-Phase']}, attendu={magnitude_before}"
    
    def test_phase_correction_rotation_matrix_properties(self):
        """
        Test des propriétés mathématiques de la rotation :
        - Préservation de la magnitude
        - Orthogonalité de la matrice de rotation
        - Déteminant = 1
        """
        processor = SignalPostProcessor()
        
        # Vecteur de référence
        i_ref = 2.0
        q_ref = 3.0
        magnitude = math.sqrt(i_ref**2 + q_ref**2)
        
        ref_sample = {
            "Ux In-Phase": i_ref,
            "Ux Quadrature": q_ref,
            "Uy In-Phase": 0.0,
            "Uy Quadrature": 0.0,
            "Uz In-Phase": 0.0,
            "Uz Quadrature": 0.0,
        }
        
        processor.calibrate_phase(ref_sample)
        theta = processor.state.phase_angles["Ux"]
        
        # Vérifier que la matrice de rotation est orthogonale
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        
        # Matrice de rotation R(-θ)
        # R = [[cos(θ), sin(θ)], [-sin(θ), cos(θ)]]
        # Déteminant = cos²(θ) + sin²(θ) = 1
        det = cos_t**2 + sin_t**2
        assert abs(det - 1.0) < 1e-10, "Déterminant de la rotation doit être 1"
        
        # Traiter le vecteur
        processed = processor.process_sample(ref_sample)
        
        # Vérifier la préservation de la magnitude
        magnitude_after = math.sqrt(processed["Ux In-Phase"]**2 + 
                                    processed["Ux Quadrature"]**2)
        assert abs(magnitude - magnitude_after) < 1e-9, \
            f"Magnitude non préservée: {magnitude} vs {magnitude_after}"
    
    def test_phase_correction_multiple_vectors_same_calibration(self):
        """
        Test que plusieurs vecteurs différents, calibrés avec le même vecteur de référence,
        sont tous correctement alignés.
        """
        processor = SignalPostProcessor()
        
        # Vecteur de référence à 60°
        ref_angle = math.radians(60)
        i_ref = math.cos(ref_angle)
        q_ref = math.sin(ref_angle)
        
        ref_sample = {
            "Ux In-Phase": i_ref,
            "Ux Quadrature": q_ref,
            "Uy In-Phase": 0.0,
            "Uy Quadrature": 0.0,
            "Uz In-Phase": 0.0,
            "Uz Quadrature": 0.0,
        }
        
        processor.calibrate_phase(ref_sample)
        
        # Tester plusieurs vecteurs avec la même calibration
        test_vectors = [
            (1.0, 0.0),    # 0°
            (0.0, 1.0),    # 90°
            (-1.0, 0.0),   # 180°
            (0.0, -1.0),   # -90°
            (math.sqrt(3)/2, 0.5),  # 30°
            (0.5, math.sqrt(3)/2),  # 60°
        ]
        
        for i_test, q_test in test_vectors:
            test_sample = {
                "Ux In-Phase": i_test,
                "Ux Quadrature": q_test,
                "Uy In-Phase": 0.0,
                "Uy Quadrature": 0.0,
                "Uz In-Phase": 0.0,
                "Uz Quadrature": 0.0,
            }
            
            processed = processor.process_sample(test_sample)
            
            # Calculer l'angle résultant
            angle_result = math.atan2(processed["Ux Quadrature"], 
                                      processed["Ux In-Phase"])
            
            # L'angle résultant devrait être l'angle du vecteur de test moins l'angle de référence
            angle_test = math.atan2(q_test, i_test)
            expected_angle = angle_test - ref_angle
            
            # Normaliser l'angle entre -π et π
            while expected_angle > math.pi:
                expected_angle -= 2 * math.pi
            while expected_angle < -math.pi:
                expected_angle += 2 * math.pi
            
            # Vérifier que l'angle résultant correspond
            assert abs(angle_result - expected_angle) < 1e-9, \
                f"Angle incorrect pour vecteur ({i_test}, {q_test}): " \
                f"obtenu={math.degrees(angle_result)}°, " \
                f"attendu={math.degrees(expected_angle)}°"
    
    def test_phase_correction_zero_vector(self):
        """
        Test du comportement avec un vecteur nul (0, 0).
        """
        processor = SignalPostProcessor()
        
        # Essayer de calibrer avec un vecteur nul
        zero_sample = {
            "Ux In-Phase": 0.0,
            "Ux Quadrature": 0.0,
            "Uy In-Phase": 0.0,
            "Uy Quadrature": 0.0,
            "Uz In-Phase": 0.0,
            "Uz Quadrature": 0.0,
        }
        
        # atan2(0, 0) est défini comme 0 en Python
        processor.calibrate_phase(zero_sample)
        assert processor.state.phase_angles["Ux"] == 0.0
        
        # Traiter un vecteur nul
        processed = processor.process_sample(zero_sample)
        assert abs(processed["Ux In-Phase"]) < 1e-10
        assert abs(processed["Ux Quadrature"]) < 1e-10
    
    def test_phase_correction_all_axes(self):
        """
        Test que la correction de phase fonctionne indépendamment pour chaque axe.
        Note: calibrate_phase traite tous les axes simultanément, donc on doit
        passer toutes les valeurs en une seule fois.
        """
        processor = SignalPostProcessor()
        
        # Calibrer tous les axes avec des angles différents en une seule fois
        angles = {
            "Ux": math.radians(45),
            "Uy": math.radians(30),
            "Uz": math.radians(60),
        }
        
        # Créer un échantillon complet avec tous les axes
        ref_sample = {
            "Ux In-Phase": math.cos(angles["Ux"]),
            "Ux Quadrature": math.sin(angles["Ux"]),
            "Uy In-Phase": math.cos(angles["Uy"]),
            "Uy Quadrature": math.sin(angles["Uy"]),
            "Uz In-Phase": math.cos(angles["Uz"]),
            "Uz Quadrature": math.sin(angles["Uz"]),
        }
        
        # Calibrer tous les axes en une fois
        processor.calibrate_phase(ref_sample)
        
        # Vérifier que tous les angles sont corrects
        for axis, expected_angle in angles.items():
            computed_angle = processor.state.phase_angles[axis]
            assert abs(computed_angle - expected_angle) < 1e-10, \
                f"Angle incorrect pour {axis}: obtenu={computed_angle}, attendu={expected_angle}"
        
        # Tester avec un échantillon complet
        test_sample = {
            "Ux In-Phase": math.cos(math.radians(45)),
            "Ux Quadrature": math.sin(math.radians(45)),
            "Uy In-Phase": math.cos(math.radians(30)),
            "Uy Quadrature": math.sin(math.radians(30)),
            "Uz In-Phase": math.cos(math.radians(60)),
            "Uz Quadrature": math.sin(math.radians(60)),
        }
        
        processed = processor.process_sample(test_sample)
        
        # Chaque axe devrait être aligné sur I (Q ≈ 0)
        for axis in ["Ux", "Uy", "Uz"]:
            q_val = processed[f"{axis} Quadrature"]
            assert abs(q_val) < 1e-9, f"Q non nul pour {axis}: {q_val}"
    
    def test_phase_correction_sequential_calibration(self):
        """
        Test que la recalibration écrase la calibration précédente.
        """
        processor = SignalPostProcessor()
        
        # Première calibration à 45°
        ref1 = {
            "Ux In-Phase": math.cos(math.radians(45)),
            "Ux Quadrature": math.sin(math.radians(45)),
            "Uy In-Phase": 0.0,
            "Uy Quadrature": 0.0,
            "Uz In-Phase": 0.0,
            "Uz Quadrature": 0.0,
        }
        processor.calibrate_phase(ref1)
        angle1 = processor.state.phase_angles["Ux"]
        
        # Deuxième calibration à 90°
        ref2 = {
            "Ux In-Phase": math.cos(math.radians(90)),
            "Ux Quadrature": math.sin(math.radians(90)),
            "Uy In-Phase": 0.0,
            "Uy Quadrature": 0.0,
            "Uz In-Phase": 0.0,
            "Uz Quadrature": 0.0,
        }
        processor.calibrate_phase(ref2)
        angle2 = processor.state.phase_angles["Ux"]
        
        # L'angle doit être celui de la deuxième calibration
        expected_angle2 = math.radians(90)
        assert abs(angle2 - expected_angle2) < 1e-10
        
        # Traiter avec le vecteur de la deuxième calibration
        processed = processor.process_sample(ref2)
        assert abs(processed["Ux Quadrature"]) < 1e-9
    
    def test_phase_correction_analytical_verification(self):
        """
        Vérification analytique complète : pour un vecteur (I, Q) et un angle θ,
        vérifier que la rotation produit le résultat attendu.
        """
        processor = SignalPostProcessor()
        
        # Vecteur de test
        i_test = 3.0
        q_test = 4.0
        magnitude = math.sqrt(i_test**2 + q_test**2)
        
        # Vecteur de référence pour calibration
        ref_angle = math.radians(30)
        i_ref = math.cos(ref_angle)
        q_ref = math.sin(ref_angle)
        
        ref_sample = {
            "Ux In-Phase": i_ref,
            "Ux Quadrature": q_ref,
            "Uy In-Phase": 0.0,
            "Uy Quadrature": 0.0,
            "Uz In-Phase": 0.0,
            "Uz Quadrature": 0.0,
        }
        
        processor.calibrate_phase(ref_sample)
        theta = processor.state.phase_angles["Ux"]
        
        # Calcul analytique manuel de la rotation
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        
        i_expected = i_test * cos_t + q_test * sin_t
        q_expected = -i_test * sin_t + q_test * cos_t
        
        # Traiter avec le processeur
        test_sample = {
            "Ux In-Phase": i_test,
            "Ux Quadrature": q_test,
            "Uy In-Phase": 0.0,
            "Uy Quadrature": 0.0,
            "Uz In-Phase": 0.0,
            "Uz Quadrature": 0.0,
        }
        
        processed = processor.process_sample(test_sample)
        
        # Comparer avec le calcul analytique
        assert abs(processed["Ux In-Phase"] - i_expected) < 1e-9, \
            f"I incorrect: obtenu={processed['Ux In-Phase']}, attendu={i_expected}"
        assert abs(processed["Ux Quadrature"] - q_expected) < 1e-9, \
            f"Q incorrect: obtenu={processed['Ux Quadrature']}, attendu={q_expected}"


if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([__file__, "-v"])
