from typing import Optional, Any
from application.services.system_lifecycle_service.i_hardware_initialization_port import IHardwareInitializationPort
from infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX import ArcusAdapter
from infrastructure.hardware.arcus_performax_4EX.driver_arcus_performax4EX import ArcusPerformax4EXController

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
        print(f"[ArcusLifecycle] Connecting Arcus Performax 4EX (Port: {self._port})...")
        
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
        Verify connection by checking motion status or reading position.
        
        Returns:
            True if verification succeeds, False otherwise.
        """
        try:
            pos = self._adapter.get_current_position()
            print(f"[ArcusLifecycle] Verification Success. Current Position: {pos}")
            return True
        except Exception as e:
            raise RuntimeError(f"Verification failed: {e}")

    def close_all(self) -> None:
        """
        Close the connection.
        """
        print("[ArcusLifecycle] Closing Arcus connection...")
        self._adapter.disable()
        self._controller.disconnect()

