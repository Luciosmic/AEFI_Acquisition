"""
MCU Composition Root

Responsibility:
- Wire together the MCU driver (SerialCommunicator) and adapters (ADS131, Lifecycle, Continuous).
- Expose a unified entry point for the application to access MCU hardware capabilities.

Rationale:
- Simplifies main.py by encapsulating the wiring logic.
- Ensures consistent initialization of related components (shared communicator).
"""

import logging
import os
from typing import Optional

from application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort
from application.services.system_lifecycle_service.ports.i_hardware_initialization_port import IHardwareInitializationPort
from application.services.aefi_acquisition_service.ports.i_aefi_acquisition_executor import IAefiAcquisitionExecutor
from application.services.excitation_configuration_service.ports.i_excitation_port import IExcitationPort
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator
from infrastructure.hardware.micro_controller.ads131a04.adapter_i_acquistion_port_ads131a04 import ADS131A04Adapter
from infrastructure.hardware.micro_controller.adapter_lifecycle_MCU import MCULifecycleAdapter
from infrastructure.hardware.micro_controller.ads131a04.adapter_aefi_acquisition_ads131a04 import AdapterAefiAcquisitionAds131a04
from infrastructure.hardware.micro_controller.ad9106.ad9106_controller import AD9106Controller
from infrastructure.hardware.micro_controller.ad9106.adapter_excitation_configuration_ad9106 import AdapterExcitationConfigurationAD9106
from infrastructure.hardware.micro_controller.ad9106.ad9106_advanced_configurator import AD9106AdvancedConfigurator
from application.services.hardware_configuration_service.ports.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator


from infrastructure.hardware.micro_controller.ads131a04.ads131a04_advanced_configurator import ADS131A04AdvancedConfigurator
from infrastructure.hardware.micro_controller.mcu_advanced_configurator import MCUAdvancedConfigurator
from infrastructure.hardware.micro_controller.hardware_config_resolution import (
    load_json_if_exists,
    resolve_config,
)

logger = logging.getLogger(__name__)


class MCUCompositionRoot:
    """
    Composition Root for MCU hardware stack (ADS131A04 + AD9106 + Serial Communicator).
    
    Wires:
    - Driver: MCU_SerialCommunicator (shared by all adapters)
    - Adapters: 
      - ADS131A04Adapter (acquisition)
      - AdapterExcitationConfigurationAD9106 (excitation)
      - MCULifecycleAdapter (lifecycle)
      - AdapterAefiAcquisitionAds131a04 (continuous acquisition)
    """

    def __init__(self, event_bus: IDomainEventBus, port: str = "COM10", baudrate: int = 1500000, communicator=None):
        """
        Initialize the MCU hardware stack.

        Args:
            event_bus: Domain event bus (required for continuous acquisition)
            port: Serial port (e.g., 'COM10')
            baudrate: Serial baudrate
            communicator: Optional injected transport (e.g. FakeMCUSerialCommunicator
                for a simulated stack). Defaults to the real MCU_SerialCommunicator.
        """
        # 1. Instantiate Driver (Shared by all adapters)
        # Note: MCU_SerialCommunicator is a Singleton, but we can instantiate it.
        # Ideally we should use the instance.
        self._driver = communicator if communicator is not None else MCU_SerialCommunicator()
        
        # 2. Instantiate Acquisition Adapter
        # Injects the driver
        self.acquisition: IAcquisitionPort = ADS131A04Adapter(self._driver)
        
        # 2b. Instantiate Acquisition Controller (for low-level config)
        from infrastructure.hardware.micro_controller.ads131a04.ads131_controller import ADS131Controller
        self._ads131_controller = ADS131Controller(self._driver)
        
        # 2c. Instantiate Acquisition Configurator (Decoupled)
        self._acquisition_configurator = ADS131A04AdvancedConfigurator(self.acquisition, self._ads131_controller)
        
        # 3. Instantiate AD9106 Controller and Adapter (Excitation)
        # Controller uses the shared driver
        self._ad9106_controller = AD9106Controller(self._driver)
        self.excitation: IExcitationPort = AdapterExcitationConfigurationAD9106(
            self._ad9106_controller, self._driver, event_bus=event_bus
        )
        
        # 3b. Instantiate AD9106 Configurator (Decoupled)
        self._ad9106_configurator = AD9106AdvancedConfigurator(self._ad9106_controller, event_bus)
        
        # 3c. Instantiate MCU General Configurator
        self._mcu_configurator = MCUAdvancedConfigurator(self._driver)
        
        # 4. Instantiate Lifecycle Adapter
        # Injects the driver to manage connection
        self.lifecycle: IHardwareInitializationPort = MCULifecycleAdapter(
            port=port,
            baudrate=baudrate,
            communicator=self._driver,
            ad9106_configurator=self._ad9106_configurator,
            ads131a04_configurator=self._acquisition_configurator,
        )
        
        # 5. Instantiate Continuous Acquisition Executor
        # Injects event bus
        self.continuous: IAefiAcquisitionExecutor = AdapterAefiAcquisitionAds131a04(event_bus)
        
        # 6. Load Configuration
        self._load_and_apply_config()
        
    def _load_and_apply_config(self) -> None:
        """Resolve each hardware's default+last config in memory and hand the
        result to the Lifecycle Adapter — no disk writes here. Actual hardware
        application (and, for MCU, persisting the resolved n_avg back to
        mcu_last_config.json) happens later, inside MCULifecycleAdapter, only
        once initialize_all() actually connects."""
        configs_dir = os.path.join(".aefi_acquisition", "configs")

        try:
            adc_config = resolve_config(
                load_json_if_exists(os.path.join(configs_dir, "ads131a04_default_config.json")),
                load_json_if_exists(os.path.join(configs_dir, "ads131a04_last_config.json")),
            )
            dds_config = resolve_config(
                load_json_if_exists(os.path.join(configs_dir, "ad9106_default_config.json")),
                load_json_if_exists(os.path.join(configs_dir, "ad9106_last_config.json")),
            )
            # MCU config has no hardware register to write at startup — n_avg
            # is re-read live from mcu_last_config.json on every
            # acquire_sample() call. Resolving it here just means the
            # lifecycle adapter will persist this resolved value back to that
            # file once it connects (see MCULifecycleAdapter._configure_mcu).
            mcu_config = resolve_config(
                load_json_if_exists(os.path.join(configs_dir, "mcu_default_config.json")),
                load_json_if_exists(os.path.join(configs_dir, "mcu_last_config.json")),
            )

            self.lifecycle.set_config({"adc": adc_config, "dds": dds_config, "mcu": mcu_config})

            # Apply to Acquisition Adapter (for internal state)
            if hasattr(self.acquisition, "load_config") and adc_config:
                self.acquisition.load_config(adc_config)

        except Exception:
            logger.exception("Failed to load config")

    @property
    def configurators(self) -> list[IHardwareAdvancedConfigurator]:
        """Return list of hardware components that support advanced configuration."""
        configs = []
        # Use the decoupled configurator for acquisition
        configs.append(self._acquisition_configurator)
        configs.append(self._ad9106_configurator)
        configs.append(self._mcu_configurator)
        return configs

    @property
    def ad9106_controller(self) -> AD9106Controller:
        """Read-only access to the shared AD9106Controller — lets main.py wire
        AdapterSynchronousDetectionAD9106 without reaching into a private attribute."""
        return self._ad9106_controller

    @property
    def ad9106_configurator(self) -> AD9106AdvancedConfigurator:
        """Read-only access to the shared AD9106AdvancedConfigurator — same
        rationale as ad9106_controller above."""
        return self._ad9106_configurator
