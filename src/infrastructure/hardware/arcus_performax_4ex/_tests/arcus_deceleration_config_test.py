import unittest
from unittest.mock import MagicMock
import sys
from pathlib import Path

# Ensure src is in path
src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from infrastructure.hardware.arcus_performax_4EX.adapter_arcus_speed_config import ArcusSpeedConfigAdapter
from infrastructure.hardware.arcus_performax_4EX.driver_arcus_performax4EX import ArcusPerformax4EXController

class TestArcusDecelerationConfig(unittest.TestCase):
    def setUp(self):
        self.mock_controller = MagicMock(spec=ArcusPerformax4EXController)
        self.adapter = ArcusSpeedConfigAdapter(self.mock_controller)

    def test_apply_config_full(self):
        # Arrange
        config = {
            "x_hs": 2000,
            "x_ls": 100,
            "x_acc": 400,
            "x_dec": 600
        }
        
        # Act
        self.adapter.apply_config(config)
        
        # Assert
        # Assert
        # Should call set_axis_params for X with all values
        self.mock_controller.set_axis_params.assert_any_call(
            "x", ls=100, hs=2000, acc=400, dec=600
        )
        # Should NOT call for Y since no Y params provided
        # (We can't easily check "not called for y" with assert_any_call, 
        # but we can check call_count or inspect call_args_list if needed.
        # For now, let's just verify X call is correct).

    def test_apply_config_partial(self):
        # Arrange
        config = {
            "hs": 1500,
            # No LS, ACC, DEC
        }
        
        # Act
        self.adapter.apply_config(config)
        
        # Assert
        # Should call for BOTH X and Y because 'hs' is global
        self.mock_controller.set_axis_params.assert_any_call(
            "x", ls=None, hs=1500, acc=None, dec=None
        )
        self.mock_controller.set_axis_params.assert_any_call(
            "y", ls=None, hs=1500, acc=None, dec=None
        )

if __name__ == '__main__':
    unittest.main()
