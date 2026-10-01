"""
Hardware Advanced Configuration Presenter - Interface V2

Bridges between HardwareConfigurationService and HardwareAdvancedConfigPanel.
Adapted from interface v1 for PySide6.
"""

import logging
from dataclasses import replace

from PySide6.QtCore import QObject, Signal, Slot
from typing import List, Dict, Any, Optional

from application.services.hardware_configuration_service.hardware_configuration_service import HardwareConfigurationService
from application.services.excitation_configuration_service.excitation_configuration_service import (
    EXCITATION_FREQUENCY_CHANGED_TOPIC,
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
from domain.shared_kernel.value_objects.hardware_configuration.hardware_advanced_parameter_schema import (
    HardwareAdvancedParameterSchema,
    NumberParameterSchema,
    EnumParameterSchema,
    BooleanParameterSchema,
)

logger = logging.getLogger(__name__)

_AD9106_HARDWARE_ID = "ad9106_dds"
DDS_CHANNEL_CONFIG_CHANGED_TOPIC = "ddschannelconfigchanged"
EXCITATION_DDS_LINK_CHANGED_TOPIC = "excitationddslinkchanged"
DDS_SYNCHRONOUS_DETECTION_CHANNEL_CHANGED_TOPIC = "ddssynchronousdetectionchannelchanged"


class HardwareAdvancedConfigPresenter(QObject):
    """
    Presenter for Hardware Advanced Configuration Panel.

    Responsibility:
    - Expose available hardware IDs.
    - Provide parameter specs for selected hardware.
    - Apply configuration changes via HardwareConfigurationService.
    - Stay in sync when the Excitation panel changes the shared DDS
      frequency directly — the reverse direction already existed
      (AD9106AdvancedConfigurator publishes on Apply) but this panel never
      listened, so it went stale until manually reselected.
    """

    # Signals emitted to the UI
    hardware_list_updated = Signal(list)  # list of str (hardware_ids)
    specs_loaded = Signal(str, list)  # hardware_id, list[HardwareAdvancedParameterSchema]
    status_message = Signal(str)  # User feedback
    config_applied = Signal(str)  # hardware_id

    def __init__(self, config_service: HardwareConfigurationService, event_bus: IDomainEventBus):
        super().__init__()
        self._service = config_service
        self._current_hardware_id: Optional[str] = None
        self._current_specs: List[HardwareAdvancedParameterSchema] = []
        event_bus.subscribe(EXCITATION_FREQUENCY_CHANGED_TOPIC, self._on_frequency_changed)
        event_bus.subscribe(DDS_CHANNEL_CONFIG_CHANGED_TOPIC, self._on_dds_channel_config_changed)
        event_bus.subscribe(EXCITATION_DDS_LINK_CHANGED_TOPIC, self._on_link_changed)
        event_bus.subscribe(
            DDS_SYNCHRONOUS_DETECTION_CHANNEL_CHANGED_TOPIC, self._on_dds_channel_config_changed
        )

    def _on_frequency_changed(self, event: ExcitationFrequencyChanged) -> None:
        """Patch just the frequency_hz spec in place — re-fetching full specs
        would re-read ad9106_default_config.json and both revert any other
        unsaved edit in this panel and show a stale frequency again (that
        file isn't updated by an Excitation-panel change)."""
        self._patch_specs_by_key({"frequency_hz": event.frequency_hz})

    def _on_dds_channel_config_changed(self, event: DdsChannelConfigChanged) -> None:
        """Mirror of _on_frequency_changed for level (-> gain) and mode
        (-> phase) — the Excitation panel writes gain/phase for channels 1/2
        the same way it already writes frequency; this panel needs the same
        catch-up for those two fields."""
        self._patch_specs_by_key({
            f"ch{event.channel}_gain": event.gain,
            f"ch{event.channel}_phase": event.phase,
        })

    def _on_link_changed(self, event: ExcitationDdsLinkChanged) -> None:
        """Mirror of _on_frequency_changed for the DDS1/DDS2 gain link — the
        Excitation panel's "Link S1-S2 = S3-S4" checkbox can toggle this
        directly; keep this panel's link_dds1_dds2 checkbox in sync."""
        self._patch_specs_by_key({"link_dds1_dds2": event.linked})

    def _patch_specs_by_key(self, new_values_by_key: Dict[str, Any]) -> None:
        if self._current_hardware_id != _AD9106_HARDWARE_ID or not self._current_specs:
            return
        self._current_specs = [
            replace(spec, default_value=new_values_by_key[spec.key]) if spec.key in new_values_by_key else spec
            for spec in self._current_specs
        ]
        self.specs_loaded.emit(self._current_hardware_id, self._current_specs)

    @Slot()
    def refresh_hardware_list(self):
        """Fetch available hardware IDs and emit signal."""
        try:
            ids = self._service.list_hardware_ids()
            self.hardware_list_updated.emit(ids)
            self.status_message.emit(f"Found {len(ids)} hardware device(s)")
        except Exception as e:
            self.status_message.emit(f"Error refreshing hardware list: {e}")
    
    @Slot(str)
    def select_hardware(self, hardware_id: str):
        """
        User selected a hardware ID.
        Load specs and emit them to View.
        
        Args:
            hardware_id: Identifier of the hardware to configure
        """
        if hardware_id not in self._service.list_hardware_ids():
            self.status_message.emit(f"Error: Hardware '{hardware_id}' not found.")
            return
        
        self._current_hardware_id = hardware_id
        
        try:
            # Service returns List[HardwareAdvancedParameterSchema]
            domain_specs = self._service.get_parameter_specs(hardware_id)
            self._current_specs = domain_specs

            self.specs_loaded.emit(hardware_id, domain_specs)
            display_name = self._service.get_hardware_display_name(hardware_id)
            self.status_message.emit(f"Loaded configuration for {display_name}")
            
        except Exception as e:
            self.status_message.emit(f"Error loading specs: {e}")
    
    @Slot(dict)
    def apply_configuration(self, config: Dict[str, Any]):
        """
        Apply configuration to the currently selected hardware.
        
        Args:
            config: Dictionary of parameter values keyed by parameter key
        """
        if not self._current_hardware_id:
            self.status_message.emit("Error: No hardware selected.")
            return
        
        try:
            self._service.apply_config(self._current_hardware_id, config)
            display_name = self._service.get_hardware_display_name(self._current_hardware_id)
            self.status_message.emit(f"Configuration applied to {display_name}")
            self.config_applied.emit(self._current_hardware_id)
        except Exception as e:
            self.status_message.emit(f"Error applying config: {e}")

    @Slot(dict)
    def save_configuration_as_default(self, config: Dict[str, Any]):
        """
        Save configuration as default for the currently selected hardware.
        """
        if not self._current_hardware_id:
            self.status_message.emit("Error: No hardware selected.")
            return
        
        try:
            self._service.save_config_as_default(self._current_hardware_id, config)
            display_name = self._service.get_hardware_display_name(self._current_hardware_id)
            self.status_message.emit(f"Default configuration saved for {display_name}")
        except Exception as e:
            self.status_message.emit(f"Error saving default config: {e}")

    @Slot()
    def reset_configuration_to_default(self):
        """
        Discard the currently selected hardware's applied/last state and
        re-apply its saved default. Unlike _patch_specs_by_key (used for the
        Excitation-panel sync events, which each touch one or two fields), a
        reset can change every field at once — so this re-fetches the full
        spec list from the service, exactly like select_hardware(), instead
        of patching in place.
        """
        if not self._current_hardware_id:
            self.status_message.emit("Error: No hardware selected.")
            return

        try:
            self._service.reset_to_default(self._current_hardware_id)
            domain_specs = self._service.get_parameter_specs(self._current_hardware_id)
            self._current_specs = domain_specs
            self.specs_loaded.emit(self._current_hardware_id, domain_specs)
            display_name = self._service.get_hardware_display_name(self._current_hardware_id)
            self.status_message.emit(f"{display_name} reset to default")
            self.config_applied.emit(self._current_hardware_id)
        except Exception as e:
            self.status_message.emit(f"Error resetting to default: {e}")


