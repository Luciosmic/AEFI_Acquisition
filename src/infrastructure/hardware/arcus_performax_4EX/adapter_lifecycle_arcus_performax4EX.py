import logging
from typing import Optional, Any
from application.services.system_lifecycle_service.ports.i_hardware_initialization_port import IHardwareInitializationPort
from infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX import ArcusAdapter
from infrastructure.hardware.arcus_performax_4EX.driver_arcus_performax4EX import ArcusPerformax4EXController

logger = logging.getLogger(__name__)


class ArcusPerformaxLifecycleAdapter(IHardwareInitializationPort):
    """
    Lifecycle Adapter for Arcus Performax 4EX.
    
    Responsibility:
    - Manage the lifecycle (Coordinate connection, verification, close)
    - Transition the injected ArcusAdapter to a connected state.
    """
    
    def __init__(self, adapter: ArcusAdapter, controller: ArcusPerformax4EXController, port: Optional[str] = None):
        """
        Args:
            adapter: The ArcusAdapter instance to manage.
            controller: The controller to use for connection.
            port: Optional serial port (e.g. 'COM3').
        """
        self._adapter = adapter
        self._controller = controller
        self._port = port

    def initialize_all(self) -> dict:
        """
        Initialize the Arcus hardware.
        Connects the controller and enables the adapter.
        
        Returns:
            Dict of initialized resources.
        """
        logger.info("Connecting Arcus Performax 4EX (Port: %s)...", self._port)
        
        # 1. Connect Controller
        success = self._controller.connect(port=self._port)
        if not success:
            raise RuntimeError(f"Failed to connect to Arcus Stage")
            
        # 2. Inject Controller into Adapter
        self._adapter.set_controller(self._controller)
        
        # 3. Enable Adapter (Start Worker)
        self._adapter.enable()
        
        return {"arcus_adapter": self._adapter}
        
    def verify_all(self) -> bool:
        """
        Verify the controller answers, reading raw positions in pulses.

        Deliberately independent of the mm/pulse conversion: an uncalibrated
        transmission must not fail the startup (the operator calibrates it from
        the dashboard). A controller that does not answer still fails.

        Returns:
            True if verification succeeds.

        Raises:
            RuntimeError: If the controller is not connected or does not answer.
        """
        try:
            if not self._controller.is_connected():
                raise RuntimeError("controller not connected")
            pulses_x = self._controller.get_position("X")
            pulses_y = self._controller.get_position("Y")
        except Exception as e:
            raise RuntimeError(f"Verification failed: {e}")
        logger.info("Verification Success. Raw position: X=%s pulses, Y=%s pulses", pulses_x, pulses_y)
        if not self._adapter.is_conversion_available():
            logger.warning(
                "Arcus verified WITHOUT mm/pulse conversion: motion stays refused until the mechanical "
                "transmission is calibrated"
            )
        return True

    def close_all(self) -> None:
        """
        Close the connection.
        """
        logger.info("Closing Arcus connection...")
        self._adapter.disable()
        self._controller.disconnect()

