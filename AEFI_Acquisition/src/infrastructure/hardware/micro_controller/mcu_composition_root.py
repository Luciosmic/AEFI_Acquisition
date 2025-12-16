"""
MCU Composition Root

Responsibility:
- Wire together the MCU driver (SerialCommunicator) and adapters (ADS131, Lifecycle, Continuous).
- Expose a unified entry point for the application to access MCU hardware capabilities.

Rationale:
- Simplifies main.py by encapsulating the wiring logic.
- Ensures consistent initialization of related components (shared communicator).
"""

import json
import os
from typing import Optional

from application.services.scan_application_service.i_acquisition_port import IAcquisitionPort
from application.services.system_lifecycle_service.i_hardware_initialization_port import IHardwareInitializationPort
from application.services.continuous_acquisition_service.i_continuous_acquisition_executor import IContinuousAcquisitionExecutor
from application.services.excitation_configuration_service.i_excitation_port import IExcitationPort
from domain.events.i_domain_event_bus import IDomainEventBus

from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator
from infrastructure.hardware.micro_controller.ads131a04.adapter_i_acquistion_port_ads131a04 import ADS131A04Adapter
from infrastructure.hardware.micro_controller.adapter_lifecycle_MCU import MCULifecycleAdapter
from infrastructure.hardware.micro_controller.ads131a04.adapter_i_continuous_acquisition_ads131a04 import AdapterIContinuousAcquisitionAds131a04
from infrastructure.hardware.micro_controller.ad9106.ad9106_controller import AD9106Controller
from infrastructure.hardware.micro_controller.ad9106.adapter_excitation_configuration_ad9106 import AdapterExcitationConfigurationAD9106
from infrastructure.hardware.micro_controller.ad9106.ad9106_advanced_configurator import AD9106AdvancedConfigurator
from application.services.hardware_configuration_service.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator


from infrastructure.hardware.micro_controller.ads131a04.ads131a04_advanced_configurator import ADS131A04AdvancedConfigurator
from infrastructure.hardware.micro_controller.mcu_advanced_configurator import MCUAdvancedConfigurator

class MCUCompositionRoot:
    """
    Composition Root for MCU hardware stack (ADS131A04 + AD9106 + Serial Communicator).
    
    Wires:
    - Driver: MCU_SerialCommunicator (shared by all adapters)
    - Adapters: 
      - ADS131A04Adapter (acquisition)
      - AdapterExcitationConfigurationAD9106 (excitation)
      - MCULifecycleAdapter (lifecycle)
      - AdapterIContinuousAcquisitionAds131a04 (continuous acquisition)
    """

    def __init__(self, event_bus: IDomainEventBus, port: str = "COM10", baudrate: int = 1500000):
        """
        Initialize the MCU hardware stack.

        Args:
            event_bus: Domain event bus (required for continuous acquisition)
            port: Serial port (e.g., 'COM10')
            baudrate: Serial baudrate
        """
        # 1. Instantiate Driver (Shared by all adapters)
        # Note: MCU_SerialCommunicator is a Singleton, but we can instantiate it.
        # Ideally we should use the instance.
        self._driver = MCU_SerialCommunicator()
        
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
        self.excitation: IExcitationPort = AdapterExcitationConfigurationAD9106(self._ad9106_controller, self._driver)
        
        # 3b. Instantiate AD9106 Configurator (Decoupled)
        self._ad9106_configurator = AD9106AdvancedConfigurator(self._ad9106_controller)
        
        # 3c. Instantiate MCU General Configurator
        self._mcu_configurator = MCUAdvancedConfigurator(self._driver)
        
        # 4. Instantiate Lifecycle Adapter
        # Injects the driver to manage connection
        self.lifecycle: IHardwareInitializationPort = MCULifecycleAdapter(
            port=port, 
            baudrate=baudrate, 
            communicator=self._driver
        )
        
        # 5. Instantiate Continuous Acquisition Executor
        # Injects event bus
        self.continuous: IContinuousAcquisitionExecutor = AdapterIContinuousAcquisitionAds131a04(event_bus)
        
        # 6. Load Configuration
        self._load_and_apply_config()
        
    def _load_and_apply_config(self) -> None:
        """Load configuration from JSON files and apply to adapters."""
        # Paths to atomic config files
        base_dir = os.path.dirname(__file__)
        
        # Defaults (Factory Settings)
        adc_default_path = os.path.join(base_dir, "ads131a04/ads131a04_default_config.json")
        dds_default_path = os.path.join(base_dir, "ad9106/ad9106_default_config.json")
        
        # User Config (Last Saved State)
        adc_user_path = os.path.join(base_dir, "ads131a04/ads131a04_last_config.json")
        dds_user_path = os.path.join(base_dir, "ad9106/ad9106_last_config.json")
        
        adc_config = {}
        dds_config = {}
        
        try:
            # 1. Load Defaults
            if os.path.exists(adc_default_path):
                with open(adc_default_path, 'r') as f:
                    adc_config = json.load(f)
            else:
                print(f"[MCUCompositionRoot] WARNING: Default ADC Config not found at {adc_default_path}")

            if os.path.exists(dds_default_path):
                with open(dds_default_path, 'r') as f:
                    dds_config = json.load(f)
            else:
                print(f"[MCUCompositionRoot] WARNING: Default DDS Config not found at {dds_default_path}")

            # 2. Load and Merge User Config
            if os.path.exists(adc_user_path):
                try:
                    with open(adc_user_path, 'r') as f:
                        user_adc = json.load(f)
                        # Simple update for now (could be deep merge if needed)
                        adc_config.update(user_adc)
                    print(f"[MCUCompositionRoot] Loaded User ADC Config")
                except Exception as e:
                    print(f"[MCUCompositionRoot] Failed to load User ADC Config: {e}")

            if os.path.exists(dds_user_path):
                try:
                    with open(dds_user_path, 'r') as f:
                        user_dds = json.load(f)
                        dds_config.update(user_dds)
                    print(f"[MCUCompositionRoot] Loaded User DDS Config")
                except Exception as e:
                    print(f"[MCUCompositionRoot] Failed to load User DDS Config: {e}")

            # 3. Combine for Lifecycle Adapter
            # Lifecycle adapter expects {"adc": ..., "dds": ...}
            combined_config = {
                "adc": adc_config,
                "dds": dds_config
            }
            self.lifecycle.set_config(combined_config)
            
            # 4. Apply to Acquisition Adapter (for internal state)
            if hasattr(self.acquisition, "load_config") and adc_config:
                self.acquisition.load_config(adc_config)
                
        except Exception as e:
            print(f"[MCUCompositionRoot] Failed to load config: {e}")

    @property
    def configurators(self) -> list[IHardwareAdvancedConfigurator]:
        """Return list of hardware components that support advanced configuration."""
        configs = []
        # Use the decoupled configurator for acquisition
        configs.append(self._acquisition_configurator)
        configs.append(self._ad9106_configurator)
        configs.append(self._mcu_configurator)
        return configs
