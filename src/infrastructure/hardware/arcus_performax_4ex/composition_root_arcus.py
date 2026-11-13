"""
Arcus Composition Root

Responsibility:
- Wire together the Arcus Performax 4EX driver and adapters.
- Expose a unified entry point for the application to access Arcus hardware capabilities.

Rationale:
- Simplifies main.py by encapsulating the wiring logic.
- Ensures consistent initialization of related components.
"""

import logging
from typing import Optional
from pathlib import Path

from application.test_bench_calibration.motion_control_service.ports.i_motion_port import IMotionPort
from application.shared.system_lifecycle_service.ports.i_hardware_initialization_port import IHardwareInitializationPort
from application.shared.hardware_configuration_service.ports.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator

from infrastructure.hardware.arcus_performax_4ex.driver_arcus_performax4ex import ArcusPerformax4EXController
from infrastructure.hardware.arcus_performax_4ex.adapter_motion_port_arcus_performax4ex.adapter_motion_port_arcus_performax4ex import ArcusAdapter
from infrastructure.hardware.arcus_performax_4ex.adapter_lifecycle_arcus_performax4ex.adapter_lifecycle_arcus_performax4ex import ArcusPerformaxLifecycleAdapter
from infrastructure.hardware.arcus_performax_4ex.adapter_raw_increment_motion_arcus.adapter_raw_increment_motion_arcus import ArcusRawIncrementMotionAdapter
from infrastructure.hardware.arcus_performax_4ex.adapter_position_increments_arcus.adapter_position_increments_arcus import ArcusPositionIncrementsAdapter
from infrastructure.hardware.arcus_performax_4ex.arcus_advanced_configuration.arcus_advanced_configuration import ArcusPerformax4EXAdvancedConfigurator
from domain.shared_kernel.events.i_domain_event_bus.i_domain_event_bus import IDomainEventBus

logger = logging.getLogger(__name__)


class ArcusCompositionRoot:
    """
    Composition Root for Arcus Performax 4EX hardware stack.
    
    Wires:
    - Driver: ArcusPerformax4EXController
    - Adapters: ArcusAdapter, ArcusPerformaxLifecycleAdapter, ArcusPerformax4EXAdvancedConfigurator
    """

    def __init__(
        self,
        port: Optional[str] = None,
        dll_path: Optional[str] = None,
        event_bus: Optional[IDomainEventBus] = None,
        controller: Optional[ArcusPerformax4EXController] = None,
    ):
        """
        Initialize the Arcus hardware stack.

        Args:
            port: Serial port (e.g., 'COM3'). If None, auto-detect.
            dll_path: Path to Arcus DLL files. If None, use default.
            event_bus: Domain event bus for publishing motion events.
            controller: Optional injected controller (e.g. FakeArcusPerformax4EXController
                for a simulated stack). Defaults to the real ArcusPerformax4EXController.
        """
        if controller is not None:
            self._driver = controller
            logger.info("Arcus composition root wired with injected controller %s", type(controller).__name__)
        else:
            # If dll_path is not provided, try to find it relative to this file
            if not dll_path:
                # Assuming DLL64 is in the same directory as this file
                dll_path = str(Path(__file__).parent / "DLL64")

            self._driver = ArcusPerformax4EXController(dll_path=dll_path)
            logger.info("Arcus composition root wired with real ArcusPerformax4EXController (port=%s, dll_path=%s)", port, dll_path)

        # 2. Instantiate Motion Adapter
        # We pass the event_bus to the adapter so it can publish events
        self.motion: ArcusAdapter = ArcusAdapter(event_bus=event_bus)
        # Note: Controller is injected by Lifecycle adapter during initialization
        
        # Same driver, motor increments without mm conversion (setpoints in increments)
        self.raw_increment_motion = ArcusRawIncrementMotionAdapter(self._driver)
        # The export's view of the same conversion: commanded and reported increments of each scan point
        self.position_increments = ArcusPositionIncrementsAdapter(self.motion)

        # 3. Instantiate Lifecycle Adapter
        # Manages connection/disconnection via the Controller and enables/disables the Motion Adapter
        self.lifecycle: IHardwareInitializationPort = ArcusPerformaxLifecycleAdapter(self.motion, self._driver, port=port)
        
        # 4. Instantiate Configurator
        # Uses the same driver to apply configuration
        self.config: IHardwareAdvancedConfigurator = ArcusPerformax4EXAdvancedConfigurator(controller=self._driver)
        logger.info(
            "Arcus hardware stack wired: motion=%s, lifecycle=%s, config=%s",
            type(self.motion).__name__,
            type(self.lifecycle).__name__,
            type(self.config).__name__,
        )
