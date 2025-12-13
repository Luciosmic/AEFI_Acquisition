import sys
import os
import unittest
import time
# Add 'src' to sys.path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from tests_e2e.test_base_agent import DiagramFriendlyTest
from tests_e2e.e2e_test_environment import TestEnvironment

class TestSpeedIntegrationE2E(DiagramFriendlyTest):
    """
    E2E Integration Test verifying that Speed settings propagate 
    from UI -> Presenter -> ConfigService -> Hardware Provider.
    
    Uses pure Mock Infrastructure but wires the REAL Application Logic.
    """

    def test_verify_speed_integration(self):
        env = TestEnvironment()
        
        # 1. Setup - Bootstrap Application
        self.log_interaction("TestRunner", "CREATE", "TestEnvironment", "Bootstrapping Application")
        context = env.setup()
        
        # 2. Action - User starts scan with specific speed
        params = {
            "x_min": "0", "x_max": "10", "x_nb_points": "5",
            "y_min": "0", "y_max": "10", "y_nb_points": "5",
            "motion_speed_cm_s": "5.0" # Target value
        }
        
        self.log_interaction("User", "CALL", "ScanPresenter", "start_scan", data=params)
        context.presenter.start_scan(params)
        
        # 3. Assert - Check Configuration Provider applied value
        # Access the mock provider inside the service
        # We know structure: config_service -> adapters -> [0] is mock
        mock_provider = context.config_service._providers_by_id["mock_hardware"]
        
        self.log_interaction("TestRunner", "QUERY", "MockHardwareConfigProvider", "Get applied_hs")
        actual_speed = mock_provider.applied_hs
        
        self.log_interaction("TestRunner", "ASSERT", "MockHardwareConfigProvider", 
                           "Verify speed applied", expect=5.0, got=actual_speed)
        
        self.assertEqual(actual_speed, 5.0, "Speed should have been applied to Hardware Provider")
        
        # 4. Cleanup & Leakage Check
        self.log_interaction("TestRunner", "CALL", "TestEnvironment", "teardown")
        env.teardown()
        
        leakage_ok = env.check_leakages()
        self.log_interaction("TestRunner", "ASSERT", "TestEnvironment", "Check Leakages", expect=True, got=leakage_ok)
        self.assertTrue(leakage_ok, "Thread leakage detected!")

if __name__ == '__main__':
    unittest.main()
