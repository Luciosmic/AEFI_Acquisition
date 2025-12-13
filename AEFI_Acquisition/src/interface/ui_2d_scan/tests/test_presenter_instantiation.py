import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add src to sys.path
# Current file is in src/interface/ui_2d_scan/tests
# We want to add src to path
src_path = Path(__file__).resolve().parents[3]
print(f"Adding to path: {src_path}")
sys.path.append(str(src_path))

from interface.ui_2d_scan.presenter_2d_scan import ScanPresenter
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.hardware_configuration_service.hardware_configuration_service import HardwareConfigurationService

def test_instantiation():
    mock_scan_service = MagicMock(spec=ScanApplicationService)
    mock_hw_config_service = MagicMock(spec=HardwareConfigurationService)
    
    presenter = ScanPresenter(mock_scan_service, mock_hw_config_service)
    print("ScanPresenter instantiated successfully")
    assert presenter._hardware_config_service == mock_hw_config_service

if __name__ == "__main__":
    test_instantiation()
