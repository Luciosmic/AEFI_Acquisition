from typing import List, Dict, Any
import json
import logging
import os
from dataclasses import replace

from application.services.hardware_configuration_service.ports.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator
from domain.shared_kernel.value_objects.hardware_configuration.hardware_advanced_parameter_schema import (
    HardwareAdvancedParameterSchema, NumberParameterSchema, EnumParameterSchema, BooleanParameterSchema
)
from infrastructure.hardware.micro_controller.ads131a04.adapter_i_acquistion_port_ads131a04 import ADS131A04Adapter

logger = logging.getLogger(__name__)

_CONFIGS_DIR = os.path.join(".aefi_acquisition", "configs")


def _parse_reference_voltage(value: Any) -> float:
    """UI enum ("2.442V"/"4.0V") or JSON float -> volts. The only two internal levels the chip offers."""
    volts = float(str(value).rstrip("V"))
    if volts not in (2.442, 4.0):
        raise ValueError(f"Unsupported ADS131A04 reference voltage: {value} (expected 2.442 or 4.0 V)")
    return volts


class ADS131A04AdvancedConfigurator(IHardwareAdvancedConfigurator):
    """
    Advanced Configurator for ADS131A04 ADC.

    Responsibility:
    - Expose hardware parameters to the UI.
    - Single writer of the ADC config: chip registers (via ADS131Controller, the only
      place that knows register bits) AND the adapter's counts->V conversion, from
      the same values — used by the panel's Apply and by MCULifecycleAdapter at boot.
    - Update configuration files.

    One name per setting, identical as UI key and JSON key (physical meaning, no
    register codes): negative_charge_pump, high_resolution, reference_voltage (V),
    reference_source ("Internal"/"External"), oversampling_ratio, clkin_divider,
    iclk_divider, channels.N.gain.
    """

    # ADS131A04 specifications (from datasheet)
    # Digital Gain values: Register ADCx bits [2:0] map to gains 1, 2, 4, 8, 16
    # See datasheet section 9.6.2 ADCx: ADC Channel Digital Gain Configuration Registers
    AVAILABLE_GAINS = [1, 2, 4, 8, 16]

    # OSR (Oversampling Ratio) values: Register MODE bits OSR[3:0] map to OSR values
    # See datasheet Table 30. Data Rate Settings (section 9.4 Device Functional Modes)
    # OSR determines data rate: Data Rate = fMOD / OSR
    # Values from datasheet Table 30 (ordered by OSR code 0000 to 1111):
    AVAILABLE_OSR = [4096, 2048, 1024, 800, 768, 512, 400, 384, 256, 200, 192, 128, 96, 64, 48, 32]

    # CLK_DIV and ICLK_DIV divider ratios (from datasheet register maps)
    # CLK_DIV[2:0] (bits 3:1 of CLKIN register): 2, 4, 6, 8, 10, 12, 14
    # ICLK_DIV[2:0] (bits 7:5 of MODE register): 2, 4, 6, 8, 10, 12, 14
    AVAILABLE_CLK_DIV = [2, 4, 6, 8, 10, 12, 14]
    AVAILABLE_ICLK_DIV = [2, 4, 6, 8, 10, 12, 14]

    def __init__(self, adapter: ADS131A04Adapter, controller: Any):
        self._adapter = adapter
        self._controller = controller

    @property
    def hardware_id(self) -> str:
        return "ads131a04"

    @property
    def display_name(self) -> str:
        return "ADS131A04 ADC"

    @staticmethod
    def get_parameter_specs() -> List[HardwareAdvancedParameterSchema]:
        specs = []

        # Global Settings - A_SYS_CFG Register (Address 11)
        # Reference Configuration (from datasheet Table 25. A_SYS_CFG Register)

        specs.append(BooleanParameterSchema(
            key="negative_charge_pump",
            display_name="Negative Charge Pump (VNCPEN)",
            description="Enable negative charge pump for 3.0-V to 3.45-V unipolar power supply. Bit 7 of A_SYS_CFG register.",
            default_value=False,
            group="Reference Configuration"
        ))

        specs.append(BooleanParameterSchema(
            key="high_resolution",
            display_name="High Resolution Mode (HRM)",
            description="High-resolution mode (better accuracy) or Low-power mode (lower power consumption). Bit 6 of A_SYS_CFG register. Affects available fMOD values.",
            default_value=True,
            group="Reference Configuration"
        ))

        specs.append(EnumParameterSchema(
            key="reference_voltage",
            display_name="Reference Voltage Level (VREF_4V)",
            description="REFP reference voltage level when using internal reference. Bit 4 of A_SYS_CFG register. 4.0 V requires a 5-V analog supply.",
            default_value="2.442V",
            choices=("2.442V", "4.0V"),
            group="Reference Configuration"
        ))

        specs.append(EnumParameterSchema(
            key="reference_source",
            display_name="Reference Source (INT_REFEN)",
            description="Internal or external reference voltage. Bit 3 of A_SYS_CFG register.",
            default_value="Internal",
            choices=("External", "Internal"),
            group="Reference Configuration"
        ))

        specs.append(EnumParameterSchema(
            key="oversampling_ratio",
            display_name="Oversampling Ratio (OSR)",
            description="Determines data rate and noise performance",
            default_value="4096",
            choices=tuple(str(x) for x in ADS131A04AdvancedConfigurator.AVAILABLE_OSR),
            group="Global"
        ))

        # Channel Settings
        # System has 2 ADS131A04 ADCs (4 channels each = 8 total)
        # Gains are configured per register (1-4), which affects the corresponding channel on BOTH ADCs.
        # So we have 4 Gain Groups (Pairs).

        for pair_idx in range(1, 5):
            specs.append(EnumParameterSchema(
                key=f"gain_pair_{pair_idx}",
                display_name=f"Gain ADC {pair_idx}",
                description=f"Gain for Channel {pair_idx} (ADC1) and Channel {pair_idx} (ADC2)",
                default_value="1",
                choices=tuple(str(x) for x in ADS131A04AdvancedConfigurator.AVAILABLE_GAINS),
                group=f"Gain Configuration"
            ))

        # Load default config if exists
        updated_specs = []
        try:
            config_path = os.path.join(_CONFIGS_DIR, "ads131a04_default_config.json")
            default_config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    default_config = json.load(f)

            for spec in specs:
                new_default = spec.default_value

                # Same key in UI and JSON — only the enum display format differs
                if spec.key in default_config:
                    val = default_config[spec.key]
                    if spec.key == "reference_voltage":
                        new_default = f"{_parse_reference_voltage(val)}V"
                    elif spec.key == "oversampling_ratio":
                        new_default = str(val)
                    else:
                        new_default = val

                # Special mapping for Gain Pairs: pair N <- channel N
                if spec.key.startswith("gain_pair_"):
                    ch_key = spec.key.split("_")[-1]
                    if "channels" in default_config and ch_key in default_config["channels"]:
                        new_default = str(default_config["channels"][ch_key].get("gain", 1))

                if new_default != spec.default_value:
                    updated_specs.append(replace(spec, default_value=new_default))
                else:
                    updated_specs.append(spec)

        except Exception:
            logger.exception("Failed to load default config")
            return specs

        return updated_specs

    def reset_to_default(self) -> None:
        """Discard the current applied state and re-apply the saved default.
        get_parameter_specs() here reads only the default file (no
        default+last resolution for this hardware yet), so its default_value
        already IS the pure default — safe to feed straight into apply_config()."""
        flat_config = {spec.key: spec.default_value for spec in self.get_parameter_specs()}
        self.apply_config(flat_config)

    @staticmethod
    def _to_persisted_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Flat UI config (enum strings, gain_pair_N) -> persisted JSON shape (same names, physical values)."""
        gains = {pair_idx: int(config.get(f"gain_pair_{pair_idx}", 1)) for pair_idx in range(1, 5)}
        return {
            "clkin_divider": 2,  # Fixed for now
            "iclk_divider": 2,  # Fixed for now
            "oversampling_ratio": int(config.get("oversampling_ratio", 4096)),
            "negative_charge_pump": bool(config.get("negative_charge_pump", False)),
            "high_resolution": bool(config.get("high_resolution", True)),
            "reference_voltage": _parse_reference_voltage(config.get("reference_voltage", "2.442V")),
            "reference_source": config.get("reference_source", "Internal"),
            # Logical channel N and N+4 (ADC1/ADC2) share gain register N
            "channels": {
                str(ch): {"gain": gains[ch if ch <= 4 else ch - 4], "enabled": True}
                for ch in range(1, 9)
            },
        }

    def apply_config(self, config: Dict[str, Any], persist: bool = True) -> None:
        """
        Apply advanced configuration (panel's Apply).

        Args:
            config: Flat dictionary of values keyed by parameter key.
            persist: write the result to ads131a04_last_config.json.
        """
        self.apply_persisted_config(self._to_persisted_config(config), persist=persist)

    def apply_persisted_config(self, adc_config: Dict[str, Any], persist: bool = False) -> None:
        """
        Single writer: chip registers + adapter conversion from the same values.

        Called with persist=False by MCULifecycleAdapter at boot — rewriting
        last_config on every boot would let it mask any later edit of the default.
        """
        # Missing keys fall back to the same defaults as the panel
        adc_config = {**self._to_persisted_config({}), **adc_config}
        adc_config["reference_voltage"] = _parse_reference_voltage(adc_config["reference_voltage"])
        logger.info(
            "ADS131A04: Command apply config (reference_voltage=%sV, reference_source=%s, oversampling_ratio=%s, persist=%s)",
            adc_config["reference_voltage"], adc_config["reference_source"], adc_config["oversampling_ratio"], persist,
        )

        writes = {
            "clkin_divider": self._controller.set_clkin_divider(int(adc_config["clkin_divider"])),
            "iclk_divider/oversampling_ratio": self._controller.set_iclk_divider_and_oversampling(
                int(adc_config["iclk_divider"]), int(adc_config["oversampling_ratio"])
            ),
            "reference": self._controller.set_reference_config(
                negative_charge_pump=bool(adc_config["negative_charge_pump"]),
                high_resolution=bool(adc_config["high_resolution"]),
                reference_voltage=adc_config["reference_voltage"],
                internal_reference=adc_config["reference_source"] == "Internal",
            ),
        }
        for pair_idx in range(1, 5):
            gain = int(adc_config["channels"].get(str(pair_idx), {}).get("gain", 1))
            writes[f"gain_pair_{pair_idx}"] = self._controller.set_channel_gain(pair_idx, gain)
        for setting, (success, msg) in writes.items():
            if not success:
                logger.warning("ADS131A04: failed to write %s to chip: %s", setting, msg)

        self._adapter.load_config(adc_config)

        if persist:
            self._write_json("ads131a04_last_config.json", adc_config)

    def save_config_as_default(self, config: Dict[str, Any]) -> None:
        """
        Save configuration as default.
        """
        self._write_json("ads131a04_default_config.json", self._to_persisted_config(config), raise_on_error=True)

    @staticmethod
    def _write_json(filename: str, data: Dict[str, Any], raise_on_error: bool = False) -> None:
        config_path = os.path.join(_CONFIGS_DIR, filename)
        try:
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=4)
            logger.info("Config saved to %s", config_path)
        except Exception:
            logger.exception("Failed to save config to %s", config_path)
            if raise_on_error:
                raise
