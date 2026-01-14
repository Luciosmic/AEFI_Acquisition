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

if __name__ == "__main__":
    unittest.main()
