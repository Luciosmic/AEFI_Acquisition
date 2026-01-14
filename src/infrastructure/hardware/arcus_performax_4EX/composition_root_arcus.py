"""
Arcus Composition Root

Responsibility:
- Wire together the Arcus Performax 4EX driver and adapters.
- Expose a unified entry point for the application to access Arcus hardware capabilities.

Rationale:
- Simplifies main.py by encapsulating the wiring logic.
- Ensures consistent initialization of related components.
"""

from typing import Optional
from pathlib import Path

from application.services.motion_control_service.i_motion_port import IMotionPort
from application.services.system_lifecycle_service.i_hardware_initialization_port import IHardwareInitializationPort
from application.services.hardware_configuration_service.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator

from infrastructure.hardware.arcus_performax_4EX.driver_arcus_performax4EX import ArcusPerformax4EXController
from infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX import ArcusAdapter
from infrastructure.hardware.arcus_performax_4EX.adapter_lifecycle_arcus_performax4EX import ArcusPerformaxLifecycleAdapter
from infrastructure.hardware.arcus_performax_4EX.arcus_advanced_configuration import ArcusPerformax4EXAdvancedConfigurator
from domain.events.i_domain_event_bus import IDomainEventBus


class ArcusCompositionRoot:
    """
    Composition Root for Arcus Performax 4EX hardware stack.
    
    Wires:
    - Driver: ArcusPerformax4EXController
    - Adapters: ArcusAdapter, ArcusPerformaxLifecycleAdapter, ArcusPerformax4EXAdvancedConfigurator
    """

    def __init__(self, port: Optional[str] = None, dll_path: Optional[str] = None, event_bus: Optional[IDomainEventBus] = None):
        """
        Initialize the Arcus hardware stack.

        Args:
            port: Serial port (e.g., 'COM3'). If None, auto-detect.
            dll_path: Path to Arcus DLL files. If None, use default.
            event_bus: Domain event bus for publishing motion events.
        """
        # 1. Instantiate Driver (Private)
        # If dll_path is not provided, try to find it relative to this file
        if not dll_path:
            # Assuming DLL64 is in the same directory as this file
            dll_path = str(Path(__file__).parent / "DLL64")
            
        self._driver = ArcusPerformax4EXController(dll_path=dll_path)
        
        # 2. Instantiate Motion Adapter
        # We pass the event_bus to the adapter so it can publish events
        self.motion: ArcusAdapter = ArcusAdapter(event_bus=event_bus)
        # Note: Controller is injected by Lifecycle adapter during initialization
        
        # 3. Instantiate Lifecycle Adapter
        # Manages connection/disconnection via the Controller and enables/disables the Motion Adapter
        self.lifecycle: IHardwareInitializationPort = ArcusPerformaxLifecycleAdapter(self.motion, self._driver, port=port)
        
        # 4. Instantiate Configurator
        # Uses the same driver to apply configuration
        self.config: IHardwareAdvancedConfigurator = ArcusPerformax4EXAdvancedConfigurator(controller=self._driver)
