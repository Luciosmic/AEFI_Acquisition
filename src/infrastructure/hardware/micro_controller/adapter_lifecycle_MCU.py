import json
import logging
import os
from typing import Optional
from application.services.system_lifecycle_service.ports.i_hardware_initialization_port import IHardwareInitializationPort
from application.services.hardware_configuration_service.ports.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator
from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator
from infrastructure.hardware.micro_controller.ad9106.ad9106_advanced_configurator import AD9106AdvancedConfigurator
from infrastructure.hardware.micro_controller.ads131a04.ads131a04_advanced_configurator import ADS131A04AdvancedConfigurator

logger = logging.getLogger(__name__)


class MCULifecycleAdapter(IHardwareInitializationPort):
    """
    Lifecycle Adapter for the MCU (MicroController Unit).

    Responsibility:
    - Manage the lifecycle (Connect, Verify, Close) of the MCU Serial Communicator.
    - Acts as the 'plumbing' layer for MCU initialization.
    """

    def __init__(
        self,
        port: str = "COM10",
        baudrate: int = 9600,
        communicator: Optional[MCU_SerialCommunicator] = None,
        ad9106_configurator: Optional[IHardwareAdvancedConfigurator] = None,
        ads131a04_configurator: Optional[ADS131A04AdvancedConfigurator] = None,
    ):
        self._port_name = port
        self._baudrate = baudrate
        if communicator:
            self._communicator = communicator
        else:
            self._communicator = MCU_SerialCommunicator() # Singleton access
        self._config: Optional[dict] = None
        # DDS gain/phase/offset/frequency at startup are applied through the
        # same apply_config() the Hardware Advanced Config panel uses for a
        # manual "Apply" — single writer, so hardware writes and the
        # ExcitationFrequencyChanged/DdsChannelConfigChanged sync events
        # happen in exactly one place instead of two diverging ones.
        self._ad9106_configurator = ad9106_configurator
        self._ads131a04_configurator = ads131a04_configurator

    def set_config(self, config: dict) -> None:
        """Set configuration to be used during initialization."""
        self._config = config

    def initialize_all(self, config: Optional[dict] = None) -> dict:
        """
        Initialize the MCU connection and configure hardware settings.
        
        Args:
            config: Dictionary containing 'adc' and 'dds' configuration.
            
        Returns:
            Dict of initialized resources.
        """
        logger.info("Initializing MCU on %s...", self._port_name)
        success = self._communicator.connect(self._port_name, self._baudrate)
        if not success:
            raise RuntimeError(f"Failed to connect to MCU on port {self._port_name}")

        if config:
            # Override stored config if provided directly
            self._config = config

        if self._config:
            logger.info("Configuring hardware from JSON...")
            self._configure_hardware_from_json(self._config)
        else:
            logger.warning("No configuration provided. Using legacy defaults.")
            self._init_default_hardware_config()
        
        return {"mcu_communicator": self._communicator}

    def _configure_hardware_from_json(self, config: dict) -> None:
        """Apply configuration from JSON dictionary."""
        if "adc" in config:
            self._configure_adc(config["adc"])
        if "dds" in config:
            self._configure_dds(config["dds"])
        if "mcu" in config:
            self._configure_mcu(config["mcu"])
            
    def _configure_adc(self, adc_config: dict) -> None:
        """Delegate to ADS131A04AdvancedConfigurator.apply_persisted_config() —
        the single ADC writer shared with the panel's Apply: chip registers and
        the counts->V conversion come from the same values, and the register
        encoding lives only in ADS131Controller. persist=False: booting must not
        copy the resolved config into ads131a04_last_config.json."""
        if self._ads131a04_configurator is None:
            logger.warning("No ADS131A04 configurator injected — ADC config not applied at startup.")
            return
        self._ads131a04_configurator.apply_persisted_config(adc_config, persist=False)

    def _configure_dds(self, dds_config: dict) -> None:
        """Configure DDS registers.

        Frequency and channel 1-4 gain/phase/offset are delegated to
        AD9106AdvancedConfigurator.apply_config() (see below) — the same
        single writer the Hardware Advanced Config panel's manual "Apply"
        uses, so hardware writes and sync-event publication happen in one
        place. AC/DC mode registers stay a direct write here: they're not
        exposed in any panel, so there's no risk of a second reader/writer
        disagreeing about their value.
        """
        # 1. Modes
        # Legacy: 38 (DDS3+4), 39 (DDS1+2). Value 12593 means AC+AC.
        # 12593 = 0x3131. 0x31 = 49 (AC). 
        # So 12593 is AC(49) << 8 | AC(49).
        # We can implement parsing logic here or just use the legacy value if we trust the JSON to match.
        # But JSON has strings "AC+AC".
        mode_map = {"AC": 49, "DC": 1} # Simplified map based on legacy
        
        if "mode_dds1_dds2" in dds_config:
            mode_str = dds_config["mode_dds1_dds2"] # "AC+AC"
            parts = mode_str.split('+')
            if len(parts) == 2:
                m1 = mode_map.get(parts[0], 49)
                m2 = mode_map.get(parts[1], 49)
                # DDS1 is LSB?, DDS2 is MSB?
                # Legacy: 39 -> 12593. 12593 = 0x3131. Both are 0x31 (49).
                # So order doesn't matter for AC+AC.
                val = (m2 << 8) | m1
                self._write_register(39, val)
                
        if "mode_dds3_dds4" in dds_config:
            mode_str = dds_config["mode_dds3_dds4"]
            parts = mode_str.split('+')
            if len(parts) == 2:
                m3 = mode_map.get(parts[0], 49)
                m4 = mode_map.get(parts[1], 49)
                val = (m4 << 8) | m3
                self._write_register(38, val)

        # 2. Frequency + channel 1-4 gain/phase/offset: single writer
        flat_config = AD9106AdvancedConfigurator.nested_channels_to_flat_config(dds_config)
        if flat_config:
            if self._ad9106_configurator is not None:
                self._ad9106_configurator.apply_config(flat_config)
            else:
                logger.warning(
                    "No AD9106 configurator injected — "
                    "frequency/gain/phase/offset not applied at startup."
                )

    def _configure_mcu(self, mcu_config: dict) -> None:
        """Persist the resolved MCU config (currently just n_avg) back to
        mcu_last_config.json — the file ADS131A04Adapter.acquire_sample()
        reads live on every acquisition. There's no persistent register to
        write for n_avg, so this is the only "apply" step it needs, and it
        must happen here (at connect time) rather than at composition-root
        construction time so a mock/fake stack that never connects doesn't
        touch disk."""
        try:
            config_path = os.path.join(".aefi_acquisition", "configs", "mcu_last_config.json")
            with open(config_path, 'w') as f:
                json.dump(mcu_config, f, indent=4)
        except Exception:
            logger.exception("Failed to persist resolved MCU config")

    def _write_register(self, address: int, value: int) -> None:
        """Helper to write to a register."""
        success, response = self._communicator.send_command(f"a{address}")
        if not success:
            logger.warning("Failed to select address %s: %s", address, response)
            return

        success, response = self._communicator.send_command(f"d{value}")
        if not success:
            logger.warning("Failed to write value %s to address %s: %s", value, address, response)

    def _init_default_hardware_config(self) -> None:
        """
        Initialize MCU hardware with default configuration.
        
        Configures:
        - ADC: CLKIN divider (2), ICLK divider (2), OSR (32), Gains (0)
        - DDS: Frequency (1000 Hz), Modes (AC+AC), Gains (0 for DDS1/2, 10000 for DDS3/4)
        
        This matches the legacy init_default_config() behavior.
        """
        # Default configuration sequence (from legacy init_default_config)
        # Format: (address, value)
        params_default = [
            # ADC Configuration
            (13, 2),      # ADC: CLKIN_divider_ratio = 2
            (14, 32),     # ADC: ICLK_divider_ratio (2) + Oversampling_ratio (32) combined
            (17, 0),      # ADC: Gain_ADC_1 = 0
            (18, 0),      # ADC: Gain_ADC_2 = 0
            (19, 0),      # ADC: Gain_ADC_3 = 0
            (20, 0),      # ADC: Gain_ADC_4 = 0
            # DDS Configuration
            (63, 12583),  # DDS: Frequence_DDS (LSB) - corresponds to ~1000 Hz
            (62, 8),      # DDS: Frequence_DDS (MSB)
            (38, 12593),  # DDS: Mode DDS3+DDS4 (AC+AC)
            (39, 12593),  # DDS: Mode DDS1+DDS2 (AC+AC)
            (34, 0),      # DAC4DOF (Offset numérique DAC4)
            (35, 0),      # DAC3DOF (Offset numérique DAC3)
            (36, 0),      # DAC2DOF (Offset numérique DAC2)
            (37, 0),      # DAC1DOF (Offset numérique DAC1)
            (49, 0),      # DDS: Const_1
            (53, 0),      # DDS: Gain_1 (no excitation on startup)
            (67, 0),      # DDS: Phase_1
            (48, 0),      # DDS: Const_2
            (52, 0),      # DDS: Gain_2 (no excitation on startup)
            (66, 32768),  # DDS: Phase_2
            (47, 0),      # DDS: Const_3
            (51, 10000),  # DDS: Gain_3
            (65, 16384),  # DDS: Phase_3
            (46, 0),      # DDS: Const_4
            (50, 10000),  # DDS: Gain_4
            (64, 0),      # DDS: Phase_4
        ]
        
        for address, value in params_default:
            # Select register
            success, response = self._communicator.send_command(f"a{address}")
            if not success:
                logger.warning("Failed to select address %s: %s", address, response)
                continue

            # Write data
            success, response = self._communicator.send_command(f"d{value}")
            if not success:
                logger.warning("Failed to write value %s to address %s: %s", value, address, response)
                continue

        logger.info("Default hardware configuration applied successfully.")
        
    def verify_all(self) -> bool:
        """
        Verify connection by sending a simple ping or checking status.
        
        Returns:
            True if verification succeeds, False otherwise.
        """
        # We can try to send a dummy command or just check if open
        if not self._communicator.ser or not self._communicator.ser.is_open:
             raise RuntimeError("MCU Serial port is not open.")
             
        # Optional: Send a 'ping' command if supported.
        # For now, just checking the connection status is enough.
        logger.info("Verification Success. Connected to %s.", self._port_name)
        return True

    def close_all(self) -> None:
        """
        Close the connection.
        """
        logger.info("Closing MCU connection...")
        self._communicator.disconnect()

    def get_communicator(self) -> MCU_SerialCommunicator:
        """
        Retrieve the communicator instance.
        """
        return self._communicator
