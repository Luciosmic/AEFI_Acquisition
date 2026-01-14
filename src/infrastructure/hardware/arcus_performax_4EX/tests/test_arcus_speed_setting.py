import unittest
from unittest.mock import MagicMock
import sys
from pathlib import Path

# Ensure src is in path
src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX import ArcusAdapter

class TestArcusSpeedSetting(unittest.TestCase):
    def setUp(self):
        self.adapter = ArcusAdapter()
        # Mock the controller/stage
        self.mock_stage = MagicMock()
        self.adapter._stage = self.mock_stage
        
        # Constants
        self.STEPS_PER_CM = 10000.0 / 43.6 # 1/0.00436

    def test_speed_conversion_6_54(self):
        # Arrange
        target_speed_cm_s = 6.54
        
        # Expected Hz: 6.54 * (1 / 0.00436) = 6.54 * 229.357... = 1499.99... -> 1500
        expected_hz = 1500 
        
        # Act
        self.adapter.set_speed(target_speed_cm_s)
        
        # Assert
        # Check if it was called with something close to 1500
        # Since we can't easily check exact integer match if calculation varies slightly,
        # we'll capture the call args.
        
        calls = self.mock_stage.query.call_args_list
        self.assertTrue(len(calls) >= 2)
        
        # Parse the calls to verify value
        # Call format: query("HSX=1500")
        
        found_x = False
        found_y = False
        
        for call in calls:
            arg = call[0][0] # first arg
            if arg.startswith("HSX="):
                val = int(arg.split("=")[1])
                self.assertAlmostEqual(val, expected_hz, delta=1)
                found_x = True
            elif arg.startswith("HSY="):
                val = int(arg.split("=")[1])
                self.assertAlmostEqual(val, expected_hz, delta=1)
                found_y = True
                
        self.assertTrue(found_x, "Did not find HSX command")
        self.assertTrue(found_y, "Did not find HSY command")

if __name__ == '__main__':
    unittest.main()
