import logging
from typing import Dict, Any
import time
from application.services.system_lifecycle_service.ports.i_hardware_initialization_port import IHardwareInitializationPort
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort

logger = logging.getLogger(__name__)

class MockHardwareInitializationPort(IHardwareInitializationPort):
    """
    Mock implementation of hardware initialization port.
    """
    
    def __init__(self):
        self.initialized = False
        self.closed = False
        
    def initialize_all(self) -> Dict[str, Any]:
        logger.info("initialize_all: Initializing all hardware")
        self.initialized = True
        self.closed = False
        return {"mock_motion": MockMotionPort(), "mock_acquisition": MockAcquisitionPort()}

    def verify_all(self) -> bool:
        logger.info("verify_all: Verifying hardware")
        return True

    def close_all(self) -> None:
        logger.info("close_all: Closing all hardware")
        self.initialized = False
        self.closed = True
