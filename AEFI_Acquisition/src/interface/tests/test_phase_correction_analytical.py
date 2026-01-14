"""
Test analytique approfondi de la correction de phase.

Ce test utilise des fonctions analytiques pour générer des signaux de test
avec des phases connues, calcule théoriquement le résultat attendu après
correction de phase, puis vérifie que l'implémentation produit bien le bon résultat.
"""
import unittest
import math
from typing import Dict, Tuple

from interface.presenters.signal_processor import SignalPostProcessor


class AnalyticalPhaseCorrectionTest(unittest.TestCase):
    """
    Test analytique de la correction de phase basé sur des fonctions mathématiques.
    
    Principe:
    - Génération de signaux avec phases connues via fonctions analytiques
    - Calcul théorique du résultat attendu après correction
    - Vérification que l'implémentation produit le résultat attendu
    """
    
    def setUp(self):
        self.processor = SignalPostProcessor()
        self.tolerance = 1e-10  # Tolérance pour comparaisons numériques
    
    def generate_analytical_signal(
        self, 
        amplitude: float, 
        phase_rad: float, 
        noise_i: float = 0.0, 
        noise_q: float = 0.0
    ) -> Tuple[float, float]:
        """
        Génère un signal analytique (I, Q) avec phase connue.
        
        Args:
            amplitude: Amplitude du signal
            phase_rad: Phase en radians
            noise_i: Bruit sur la composante In-Phase
            noise_q: Bruit sur la composante Quadrature
            
        Returns:
            Tuple (I, Q) représentant le signal
        """
        i = amplitude * math.cos(phase_rad) + noise_i
        q = amplitude * math.sin(phase_rad) + noise_q
        return (i, q)
    
    def compute_expected_phase_correction(
        self, 
        i: float, 
        q: float, 
        reference_phase: float
    ) -> Tuple[float, float]:
        """
        Calcule théoriquement le résultat attendu après correction de phase.
        
        La correction de phase applique une rotation de -theta pour aligner
        le vecteur de référence sur l'axe I (Q=0).
        
        Args:
            i: Composante In-Phase du signal
            q: Composante Quadrature du signal
            reference_phase: Phase de référence (theta = atan2(q_ref, i_ref))
            
        Returns:
            Tuple (I_corrected, Q_corrected) attendu
        """
        cos_theta = math.cos(reference_phase)
        sin_theta = math.sin(reference_phase)
        
        # Rotation de -theta (formule du code)
        i_corrected = i * cos_theta + q * sin_theta
        q_corrected = -i * sin_theta + q * cos_theta
        
        return (i_corrected, q_corrected)
    
    def create_sample_dict(self, axis: str, i: float, q: float) -> Dict[str, float]:
        """Crée un dictionnaire d'échantillon pour un axe donné."""
        return {
            f"{axis} In-Phase": i,
            f"{axis} Quadrature": q,
            "Uy In-Phase": 0.0,
            "Uy Quadrature": 0.0,
            "Uz In-Phase": 0.0,
            "Uz Quadrature": 0.0,
        }
    
    def test_phase_correction_analytical_sinusoidal(self):
        """
        Test avec signaux sinusoïdaux de phases variées.
        
        Scénario:
        1. Génère un signal de référence avec phase phi_ref
        2. Calibre la correction de phase sur ce signal
        3. Génère plusieurs signaux de test avec phases différentes
        4. Vérifie que chaque signal est correctement corrigé
        """
        # Paramètres du test
        amplitude = 5.0
        reference_phase = math.pi / 4  # 45 degrés
        
        # 1. Générer signal de référence
        i_ref, q_ref = self.generate_analytical_signal(amplitude, reference_phase)
        ref_sample = self.create_sample_dict("Ux", i_ref, q_ref)
        
        # 2. Calibrer la correction de phase
        self.processor.calibrate_phase(ref_sample)
        
        # Vérifier que l'angle calculé correspond à la phase de référence
        calculated_theta = self.processor.state.phase_angles.get("Ux", 0.0)
        expected_theta = math.atan2(q_ref, i_ref)
        
        self.assertAlmostEqual(calculated_theta, expected_theta, places=10)
        
        # 3. Tester plusieurs signaux avec phases différentes
        test_phases = [
            0.0,                    # 0°
            math.pi / 6,            # 30°
            math.pi / 3,            # 60°
            math.pi / 2,            # 90°
            math.pi,                # 180°
            3 * math.pi / 2,        # 270°
            math.pi / 4 + math.pi,  # 225° (référence + 180°)
        ]
        
        for test_phase in test_phases:
            # Générer signal de test
            i_test, q_test = self.generate_analytical_signal(amplitude, test_phase)
            test_sample = self.create_sample_dict("Ux", i_test, q_test)
            
            # Calculer résultat attendu théoriquement
            i_expected, q_expected = self.compute_expected_phase_correction(
                i_test, q_test, calculated_theta
            )
            
            # Traiter avec le processeur
            result = self.processor.process_sample(test_sample)
            i_result = result["Ux In-Phase"]
            q_result = result["Ux Quadrature"]
            
            # Vérifier In-Phase
            self.assertAlmostEqual(
                i_result, i_expected, places=10,
                msg=f"I mismatch at {math.degrees(test_phase):.1f}°: expected {i_expected:.10f}, got {i_result:.10f}"
            )
            
            # Vérifier Quadrature
            self.assertAlmostEqual(
                q_result, q_expected, places=10,
                msg=f"Q mismatch at {math.degrees(test_phase):.1f}°: expected {q_expected:.10f}, got {q_result:.10f}"
            )
    
    def test_phase_correction_preserves_magnitude(self):
        """
        Test que la correction de phase préserve la magnitude du signal.
        
        Propriété importante: la rotation ne change pas la magnitude.
        """
        amplitude = 3.5
        reference_phase = math.pi / 6  # 30 degrés
        
        # Générer signal de référence
        i_ref, q_ref = self.generate_analytical_signal(amplitude, reference_phase)
        ref_sample = self.create_sample_dict("Ux", i_ref, q_ref)
        
        # Calibrer
        self.processor.calibrate_phase(ref_sample)
        
        # Tester plusieurs signaux
        test_phases = [0.0, math.pi / 4, math.pi / 2, math.pi, 3 * math.pi / 2]
        
        for test_phase in test_phases:
            i_test, q_test = self.generate_analytical_signal(amplitude, test_phase)
            test_sample = self.create_sample_dict("Ux", i_test, q_test)
            
            # Magnitude avant correction
            magnitude_before = math.sqrt(i_test**2 + q_test**2)
            
            # Traiter
            result = self.processor.process_sample(test_sample)
            i_result = result["Ux In-Phase"]
            q_result = result["Ux Quadrature"]
            
            # Magnitude après correction
            magnitude_after = math.sqrt(i_result**2 + q_result**2)
            
            self.assertAlmostEqual(
                magnitude_before, magnitude_after, places=10,
                msg=f"Magnitude not preserved at {math.degrees(test_phase):.1f}°: "
                    f"before={magnitude_before:.10f}, after={magnitude_after:.10f}"
            )
    
    def test_phase_correction_reference_alignment(self):
        """
        Test que le signal de référence est bien aligné sur l'axe I (Q=0).
        
        Après calibration, le signal de référence doit avoir Q=0.
        """
        amplitude = 4.0
        reference_phase = math.pi / 3  # 60 degrés
        
        # Générer signal de référence
        i_ref, q_ref = self.generate_analytical_signal(amplitude, reference_phase)
        ref_sample = self.create_sample_dict("Ux", i_ref, q_ref)
        
        # Calibrer
        self.processor.calibrate_phase(ref_sample)
        
        # Traiter le signal de référence lui-même
        result = self.processor.process_sample(ref_sample)
        i_result = result["Ux In-Phase"]
        q_result = result["Ux Quadrature"]
        
        # Vérifier que Q est proche de 0
        self.assertAlmostEqual(
            q_result, 0.0, places=10,
            msg=f"Reference Q should be zero, got {q_result:.10f}"
        )
        
        # Vérifier que I correspond à la magnitude
        expected_magnitude = math.sqrt(i_ref**2 + q_ref**2)
        self.assertAlmostEqual(
            i_result, expected_magnitude, places=10,
            msg=f"Reference I should equal magnitude: expected {expected_magnitude:.10f}, got {i_result:.10f}"
        )
    
    def test_phase_correction_with_noise(self):
        """
        Test de correction de phase avec bruit sur les signaux.
        
        Vérifie que la correction fonctionne même avec du bruit additif.
        """
        amplitude = 2.5
        reference_phase = math.pi / 4
        
        # Signal de référence avec bruit
        noise_i_ref = 0.1
        noise_q_ref = -0.05
        i_ref, q_ref = self.generate_analytical_signal(amplitude, reference_phase, noise_i_ref, noise_q_ref)
        ref_sample = self.create_sample_dict("Ux", i_ref, q_ref)
        
        # Calibrer
        self.processor.calibrate_phase(ref_sample)
        theta = self.processor.state.phase_angles["Ux"]
        
        # Signal de test avec bruit différent
        noise_i_test = 0.15
        noise_q_test = 0.08
        i_test, q_test = self.generate_analytical_signal(amplitude, math.pi / 6, noise_i_test, noise_q_test)
        test_sample = self.create_sample_dict("Ux", i_test, q_test)
        
        # Calculer attendu
        i_expected, q_expected = self.compute_expected_phase_correction(i_test, q_test, theta)
        
        # Traiter
        result = self.processor.process_sample(test_sample)
        i_result = result["Ux In-Phase"]
        q_result = result["Ux Quadrature"]
        
        self.assertAlmostEqual(
            i_result, i_expected, places=10,
            msg=f"I with noise mismatch: expected {i_expected:.10f}, got {i_result:.10f}"
        )
        
        self.assertAlmostEqual(
            q_result, q_expected, places=10,
            msg=f"Q with noise mismatch: expected {q_expected:.10f}, got {q_result:.10f}"
        )
    
    def test_phase_correction_multiple_axes(self):
        """
        Test de correction de phase sur plusieurs axes simultanément.
        
        Chaque axe doit avoir sa propre correction de phase indépendante.
        """
        amplitude = 3.0
        
        # Différentes phases pour chaque axe
        phases = {
            "Ux": math.pi / 4,      # 45°
            "Uy": math.pi / 6,       # 30°
            "Uz": math.pi / 3,       # 60°
        }
        
        # Générer signaux de référence pour chaque axe
        ref_sample = {
            "Ux In-Phase": 0.0, "Ux Quadrature": 0.0,
            "Uy In-Phase": 0.0, "Uy Quadrature": 0.0,
            "Uz In-Phase": 0.0, "Uz Quadrature": 0.0,
        }
        
        for axis, phase in phases.items():
            i, q = self.generate_analytical_signal(amplitude, phase)
            ref_sample[f"{axis} In-Phase"] = i
            ref_sample[f"{axis} Quadrature"] = q
        
        # Calibrer
        self.processor.calibrate_phase(ref_sample)
        
        # Vérifier que chaque axe a son angle correct
        for axis, expected_phase in phases.items():
            i_ref = ref_sample[f"{axis} In-Phase"]
            q_ref = ref_sample[f"{axis} Quadrature"]
            expected_theta = math.atan2(q_ref, i_ref)
            calculated_theta = self.processor.state.phase_angles[axis]
            
            self.assertAlmostEqual(
                calculated_theta, expected_theta, places=10,
                msg=f"Phase angle mismatch for {axis}: expected {expected_theta:.10f}, got {calculated_theta:.10f}"
            )
        
        # Tester un signal avec phases différentes
        test_phases = {
            "Ux": math.pi / 2,      # 90°
            "Uy": 0.0,             # 0°
            "Uz": math.pi,          # 180°
        }
        
        test_sample = {}
        expected_results = {}
        
        for axis, phase in test_phases.items():
            i, q = self.generate_analytical_signal(amplitude, phase)
            test_sample[f"{axis} In-Phase"] = i
            test_sample[f"{axis} Quadrature"] = q
            
            theta = self.processor.state.phase_angles[axis]
            i_exp, q_exp = self.compute_expected_phase_correction(i, q, theta)
            expected_results[axis] = (i_exp, q_exp)
        
        # Traiter
        result = self.processor.process_sample(test_sample)
        
        # Vérifier chaque axe
        for axis, (i_exp, q_exp) in expected_results.items():
            i_res = result[f"{axis} In-Phase"]
            q_res = result[f"{axis} Quadrature"]
            
            self.assertAlmostEqual(
                i_res, i_exp, places=10,
                msg=f"{axis} I mismatch: expected {i_exp:.10f}, got {i_res:.10f}"
            )
            
            self.assertAlmostEqual(
                q_res, q_exp, places=10,
                msg=f"{axis} Q mismatch: expected {q_exp:.10f}, got {q_res:.10f}"
            )


if __name__ == "__main__":
    unittest.main()
