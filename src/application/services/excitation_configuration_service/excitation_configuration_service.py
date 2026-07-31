from dataclasses import replace
from typing import Dict

from .ports.i_excitation_port import IExcitationPort
from domain.shared_kernel.excitation.value_objects.excitation_parameters import ExcitationParameters
from domain.shared_kernel.excitation.value_objects.excitation_level import ExcitationLevel
from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.excitation.events.excitation_frequency_changed.excitation_frequency_changed import (
    ExcitationFrequencyChanged,
)
from domain.shared_kernel.excitation.events.excitation_levels_changed.excitation_levels_changed import (
    ExcitationLevelsChanged,
)
from domain.shared_kernel.excitation.events.dds_channel_config_changed.dds_channel_config_changed import (
    DdsChannelConfigChanged,
)

EXCITATION_FREQUENCY_CHANGED_TOPIC = "excitationfrequencychanged"
EXCITATION_LEVELS_CHANGED_TOPIC = "excitationlevelschanged"
DDS_CHANNEL_CONFIG_CHANGED_TOPIC = "ddschannelconfigchanged"

# Mirrors AdapterExcitationConfigurationAD9106._map_excitation_mode_to_dds's
# phase table, (DDS1 phase, DDS2 phase) -> mode — channel number = DDS
# number for phase (no S1S2/S3S4 swap, unlike gain/level). Kept as local
# data rather than importing the infra adapter: what a phase pair *means*
# is part of ExcitationMode's own identity, and this is the one place that
# needs the reverse direction (mode -> phases is infra-only).
_MODE_BY_PHASE_PAIR = {
    (0, 0): ExcitationMode.Y_DIR,
    (0, 32768): ExcitationMode.X_DIR,
    (0, 16384): ExcitationMode.CIRCULAR_PLUS,
    (0, 49152): ExcitationMode.CIRCULAR_MINUS,
}
# Mirrors AdapterExcitationConfigurationAD9106.MAX_EXCITATION_GAIN.
_MAX_EXCITATION_GAIN = 5500


class ExcitationConfigurationService:
    """
    Application Service to configure the field excitation.
    """

    def __init__(self, excitation_port: IExcitationPort, event_bus: IDomainEventBus) -> None:
        self._port = excitation_port
        self._event_bus = event_bus
        self._current_params = ExcitationParameters.off()
        self._muted_params: ExcitationParameters | None = None
        self._last_known_phase_by_channel: Dict[int, int] = {1: 0, 2: 0}
        # Hardware Config tab can also change the shared DDS frequency register,
        # or channel 1/2 gain/phase, directly (bypassing this service) — stay in
        # sync via the event bus instead of polling.
        self._event_bus.subscribe(EXCITATION_FREQUENCY_CHANGED_TOPIC, self._on_frequency_changed)
        self._event_bus.subscribe(DDS_CHANNEL_CONFIG_CHANGED_TOPIC, self._on_dds_channel_config_changed)

    def _on_frequency_changed(self, event: ExcitationFrequencyChanged) -> None:
        self._current_params = replace(self._current_params, frequency=event.frequency_hz)

    def _on_dds_channel_config_changed(self, event: DdsChannelConfigChanged) -> None:
        """Recompute level for the changed channel from its gain, and
        re-derive mode from the (DDS1, DDS2) phase pair — falling back to
        ExcitationMode.CUSTOM when a manual Hardware Config edit no longer
        matches a known mode's phase pattern (e.g. an arbitrary phase)."""
        self._last_known_phase_by_channel[event.channel] = event.phase
        new_level_percent = (event.gain / _MAX_EXCITATION_GAIN) * 100.0

        # channel 1 = DDS1 -> feeds S3/S4; channel 2 = DDS2 -> feeds S1/S2
        if event.channel == 1:
            level_s3_s4 = ExcitationLevel(new_level_percent)
            level_s1_s2 = self._current_params.level_s1_s2
        else:
            level_s1_s2 = ExcitationLevel(new_level_percent)
            level_s3_s4 = self._current_params.level_s3_s4

        phase_pair = (self._last_known_phase_by_channel[1], self._last_known_phase_by_channel[2])
        mode = _MODE_BY_PHASE_PAIR.get(phase_pair, ExcitationMode.CUSTOM)

        self._current_params = replace(
            self._current_params, mode=mode, level_s1_s2=level_s1_s2, level_s3_s4=level_s3_s4
        )

    def set_excitation(
        self,
        mode: ExcitationMode,
        level_s1_s2_percent: float,
        level_s3_s4_percent: float,
        frequency: float,
    ) -> None:
        """
        Set the excitation mode, DDS levels, and frequency.

        Args:
            mode: Desired ExcitationMode
            level_s1_s2_percent: Intensity of spheres S1/S2 (DDS2 generator), 0.0 - 100.0
            level_s3_s4_percent: Intensity of spheres S3/S4 (DDS1 generator), 0.0 - 100.0
            frequency: Frequency logic (Hz)
        """
        level_s1_s2 = ExcitationLevel(level_s1_s2_percent)
        level_s3_s4 = ExcitationLevel(level_s3_s4_percent)
        params = ExcitationParameters(mode, level_s1_s2, level_s3_s4, frequency)

        frequency_changed = frequency != self._current_params.frequency
        levels_changed = (
            level_s1_s2_percent != self._current_params.level_s1_s2.value
            or level_s3_s4_percent != self._current_params.level_s3_s4.value
        )

        self._port.apply_excitation(params)
        self._current_params = params

        if frequency_changed:
            self._event_bus.publish(
                EXCITATION_FREQUENCY_CHANGED_TOPIC,
                ExcitationFrequencyChanged(frequency_hz=frequency),
            )
        if levels_changed:
            self._event_bus.publish(
                EXCITATION_LEVELS_CHANGED_TOPIC,
                ExcitationLevelsChanged(
                    level_s1_s2_percent=level_s1_s2_percent,
                    level_s3_s4_percent=level_s3_s4_percent,
                ),
            )

    def get_current_parameters(self) -> ExcitationParameters:
        return self._current_params

    def mute(self) -> None:
        """
        Cut the DDS gain to 0% for the differential-measurement baseline
        window, keeping mode/frequency untouched. Transient hardware toggle
        for the scan loop — not a user-facing config change, so it neither
        updates `_current_params` (still reflects the "real" excitation the
        user configured) nor publishes events.
        """
        if self._muted_params is not None:
            return  # already muted — avoid overwriting the pre-mute levels
        self._muted_params = self._current_params
        self._port.apply_excitation(
            replace(
                self._current_params,
                level_s1_s2=ExcitationLevel.off(),
                level_s3_s4=ExcitationLevel.off(),
            )
        )

    def unmute(self) -> None:
        """Restore the levels active before the last mute(). No-op if not muted."""
        if self._muted_params is None:
            return
        self._port.apply_excitation(self._muted_params)
        self._muted_params = None
