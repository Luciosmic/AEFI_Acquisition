import sys
import os

# Adjust path to include src to allow imports
# We need 'src' in sys.path so 'from application...' works
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..", "src"))
sys.path.append(src_path)

from interface.ui_2d_scan.presenter_2d_scan import ScanPresenter
from application.hardware_configuration_service.hardware_configuration_service import HardwareConfigurationService
from infrastructure.tests.mock_ports import MockHardwareConfigProvider
from application.scan_application_service.scan_application_service import ScanApplicationService
from infrastructure.tests.mock_ports import MockMotionPort, MockAcquisitionPort, MockScanExecutor
from infrastructure.events.in_memory_event_bus import InMemoryEventBus

def verify_speed_integration():
    print("--- Verifying Speed Integration ---")
    
    # 1. Setup Infrastructure
    event_bus = InMemoryEventBus()
    motion_port = MockMotionPort()
    acquisition_port = MockAcquisitionPort()
    executor = MockScanExecutor()
    
    # 2. Setup Application Service
    scan_service = ScanApplicationService(motion_port, acquisition_port, event_bus, executor)
    
    # 3. Setup Hardware Configuration
    mock_provider = MockHardwareConfigProvider("mock_hardware")
    config_service = HardwareConfigurationService([mock_provider])
    
    # 4. Setup Presenter
    presenter = ScanPresenter(scan_service, config_service)
    
    # 5. Simulate Start Scan with Speed
    params = {
        "x_min": "0", "x_max": "10", "x_nb_points": "5",
        "y_min": "0", "y_max": "10", "y_nb_points": "5",
        "motion_speed_cm_s": "5.0" # Test Value cm/s
    }
    
    print(f"Starting scan with speed: {params['motion_speed_cm_s']} cm/s")
    presenter.start_scan(params)
    
    # 6. Verify Config Application
    # The MockProvider should have received the 'hs' value as-is (cm/s)
    # in a real scenario, the adapter converts it, but the config service passes it down.
    if mock_provider.applied_hs == 5.0:
        print("SUCCESS: Speed 5.0 cm/s was correctly applied to MockHardwareConfigProvider.")
    else:
        print(f"FAILURE: Expected applied_hs=5.0, got {mock_provider.applied_hs}")
        sys.exit(1)

if __name__ == "__main__":
    verify_speed_integration()
