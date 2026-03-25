import unittest
import math
import sys
from pathlib import Path

# Add the skills directory to sys.path to import DiagramFriendlyTest
skills_dir = Path(__file__).parents[3] / ".cursor" / "skills" / "diagram_friendly_test"
sys.path.append(str(skills_dir))

from diagram_friendly_test import DiagramFriendlyTest
from interface.presenters.signal_processor import SignalPostProcessor

class TestSignalPostProcessor(DiagramFriendlyTest):
    
    def setUp(self):
        super().setUp()
        self.processor = SignalPostProcessor()
        self.log_interaction("Test", "CREATE", "SignalPostProcessor", "Initialized processor instance")
        
    def test_noise_subtraction(self):
        """Verify noise offset is correctly subtracted."""
        self.log_divider("Noise Subtraction Test")
        
        # 1. Calibrate Noise
        raw_noise = {
            "Ux In-Phase": 0.1, "Ux Quadrature": 0.2,
            "Uy In-Phase": 0.0, "Uy Quadrature": 0.0,
            "Uz In-Phase": 0.0, "Uz Quadrature": 0.0,
        }
        self.log_interaction("Test", "CALIBRATE", "SignalPostProcessor", "Calibrate Noise Offset", data=raw_noise)
        self.processor.calibrate_noise(raw_noise)
        
        # 2. Process a sample
        sample = {
            "Ux In-Phase": 1.1, "Ux Quadrature": 1.2,
            "Uy In-Phase": 5.0, "Uy Quadrature": 5.0,
            "Uz In-Phase": 0.0, "Uz Quadrature": 0.0,
        }
        self.log_interaction("Test", "PROCESS", "SignalPostProcessor", "Process Sample", data=sample)
        result = self.processor.process_sample(sample)
        
        # 3. Verify
        self.log_interaction("Test", "ASSERT", "Result", "Check Ux In-Phase", expect="1.0", got=result["Ux In-Phase"])
        self.assertAlmostEqual(result["Ux In-Phase"], 1.0)
        
        self.log_interaction("Test", "ASSERT", "Result", "Check Ux Quadrature", expect="1.0", got=result["Ux Quadrature"])
        self.assertAlmostEqual(result["Ux Quadrature"], 1.0)
        
        self.log_interaction("Test", "ASSERT", "Result", "Check Uy In-Phase", expect="5.0", got=result["Uy In-Phase"])
        self.assertAlmostEqual(result["Uy In-Phase"], 5.0)

    def test_phase_alignment(self):
        """Verify phase rotation aligns vector to In-Phase axis."""
        self.log_divider("Phase Alignment Test")
        
        # Vector at 45 degrees: (1, 1). Magnitude = sqrt(2) ~= 1.414
        raw_sample = {
            "Ux In-Phase": 1.0, "Ux Quadrature": 1.0, 
            "Uy In-Phase": 0, "Uy Quadrature": 0,
            "Uz In-Phase": 0, "Uz Quadrature": 0,
        }
        
        # 1. Calibrate Phase
        self.log_interaction("Test", "CALIBRATE", "SignalPostProcessor", "Calibrate Phase Alignment", data=raw_sample)
        self.processor.calibrate_phase(raw_sample)
        
        # 2. Process same sample -> Should be (1.414, 0)
        self.log_interaction("Test", "PROCESS", "SignalPostProcessor", "Process Reference Sample", data=raw_sample)
        result = self.processor.process_sample(raw_sample)
        
        expected_mag = math.sqrt(2)
        self.log_interaction("Test", "ASSERT", "Result", "Check Ux In-Phase (Magnitude)", expect=str(expected_mag), got=result["Ux In-Phase"])
        self.assertAlmostEqual(result["Ux In-Phase"], expected_mag)
        
        self.log_interaction("Test", "ASSERT", "Result", "Check Ux Quadrature (Zero)", expect="0.0", got=result["Ux Quadrature"])
        self.assertAlmostEqual(result["Ux Quadrature"], 0.0)
        
        # 3. Process vector at 90 deg (0, 1) -> Should be rotated by -45 -> 45 deg
        self.log_divider("Test Rotated Sample")
        sample_90 = {
            "Ux In-Phase": 0.0, "Ux Quadrature": 1.0,
            "Uy In-Phase": 0, "Uy Quadrature": 0,
            "Uz In-Phase": 0, "Uz Quadrature": 0,
        }
        
        self.log_interaction("Test", "PROCESS", "SignalPostProcessor", "Process 90deg Sample", data=sample_90)
        res_90 = self.processor.process_sample(sample_90)
        
        expected_val = math.sqrt(2)/2
        self.log_interaction("Test", "ASSERT", "Result", "Check 45deg Result", expect=str(expected_val), got=res_90["Ux In-Phase"])
        self.assertAlmostEqual(res_90["Ux In-Phase"], expected_val)  # 0.707
        self.assertAlmostEqual(res_90["Ux Quadrature"], expected_val)

    def test_primary_field_subtraction(self):
        """Verify primary field tare works after other corrections."""
        self.log_divider("Primary Field Subtraction Test")
        
        # Scenario: pure offset of 5.0 on In-Phase
        base_sample = {
            "Ux In-Phase": 5.0, "Ux Quadrature": 0.0,
            "Uy In-Phase": 0, "Uy Quadrature": 0,
            "Uz In-Phase": 0, "Uz Quadrature": 0,
        }
        
        # 1. Calibrate Primary
        self.log_interaction("Test", "CALIBRATE", "SignalPostProcessor", "Null Primary Field", data=base_sample)
        self.processor.calibrate_primary(base_sample)
        
        # 2. Process 5.0 -> Should be 0.0
        self.log_interaction("Test", "PROCESS", "SignalPostProcessor", "Process Base Sample", data=base_sample)
        res = self.processor.process_sample(base_sample)
        
        self.log_interaction("Test", "ASSERT", "Result", "Check Zero Output", expect="0.0", got=res["Ux In-Phase"])
        self.assertAlmostEqual(res["Ux In-Phase"], 0.0)
        
        # 3. Process 7.0 -> Should be 2.0
        sample_7 = {
            "Ux In-Phase": 7.0, "Ux Quadrature": 0.0,
            "Uy In-Phase": 0, "Uy Quadrature": 0,
            "Uz In-Phase": 0, "Uz Quadrature": 0,
        }
        self.log_interaction("Test", "PROCESS", "SignalPostProcessor", "Process 7.0 Sample", data=sample_7)
        res_7 = self.processor.process_sample(sample_7)
        
        self.log_interaction("Test", "ASSERT", "Result", "Check Offset Output", expect="2.0", got=res_7["Ux In-Phase"])
        self.assertAlmostEqual(res_7["Ux In-Phase"], 2.0)

    def test_full_pipeline(self):
        """Test Noise -> Phase -> Primary chain."""
        self.log_divider("Full Processing Pipeline Test")
        
        # 1. Setup Noise: Offset (1, 1)
        noise_sample = {"Ux In-Phase": 1.0, "Ux Quadrature": 1.0, "Uy In-Phase":0, "Uy Quadrature":0, "Uz In-Phase":0, "Uz Quadrature":0}
        self.log_interaction("Test", "CALIBRATE", "SignalPostProcessor", "1. Zero Noise", data=noise_sample)
        self.processor.calibrate_noise(noise_sample)
        
        # 2. Setup Phase with Pre-Phase Sample (2, 2)
        # Raw (2,2) - Noise (1,1) = (1,1) (45 deg)
        pre_phase_sample = {"Ux In-Phase": 1.0, "Ux Quadrature": 1.0, "Uy In-Phase":0, "Uy Quadrature":0, "Uz In-Phase":0, "Uz Quadrature":0}
        self.log_interaction("Test", "CALIBRATE", "SignalPostProcessor", "2. Align Phase (using pre-phase sample)", data=pre_phase_sample)
        self.processor.calibrate_phase(pre_phase_sample)
        
        # 3. Setup Primary
        # Ref vector (2,2) -> Noise Corrected (1,1) -> Rotated (1.414, 0)
        fully_processed_ref = {"Ux In-Phase": math.sqrt(2), "Ux Quadrature": 0.0, "Uy In-Phase":0, "Uy Quadrature":0, "Uz In-Phase":0, "Uz Quadrature":0}
        self.log_interaction("Test", "CALIBRATE", "SignalPostProcessor", "3. Null Primary (using fully processed ref)", data=fully_processed_ref)
        self.processor.calibrate_primary(fully_processed_ref)
        
        # 4. Test a new point (3, 3)
        # Expected:
        # - Noise: (3,3)-(1,1) = (2,2)
        # - Phase: (2,2) rotated -45deg = (2.828, 0)
        # - Primary: (2.828, 0) - (1.414, 0) = (1.414, 0)
        
        input_sample = {
            "Ux In-Phase": 3.0, "Ux Quadrature": 3.0,
            "Uy In-Phase": 0, "Uy Quadrature": 0,
            "Uz In-Phase": 0, "Uz Quadrature": 0,
        }
        
        self.log_interaction("Test", "PROCESS", "SignalPostProcessor", "Process New Sample (3,3)", data=input_sample)
        final_result = self.processor.process_sample(input_sample)
        
        expected = math.sqrt(2)
        self.log_interaction("Test", "ASSERT", "Result", "Check Final Result", expect=str(expected), got=final_result["Ux In-Phase"])
        self.assertAlmostEqual(final_result["Ux In-Phase"], expected)
        self.assertAlmostEqual(final_result["Ux Quadrature"], 0.0)

    def test_phase_alignment_negative_signals(self):
        """Verify phase correction preserves sign of negative signals."""
        self.log_divider("Phase Alignment Sign Invariance Test")
        
        # Test 1: I negative, Q = 0 -> Should remain negative
        self.log_divider("Test 1: Negative I, Q=0")
        sample_neg_i = {
            "Ux In-Phase": -1.0, "Ux Quadrature": 0.0,
            "Uy In-Phase": 0, "Uy Quadrature": 0,
            "Uz In-Phase": 0, "Uz Quadrature": 0,
        }
        self.log_interaction("Test", "CALIBRATE", "SignalPostProcessor", "Calibrate Phase (negative I)", data=sample_neg_i)
        self.processor.calibrate_phase(sample_neg_i)
        
        result_neg_i = self.processor.process_sample(sample_neg_i)
        self.log_interaction("Test", "ASSERT", "Result", "Check Negative I Preserved", expect="-1.0", got=result_neg_i["Ux In-Phase"])
        self.assertAlmostEqual(result_neg_i["Ux In-Phase"], -1.0, msg="Negative I should remain negative")
        self.assertAlmostEqual(result_neg_i["Ux Quadrature"], 0.0, places=5)
        
        # Test 2: I = 0, Q negative -> Should give negative I after rotation
        self.log_divider("Test 2: I=0, Negative Q")
        self.processor.reset_calibration()
        sample_neg_q = {
            "Ux In-Phase": 0.0, "Ux Quadrature": -1.0,
            "Uy In-Phase": 0, "Uy Quadrature": 0,
            "Uz In-Phase": 0, "Uz Quadrature": 0,
        }
        self.log_interaction("Test", "CALIBRATE", "SignalPostProcessor", "Calibrate Phase (negative Q)", data=sample_neg_q)
        self.processor.calibrate_phase(sample_neg_q)
        
        result_neg_q = self.processor.process_sample(sample_neg_q)
        expected_mag = 1.0
        self.log_interaction("Test", "ASSERT", "Result", "Check Negative Q -> Negative I", expect=f"-{expected_mag}", got=result_neg_q["Ux In-Phase"])
        self.assertAlmostEqual(result_neg_q["Ux In-Phase"], -expected_mag, msg="Negative Q should result in negative I")
        self.assertAlmostEqual(result_neg_q["Ux Quadrature"], 0.0, places=5)
        
        # Test 3: I and Q both negative -> Should preserve sign of I
        self.log_divider("Test 3: Both I and Q Negative")
        self.processor.reset_calibration()
        sample_both_neg = {
            "Ux In-Phase": -1.0, "Ux Quadrature": -1.0,
            "Uy In-Phase": 0, "Uy Quadrature": 0,
            "Uz In-Phase": 0, "Uz Quadrature": 0,
        }
        self.log_interaction("Test", "CALIBRATE", "SignalPostProcessor", "Calibrate Phase (both negative)", data=sample_both_neg)
        self.processor.calibrate_phase(sample_both_neg)
        
        result_both_neg = self.processor.process_sample(sample_both_neg)
        expected_mag_both = math.sqrt(2)
        self.log_interaction("Test", "ASSERT", "Result", "Check Both Negative -> Negative I", expect=f"-{expected_mag_both}", got=result_both_neg["Ux In-Phase"])
        self.assertAlmostEqual(result_both_neg["Ux In-Phase"], -expected_mag_both, msg="Both negative should result in negative I")
        self.assertAlmostEqual(result_both_neg["Ux Quadrature"], 0.0, places=5)
        
        # Test 4: I positive, Q negative -> Should remain positive
        self.log_divider("Test 4: Positive I, Negative Q")
        self.processor.reset_calibration()
        sample_pos_neg = {
            "Ux In-Phase": 1.0, "Ux Quadrature": -1.0,
            "Uy In-Phase": 0, "Uy Quadrature": 0,
            "Uz In-Phase": 0, "Uz Quadrature": 0,
        }
        self.log_interaction("Test", "CALIBRATE", "SignalPostProcessor", "Calibrate Phase (positive I, negative Q)", data=sample_pos_neg)
        self.processor.calibrate_phase(sample_pos_neg)
        
        result_pos_neg = self.processor.process_sample(sample_pos_neg)
        expected_mag_pos_neg = math.sqrt(2)
        self.log_interaction("Test", "ASSERT", "Result", "Check Positive I Preserved", expect=str(expected_mag_pos_neg), got=result_pos_neg["Ux In-Phase"])
        self.assertAlmostEqual(result_pos_neg["Ux In-Phase"], expected_mag_pos_neg, msg="Positive I should remain positive")
        self.assertAlmostEqual(result_pos_neg["Ux Quadrature"], 0.0, places=5)
        
        # Test 5: Verify magnitude is preserved
        self.log_divider("Test 5: Magnitude Preservation")
        self.processor.reset_calibration()
        test_samples = [
            {"I": 2.0, "Q": 0.0, "expected_sign": 1},
            {"I": -2.0, "Q": 0.0, "expected_sign": -1},
            {"I": 0.0, "Q": 2.0, "expected_sign": 1},
            {"I": 0.0, "Q": -2.0, "expected_sign": -1},
            {"I": 3.0, "Q": 4.0, "expected_sign": 1},  # Magnitude = 5
            {"I": -3.0, "Q": -4.0, "expected_sign": -1},  # Magnitude = 5
        ]
        
        for test_case in test_samples:
            sample = {
                "Ux In-Phase": test_case["I"], "Ux Quadrature": test_case["Q"],
                "Uy In-Phase": 0, "Uy Quadrature": 0,
                "Uz In-Phase": 0, "Uz Quadrature": 0,
            }
            original_mag = math.sqrt(test_case["I"]**2 + test_case["Q"]**2)
            
            self.processor.reset_calibration()
            self.processor.calibrate_phase(sample)
            result = self.processor.process_sample(sample)
            
            result_mag = abs(result["Ux In-Phase"])
            expected_i = test_case["expected_sign"] * original_mag
            
            self.log_interaction("Test", "ASSERT", "Result", f"Magnitude preserved (I={test_case['I']}, Q={test_case['Q']})", 
                               expect=str(expected_i), got=result["Ux In-Phase"])
            self.assertAlmostEqual(result["Ux In-Phase"], expected_i, places=5, 
                                 msg=f"Magnitude should be preserved with correct sign for I={test_case['I']}, Q={test_case['Q']}")
            self.assertAlmostEqual(result_mag, original_mag, places=5, 
                                 msg=f"Magnitude should be preserved: {original_mag}")

if __name__ == "__main__":
    unittest.main()
