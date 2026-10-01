"""
AD9106 Advanced Configurator - Infrastructure Layer

Responsibility:
- Implement IHardwareAdvancedConfigurator interface
- Expose low-level AD9106 configuration (Gains, Phases, Offsets) for manual tuning
- Save/Load last configuration

Rationale:
- Extracted from AD9106Adapter to separate concerns (SRP).
- The Adapter focuses on Domain -> Hardware translation (Excitation).
- The Configurator focuses on User -> Hardware tuning (Advanced Config).
"""

from typing import List, Dict, Any, Optional
import json
import logging
import os
from dataclasses import replace

from application.services.hardware_configuration_service.ports.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator
from domain.shared_kernel.value_objects.hardware_configuration.hardware_advanced_parameter_schema import (
    HardwareAdvancedParameterSchema, NumberParameterSchema, BooleanParameterSchema
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.excitation.events.excitation_frequency_changed.excitation_frequency_changed import (
    ExcitationFrequencyChanged,
)
from domain.shared_kernel.excitation.events.dds_channel_config_changed.dds_channel_config_changed import (
    DdsChannelConfigChanged,
)
from domain.shared_kernel.excitation.events.excitation_dds_link_changed.excitation_dds_link_changed import (
    ExcitationDdsLinkChanged,
)
from domain.shared_kernel.excitation.value_objects.phase_angle import PhaseAngle
from infrastructure.hardware.micro_controller.ad9106.ad9106_controller import AD9106Controller
from infrastructure.hardware.micro_controller.hardware_config_resolution import (
    load_json_if_exists,
    resolve_config,
)

EXCITATION_FREQUENCY_CHANGED_TOPIC = "excitationfrequencychanged"
DDS_CHANNEL_CONFIG_CHANGED_TOPIC = "ddschannelconfigchanged"
EXCITATION_DDS_LINK_CHANGED_TOPIC = "excitationddslinkchanged"
# Separate topic (channels 3/4 — synchronous detection reference, NOT
# excitation) — deliberately NOT the same topic as DDS_CHANNEL_CONFIG_CHANGED_TOPIC:
# ExcitationConfigurationService._on_dds_channel_config_changed treats any
# channel != 1 as channel 2 (DDS1/DDS2 excitation pairing), so publishing
# ch3/ch4 there would corrupt its excitation-mode/level state.
DDS_SYNCHRONOUS_DETECTION_CHANNEL_CHANGED_TOPIC = "ddssynchronousdetectionchannelchanged"

logger = logging.getLogger(__name__)


class AD9106AdvancedConfigurator(IHardwareAdvancedConfigurator):
    """
    Advanced Configurator for AD9106 DDS hardware.
    Allows manual tuning of registers via the UI.
    """

    def __init__(self, controller: AD9106Controller, event_bus: IDomainEventBus):
        """
        Initialize configurator with shared controller.

        Args:
            controller: AD9106Controller instance (shared with Adapter).
            event_bus: Domain event bus — publishes ExcitationFrequencyChanged so the
                Excitation tab (and its subscribers) stay in sync when frequency is
                changed from this Advanced Config tab instead. Also publishes
                DdsChannelConfigChanged for channels 1/2 (gain/phase) — same event
                AdapterExcitationConfigurationAD9106 publishes in the other
                direction — so ExcitationConfigurationService can detect a
                non-standard phase pair and fall back to ExcitationMode.CUSTOM.
        """
        self._controller = controller
        self._event_bus = event_bus
        self._last_published_frequency_hz: Optional[float] = None
        self._last_published_channel_config: Dict[int, tuple] = {}
        self._last_published_link: Optional[bool] = None
        self._last_published_synchronous_channel_config: Dict[int, tuple] = {}

    @property
    def hardware_id(self) -> str:
        return "ad9106_dds"

    @property
    def display_name(self) -> str:
        return "AD9106 DDS"

    @staticmethod
    def get_parameter_specs() -> List[HardwareAdvancedParameterSchema]:
        specs = []
        
        # Global Settings
        specs.append(NumberParameterSchema(
            key="frequency_hz",
            display_name="Frequency",
            description="DDS Output Frequency",
            default_value=1000.0,
            min_value=0.1,
            max_value=8000000.0, # 8 MHz
            unit="Hz",
            group="Global"
        ))

        specs.append(BooleanParameterSchema(
            key="link_dds1_dds2",
            display_name="Link DDS1-DDS2",
            description="Keep DDS1 and DDS2 gain equal (mirrors the Excitation panel's "
                         "\"Link S1-S2 = S3-S4\") — changing one from either panel updates the other.",
            default_value=True,
            group="Global"
        ))

        # Channel Settings (Restricted to DDS1 and DDS2 as per requirements)
        # Channel Settings (Expanded to all 4 channels)
        for ch in range(1, 5):
            default_gain = 0.0
            if ch in [3, 4]:
                default_gain = 10000.0 # Default gain for Ch 3/4 to match controller default

            specs.append(NumberParameterSchema(
                key=f"ch{ch}_gain",
                display_name=f"DDS {ch} Gain",
                description=f"Digital Gain for DDS {ch}",
                default_value=default_gain,
                min_value=0.0,
                max_value=16376.0,
                group=f"DDS {ch}"
            ))
            specs.append(NumberParameterSchema(
                key=f"ch{ch}_phase",
                display_name=f"DDS {ch} Phase",
                description=f"Phase Offset for DDS {ch}",
                default_value=0.0,
                min_value=0.0,
                max_value=65535.0,
                group=f"DDS {ch}"
            ))
            specs.append(NumberParameterSchema(
                key=f"ch{ch}_offset",
                display_name=f"DDS {ch} Offset",
                description=f"DC Offset for DDS {ch}",
                default_value=0.0,
                min_value=0.0,
                max_value=65535.0,
                group=f"DDS {ch}"
            ))
            


        # Resolve default+last config so the panel shows what's actually
        # applied (last_config.json is only ever written by apply_config()),
        # not just the factory default.
        updated_specs = []
        try:
            default_path = os.path.join(".aefi_acquisition", "configs", "ad9106_default_config.json")
            last_path = os.path.join(".aefi_acquisition", "configs", "ad9106_last_config.json")
            default_config = resolve_config(load_json_if_exists(default_path), load_json_if_exists(last_path))

            for spec in specs:
                new_default = spec.default_value
                
                # Global
                if spec.key == "frequency_hz" and "frequency_hz" in default_config:
                    new_default = default_config["frequency_hz"]
                if spec.key == "link_dds1_dds2" and "link_dds1_dds2" in default_config:
                    new_default = bool(default_config["link_dds1_dds2"])

                # Channels
                if spec.key.startswith("ch"):
                    # Parse key: ch{ch}_{param}
                    parts = spec.key.split("_")
                    if len(parts) >= 2:
                        ch_str = parts[0][2:] # "1" from "ch1"
                        param = parts[1] # "gain", "phase", "offset"
                        
                        if "channels" in default_config and ch_str in default_config["channels"]:
                            ch_config = default_config["channels"][ch_str]
                            if param in ch_config:
                                new_default = float(ch_config[param])
                
                if new_default != spec.default_value:
                    updated_specs.append(replace(spec, default_value=new_default))
                else:
                    updated_specs.append(spec)
                                    
        except Exception:
            logger.exception("Failed to load default config")
            return specs
            
        return updated_specs

    @staticmethod
    def nested_channels_to_flat_config(dds_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert the on-disk nested JSON shape
        ({"frequency_hz":.., "channels": {"1": {"gain":.., "phase":.., "offset":..}}})
        into the flat dict shape apply_config()/get_parameter_specs() use
        ({"frequency_hz":.., "ch1_gain":.., "ch1_phase":.., "ch1_offset":..}) —
        lets MCULifecycleAdapter reuse apply_config() as the single writer at
        boot instead of duplicating a register-write path.

        Only emits keys actually present in dds_config: relies on the caller
        having resolved default+last upstream (resolve_config always fills
        all 4 channels from the default), so apply_config()'s own
        config.get(key, 0) fallback for an absent channel never kicks in here.
        """
        flat: Dict[str, Any] = {}
        if "frequency_hz" in dds_config:
            flat["frequency_hz"] = dds_config["frequency_hz"]
        if "link_dds1_dds2" in dds_config:
            flat["link_dds1_dds2"] = dds_config["link_dds1_dds2"]
        for ch_str, settings in dds_config.get("channels", {}).items():
            for param in ("gain", "phase", "offset"):
                if param in settings:
                    flat[f"ch{ch_str}_{param}"] = settings[param]
        return flat

    def get_default_ch3_gain(self) -> int:
        """Recommended gain for the synchronous-detection channels (ch3/ch4,
        kept equal by _enforce_dds3_dds4_gain_link), as declared in the pure
        default template — used to detect and fix an under-driven lock-in
        gain from the Excitation panel."""
        default_path = os.path.join(".aefi_acquisition", "configs", "ad9106_default_config.json")
        default_config = load_json_if_exists(default_path)
        return int(default_config.get("channels", {}).get("3", {}).get("gain", 10000))

    def reset_to_default(self) -> None:
        """Discard whatever is in ad9106_last_config.json and re-apply the
        saved default — reads the PURE default file (not resolve_config()'s
        default+last merge, which would just reproduce the current state)."""
        default_path = os.path.join(".aefi_acquisition", "configs", "ad9106_default_config.json")
        flat_config = self.nested_channels_to_flat_config(load_json_if_exists(default_path))
        self.apply_config(flat_config)

    def reload_last_config(self) -> None:
        """Discard any transient (persist=False) hardware write — e.g. the
        synchronous-detection compensation's correction on ch3 — and
        re-apply the last MANUALLY persisted configuration. Counterpart to
        reset_to_default(), which reloads the default file instead of the
        last one."""
        last_path = os.path.join(".aefi_acquisition", "configs", "ad9106_last_config.json")
        flat_config = self.nested_channels_to_flat_config(load_json_if_exists(last_path))
        if flat_config:
            self.apply_config(flat_config)

    def _enforce_dds1_dds2_link(self, config: Dict[str, Any], base_config: Dict[str, Any]) -> Dict[str, Any]:
        """When the DDS1/DDS2 gain link is active, mirror ch1_gain/ch2_gain
        onto each other before anything is written — this is what actually
        prevents the desync the link promises: without it, applying a config
        that only touches one channel (e.g. from the Hardware Advanced tab)
        would silently break the pair even while the link shows "on"."""
        linked = bool(config.get("link_dds1_dds2", base_config.get("link_dds1_dds2", True)))
        if not linked:
            return config
        ch1_in, ch2_in = "ch1_gain" in config, "ch2_gain" in config
        if not ch1_in and not ch2_in:
            return config
        config = dict(config)
        if ch1_in and not ch2_in:
            config["ch2_gain"] = config["ch1_gain"]
        elif ch2_in and not ch1_in:
            config["ch1_gain"] = config["ch2_gain"]
        elif config["ch1_gain"] != config["ch2_gain"]:
            # Both present but disagree — mirror whichever moved from its
            # last known value onto the other (assume ch2 moved if neither
            # matches, e.g. first-ever apply).
            prev_ch1_gain = self._last_published_channel_config.get(1, (None, None))[0]
            if config["ch1_gain"] == prev_ch1_gain:
                config["ch1_gain"] = config["ch2_gain"]
            else:
                config["ch2_gain"] = config["ch1_gain"]
            logger.debug(
                "DDS1/DDS2 link tie-break: ch1_gain/ch2_gain disagreed, resolved to gain=%s",
                config["ch1_gain"],
            )
        return config

    def _enforce_dds3_dds4_gain_link(self, config: Dict[str, Any], base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Mirror of _enforce_dds1_dds2_link for channels 3/4: keeps the
        synchronous-detection I/Q gains equal (both feed the same lock-in
        amplitude scaling) — without this, editing one via Hardware Advanced
        Config silently desyncs the pair. Config-only flag, no UI toggle,
        same pattern as enforce_dds3_dds4_quadrature — defaults to always-on."""
        linked = bool(config.get("link_dds3_dds4_gain", base_config.get("link_dds3_dds4_gain", True)))
        if not linked:
            return config
        ch3_in, ch4_in = "ch3_gain" in config, "ch4_gain" in config
        if not ch3_in and not ch4_in:
            return config
        config = dict(config)
        if ch3_in and not ch4_in:
            config["ch4_gain"] = config["ch3_gain"]
        elif ch4_in and not ch3_in:
            config["ch3_gain"] = config["ch4_gain"]
        elif config["ch3_gain"] != config["ch4_gain"]:
            # Both present but disagree — mirror whichever moved from its
            # last known value onto the other (assume ch4 moved if neither
            # matches, e.g. first-ever apply).
            prev_ch3_gain = self._last_published_synchronous_channel_config.get(3, (None, None))[0]
            if config["ch3_gain"] == prev_ch3_gain:
                config["ch3_gain"] = config["ch4_gain"]
            else:
                config["ch4_gain"] = config["ch3_gain"]
            logger.debug(
                "DDS3/DDS4 gain link tie-break: ch3_gain/ch4_gain disagreed, resolved to gain=%s",
                config["ch3_gain"],
            )
        return config

    def _enforce_dds3_dds4_quadrature(self, config: Dict[str, Any], base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Unidirectional invariant: when ch3 is INTENTIONALLY changed, ch4
        follows it at -90° (quadrature I/Q reference for the synchronous
        detection demodulation), never the other way around. Unlike
        _enforce_dds1_dds2_link, there is no mutual mirroring — ch3 is the
        sole source of truth. Preserves the default config template
        convention (ch3=90°, ch4=0°, i.e. ch4 = ch3 - 90°).

        Guards on ch3_phase actually DIFFERING from the last-applied value
        (base_config), not merely being present in `config` — the generic
        Hardware Advanced Config panel resubmits every widget's current
        value on every Apply click, so ch3_phase is present in nearly every
        call even when the user only edited ch4. Without this guard, a
        direct ch4 edit was silently discarded on every apply."""
        enforced = bool(config.get(
            "enforce_dds3_dds4_quadrature", base_config.get("enforce_dds3_dds4_quadrature", True)
        ))
        if not enforced or "ch3_phase" not in config:
            return config
        new_ch3_phase = int(config["ch3_phase"])
        base_ch3_phase = base_config.get("channels", {}).get("3", {}).get("phase")
        if base_ch3_phase is not None and new_ch3_phase == int(base_ch3_phase):
            # ch3 unchanged from the last applied state — this call isn't an
            # intentional ch3 edit, so leave ch4 alone (respects a direct,
            # independent ch4 edit submitted in the same full-config call).
            logger.debug(
                "DDS3/DDS4 quadrature: ch3_phase=%s unchanged from last applied value, "
                "skipping ch4 auto-update (preserves any direct ch4 edit in this same apply call)",
                new_ch3_phase,
            )
            return config
        config = dict(config)
        ch3_angle = PhaseAngle.from_register(new_ch3_phase)
        ch4_degrees = (ch3_angle.degrees - 90.0) % 360.0
        config["ch4_phase"] = PhaseAngle(ch4_degrees).to_register()
        return config

    def is_dds3_dds4_quadrature_enforced(self) -> bool:
        """Read-only resolved state (default+last config) of the ch3/ch4
        quadrature enforcement flag — no UI toggle exists for it, this is
        for other infrastructure/application code to query."""
        default_path = os.path.join(".aefi_acquisition", "configs", "ad9106_default_config.json")
        last_path = os.path.join(".aefi_acquisition", "configs", "ad9106_last_config.json")
        resolved = resolve_config(load_json_if_exists(default_path), load_json_if_exists(last_path))
        return bool(resolved.get("enforce_dds3_dds4_quadrature", True))

    def apply_config(self, config: Dict[str, Any], persist: bool = True) -> None:
        """
        Apply advanced configuration.

        Args:
            config: Flat dictionary of values keyed by parameter key.
            persist: When False, writes the hardware registers and publishes
                the usual change events, but does NOT merge/save onto
                ad9106_last_config.json. Used by the synchronous-detection
                compensation write path: that value is a transient,
                programmatic correction, not the user's manually-tuned
                baseline — ad9106_last_config.json must keep reflecting the
                last MANUAL setting, so disabling compensation (or simply
                reselecting the hardware in Hardware Advanced Config, which
                re-reads this file) still shows/restores the user's own
                value rather than whatever compensation last computed.
        """
        default_path = os.path.join(".aefi_acquisition", "configs", "ad9106_default_config.json")
        last_path = os.path.join(".aefi_acquisition", "configs", "ad9106_last_config.json")
        base_config = resolve_config(load_json_if_exists(default_path), load_json_if_exists(last_path))
        config = self._enforce_dds1_dds2_link(config, base_config)
        config = self._enforce_dds3_dds4_gain_link(config, base_config)
        config = self._enforce_dds3_dds4_quadrature(config, base_config)

        # 1. Apply to Hardware via Controller
        try:
            # Frequency
            if "frequency_hz" in config:
                new_frequency_hz = float(config["frequency_hz"])
                self._controller.set_dds_frequency(new_frequency_hz)

                # Notify other consumers (Excitation tab cache, probe demodulation, scan
                # export snapshot) that the shared DDS frequency register changed — the
                # panel re-sends the full config dict on every "Apply", so guard on the
                # actual value to avoid publishing on unrelated gain/phase edits.
                if new_frequency_hz != self._last_published_frequency_hz:
                    self._event_bus.publish(
                        EXCITATION_FREQUENCY_CHANGED_TOPIC,
                        ExcitationFrequencyChanged(frequency_hz=new_frequency_hz),
                    )
                    self._last_published_frequency_hz = new_frequency_hz


            # Channels (Restricted to DDS1 and DDS2)
            # Channels (Expanded to all 4 channels)
            for ch in range(1, 5):
                # Note: Keys come from get_parameter_specs which uses "ch{ch}_..." prefix
                if f"ch{ch}_gain" in config:
                    self._controller.set_dds_gain(ch, int(config[f"ch{ch}_gain"]))
                if f"ch{ch}_phase" in config:
                    self._controller.set_dds_phase(ch, int(config[f"ch{ch}_phase"]))
                if f"ch{ch}_offset" in config:
                    self._controller.set_dds_offset(ch, int(config[f"ch{ch}_offset"]))

                # Channels 1/2 drive excitation (3/4 are synchronous detection) —
                # notify ExcitationConfigurationService so it can recompute
                # level and detect a non-standard phase pair (-> CUSTOM mode).
                if ch in (1, 2) and (f"ch{ch}_gain" in config or f"ch{ch}_phase" in config):
                    base_ch = base_config.get("channels", {}).get(str(ch), {})
                    new_gain = int(config.get(f"ch{ch}_gain", base_ch.get("gain", 0)))
                    new_phase = int(config.get(f"ch{ch}_phase", base_ch.get("phase", 0)))
                    new_channel_config = (new_gain, new_phase)
                    if new_channel_config != self._last_published_channel_config.get(ch):
                        self._event_bus.publish(
                            DDS_CHANNEL_CONFIG_CHANGED_TOPIC,
                            DdsChannelConfigChanged(channel=ch, gain=new_gain, phase=new_phase),
                        )
                        self._last_published_channel_config[ch] = new_channel_config

                # Channels 3/4 (synchronous detection reference) — on a
                # SEPARATE topic (see comment on the constant above), so the
                # Hardware Advanced Config panel's own ch3/ch4 widgets and the
                # Synchronous Detection presenter can refresh after a manual
                # edit or the quadrature-enforcement-derived ch4 write —
                # without ExcitationConfigurationService seeing it.
                if ch in (3, 4) and (f"ch{ch}_gain" in config or f"ch{ch}_phase" in config):
                    base_ch = base_config.get("channels", {}).get(str(ch), {})
                    new_gain = int(config.get(f"ch{ch}_gain", base_ch.get("gain", 0)))
                    new_phase = int(config.get(f"ch{ch}_phase", base_ch.get("phase", 0)))
                    new_channel_config = (new_gain, new_phase)
                    if new_channel_config != self._last_published_synchronous_channel_config.get(ch):
                        self._event_bus.publish(
                            DDS_SYNCHRONOUS_DETECTION_CHANNEL_CHANGED_TOPIC,
                            DdsChannelConfigChanged(channel=ch, gain=new_gain, phase=new_phase),
                        )
                        self._last_published_synchronous_channel_config[ch] = new_channel_config

            # Link toggle (no hardware register — just a persisted/synced flag)
            if "link_dds1_dds2" in config:
                new_linked = bool(config["link_dds1_dds2"])
                if new_linked != self._last_published_link:
                    self._event_bus.publish(
                        EXCITATION_DDS_LINK_CHANGED_TOPIC,
                        ExcitationDdsLinkChanged(linked=new_linked),
                    )
                    self._last_published_link = new_linked

        except Exception as e:
            logger.exception("Failed to apply config to hardware")
            raise e

        if not persist:
            return

        # 2. Merge onto the current resolved state (computed above, before
        # the link enforcement) and save — using config.get(key, 0) here
        # (instead of falling back to the existing value) used to silently
        # zero out every channel/field not present in this specific call's
        # flat dict. A partial `config` (e.g. a single-channel edit, or any
        # test calling apply_config with just a couple of keys) would then
        # permanently corrupt last_config.json: since it's always "complete"
        # once written once, resolve_config() has no way to recover the
        # wiped fields from the default on a later boot. Reading the current
        # resolved state as the base fixes this.
        base_channels = base_config.get("channels", {})

        json_config = {
            "frequency_hz": float(config.get("frequency_hz", base_config.get("frequency_hz", 1000))),
            "link_dds1_dds2": bool(config.get("link_dds1_dds2", base_config.get("link_dds1_dds2", True))),
            "enforce_dds3_dds4_quadrature": bool(config.get(
                "enforce_dds3_dds4_quadrature", base_config.get("enforce_dds3_dds4_quadrature", True)
            )),
            "link_dds3_dds4_gain": bool(config.get(
                "link_dds3_dds4_gain", base_config.get("link_dds3_dds4_gain", True)
            )),
            "channels": {},
            "dacs": base_config.get("dacs", {}) or {str(ch): {"offset": 0} for ch in range(1, 5)},
        }

        for ch in range(1, 5):
            base_ch = base_channels.get(str(ch), {})
            json_config["channels"][str(ch)] = {
                "gain": int(config.get(f"ch{ch}_gain", base_ch.get("gain", 0))),
                "phase": int(config.get(f"ch{ch}_phase", base_ch.get("phase", 0))),
                "offset": int(config.get(f"ch{ch}_offset", base_ch.get("offset", 0))),
            }

        try:
            # Save to the configs folder
            with open(last_path, 'w') as f:
                json.dump(json_config, f, indent=4)
            logger.info("Config saved to %s", last_path)
        except Exception:
            logger.exception("Failed to save config")

    def save_config_as_default(self, config: Dict[str, Any]) -> None:
        """
        Save configuration as default.
        """
        # Merge onto the current default (same read-modify-write reasoning
        # as apply_config() above — a partial `config` must not zero out
        # fields it doesn't mention).
        default_path = os.path.join(".aefi_acquisition", "configs", "ad9106_default_config.json")
        base_config = load_json_if_exists(default_path)
        base_channels = base_config.get("channels", {})

        json_config = {
            "frequency_hz": float(config.get("frequency_hz", base_config.get("frequency_hz", 1000))),
            "link_dds1_dds2": bool(config.get("link_dds1_dds2", base_config.get("link_dds1_dds2", True))),
            "enforce_dds3_dds4_quadrature": bool(config.get(
                "enforce_dds3_dds4_quadrature", base_config.get("enforce_dds3_dds4_quadrature", True)
            )),
            "link_dds3_dds4_gain": bool(config.get(
                "link_dds3_dds4_gain", base_config.get("link_dds3_dds4_gain", True)
            )),
            "channels": {},
            "dacs": base_config.get("dacs", {}) or {str(ch): {"offset": 0} for ch in range(1, 5)},
        }

        for ch in range(1, 5):
            base_ch = base_channels.get(str(ch), {})
            json_config["channels"][str(ch)] = {
                "gain": int(config.get(f"ch{ch}_gain", base_ch.get("gain", 0))),
                "phase": int(config.get(f"ch{ch}_phase", base_ch.get("phase", 0))),
                "offset": int(config.get(f"ch{ch}_offset", base_ch.get("offset", 0))),
            }
            json_config["dacs"][str(ch)] = {"offset": 0}

        try:
            with open(default_path, 'w') as f:
                json.dump(json_config, f, indent=4)
            logger.info("Default config saved to %s", default_path)
        except Exception as e:
            logger.exception("Failed to save default config")
            raise e
