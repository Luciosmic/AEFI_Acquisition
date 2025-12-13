from typing import Dict, Any
import time
from application.services.system_lifecycle_service.i_hardware_initialization_port import IHardwareInitializationPort
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort

class MockHardwareInitializationPort(IHardwareInitializationPort):
    """
    Mock implementation of hardware initialization port.
    """
    
    def __init__(self):
        self.initialized = False
        self.closed = False
        
    def initialize_all(self) -> Dict[str, Any]:
        print("[MockHardwareInitializationPort] Initializing all hardware")
        self.initialized = True
        self.closed = False
        return {"mock_motion": MockMotionPort(), "mock_acquisition": MockAcquisitionPort()}
        
    def verify_all(self) -> bool:
        print("[MockHardwareInitializationPort] Verifying hardware")
        return True
        
    def close_all(self) -> None:
        print("[MockHardwareInitializationPort] Closing all hardware")
        self.initialized = False
        self.closed = True
