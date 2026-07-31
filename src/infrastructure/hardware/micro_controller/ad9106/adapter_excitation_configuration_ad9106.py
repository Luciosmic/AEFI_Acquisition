"""
AD9106 Excitation Configuration Adapter - Infrastructure Layer

Responsibility:
- Implement IExcitationPort interface
- Translate domain ExcitationParameters to AD9106 DDS hardware configuration
- Map excitation modes (X_DIR, Y_DIR, CIRCULAR) to DDS channel settings

Rationale:
- Separates domain logic from hardware details
- Allows domain to remain independent of specific DDS model
- Encapsulates hardware-specific mapping (phases, gains, modes)

Design:
- Hexagonal Architecture: Adapter pattern
- Translates ExcitationParameters → DDS commands
- Uses AD9106Controller for low-level hardware control
"""

# EXTERNAL PYTHON LIBS
from dataclasses import replace
from typing import Optional

# DOMAIN VALUE OBJECTS
from domain.shared_kernel.excitation.value_objects.excitation_parameters import ExcitationParameters
from domain.shared_kernel.excitation.value_objects.excitation_level import ExcitationLevel
from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode
from domain.shared_kernel.operation_result import OperationResult
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.excitation.events.dds_channel_config_changed.dds_channel_config_changed import (
    DdsChannelConfigChanged,
)

# APPLICATION
from application.services.excitation_configuration_service.ports.i_excitation_port import IExcitationPort

# INFRASTRUCTURE
from infrastructure.hardware.micro_controller.ad9106.ad9106_controller import AD9106Controller
from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator


class AdapterExcitationConfigurationAD9106(IExcitationPort):
    """
    Infrastructure adapter for AD9106 DDS excitation hardware.
    Implements IExcitationPort interface.
    Translates domain ExcitationParameters to hardware DDS configuration.
    """
    
    # Maximum DDS gain value (hardware limit)
    MAX_DDS_GAIN = 16376
    # Next value takes over to take into accound saturation of excitation board
    # Mapping: 100% level corresponds to this hardware gain value
    # This is the maximum practical gain for excitation (not the absolute hardware max)
    MAX_EXCITATION_GAIN = 5500  # 100% level maps to 5500
    
    # Phase values from documentation (event_storming_aefi.md) and config (experimental_data_config_v3.json)
    # Phases are in 16-bit values (0-65535) representing 0-360 degrees
    # Corrected mapping (was inverted in previous code):
    # - X_DIR: DDS1=0°, DDS2=0° (In Phase)
    # - Y_DIR: DDS1=0°, DDS2=180° (Opposition) = 32768
    # - circ+: phase_dds1=0, phase_dds2=16384 (90°)
    # - circ-: phase_dds1=0, phase_dds2=49152 (270°)
    
    def __init__(
        self,
        controller: Optional[AD9106Controller] = None,
        communicator: Optional[MCU_SerialCommunicator] = None,
        event_bus: Optional[IDomainEventBus] = None,
    ):
        """
        Initialize AD9106 adapter.

        Args:
            controller: AD9106Controller instance. If None, creates one.
            communicator: MCU_SerialCommunicator (for controller creation). If None, uses singleton.
            event_bus: Domain event bus — publishes DdsChannelConfigChanged so the
                Hardware Config tab (and any other subscriber) stays in sync when
                gain/phase is changed from this (Excitation panel) side instead.
                Optional: sync is a nice-to-have, not required for excitation itself.
        """
        if controller:
            self._controller = controller
        else:
            comm = communicator or MCU_SerialCommunicator()
            self._controller = AD9106Controller(comm)

        self._current_params: Optional[ExcitationParameters] = None
        self._event_bus = event_bus

    @property
    def last_parameters(self) -> Optional[ExcitationParameters]:
        """Read-only view of the last applied params — same duck-typed attribute
        name as MockExcitationPort, so ExcitationAwareAcquisitionPort's
        physical-coupling simulation works against either (see its
        _get_current_excitation, which checks hasattr(..., 'last_parameters'))."""
        return self._current_params

    def apply_excitation(self, params: ExcitationParameters) -> None:
        """
        Apply excitation parameters to AD9106 hardware.
        
        Translates domain ExcitationParameters to DDS configuration:
        - Frequency → set_dds_frequency()
        - Mode → set_dds_phase() for each channel (Gains only if active channels change)
        - Level → set_dds_gain() for active channels
        
        Optimized to minimize hardware communication:
        - Only updates parameters that have changed.
        - Strictly follows "Just change phases for mode change" rule where possible.
        
        Args:
            params: Domain excitation parameters (mode, level, frequency)
            
        Raises:
            RuntimeError: If hardware configuration fails
        """
        # Check for redundant update to avoid double communication
        if self._current_params == params:
            return

        print(
            f"[AD9106Adapter] apply_excitation called: mode={params.mode.name}, "
            f"level_s1_s2={params.level_s1_s2.value}%, level_s3_s4={params.level_s3_s4.value}%, "
            f"freq={params.frequency}Hz"
        )

        # 1. Handle full OFF (both DDS levels at 0)
        if params.level_s1_s2.value == 0 and params.level_s3_s4.value == 0:
            # Zero gain only — amplitude is what "off" means, phase is
            # irrelevant once gain is 0 and not worth touching (it used to
            # get reset to 0 here too, which scrambled the excitation
            # direction on every point of a differential scan, since mute()
            # goes through this same branch).
            for channel in [1, 2]:
                result = self._controller.set_dds_gain(channel, 0)
                if result.is_failure:
                    raise RuntimeError(f"Failed to set DDS{channel} gain to 0: {result.error}")
            current_phase = self._controller.get_memory_state()["DDS"]["Phase"]
            self._publish_channel_config_changed(
                {1: 0, 2: 0}, {1: current_phase[1], 2: current_phase[2]}
            )
            # Store current parameters and return
            self._current_params = params
            return

        # Determine what changed
        # If previous was None or fully OFF, assume everything needs update
        was_off = self._current_params is None or (
            self._current_params.level_s1_s2.value == 0 and self._current_params.level_s3_s4.value == 0
        )

        freq_changed = was_off or (params.frequency != self._current_params.frequency)
        level_changed = was_off or (
            params.level_s1_s2.value != self._current_params.level_s1_s2.value
            or params.level_s3_s4.value != self._current_params.level_s3_s4.value
        )
        mode_changed = was_off or (params.mode != self._current_params.mode)

        # 2. Set frequency (applies to all DDS channels)
        if params.frequency > 0 and freq_changed:
            result = self._controller.set_dds_frequency(params.frequency)
            if result.is_failure:
                raise RuntimeError(f"Failed to set DDS frequency: {result.error}")
        
        # 3. Map excitation mode to DDS channel configuration
        dds_config = self._map_excitation_mode_to_dds(params.mode)
        
        # 4. Set gains
        # Update gains if Level changed OR if Active Channels changed (due to mode change)
        update_gains = level_changed
        if mode_changed and not was_off:
            # Check if active channels changed
            prev_config = self._map_excitation_mode_to_dds(self._current_params.mode)
            if set(prev_config["active_channels"]) != set(dds_config["active_channels"]):
                update_gains = True
        
        # Convert level percentages (0-100) to DDS gain (0-5500), per channel.
        # Confirmed on oscilloscope (see "Correspondance Poupette Sortie DDS" note):
        # channel 1 (DDS1 generator) feeds spheres S3/S4, channel 2 (DDS2 generator)
        # feeds spheres S1/S2 — the reverse of the naive channel-number assumption.
        # Computed unconditionally (cheap) so it's available for the sync-event
        # publish below even on a phase-only change (update_gains False).
        active_channels = dds_config["active_channels"]
        applied_gain_by_channel = {
            1: int((params.level_s3_s4.value / 100.0) * self.MAX_EXCITATION_GAIN) if 1 in active_channels else 0,
            2: int((params.level_s1_s2.value / 100.0) * self.MAX_EXCITATION_GAIN) if 2 in active_channels else 0,
        }

        if update_gains:
            # Apply gain to active channels
            for channel in active_channels:
                result = self._controller.set_dds_gain(channel, applied_gain_by_channel[channel])
                if result.is_failure:
                    raise RuntimeError(f"Failed to set DDS{channel} gain: {result.error}")

            # Set inactive excitation channels (DDS1/DDS2) to 0 gain
            inactive_excitation_channels = [ch for ch in [1, 2] if ch not in active_channels]
            for channel in inactive_excitation_channels:
                result = self._controller.set_dds_gain(channel, 0)
                if result.is_failure:
                    raise RuntimeError(f"Failed to set DDS{channel} gain to 0: {result.error}")

        # 5. Set phases
        # Update phases if Mode changed (or if we just came from OFF)
        if mode_changed:
            for channel in [1, 2]:
                phase = dds_config["phases"][channel]
                print(f"[AD9106Adapter] Setting DDS{channel} phase to {phase} (mode={params.mode.name})")
                result = self._controller.set_dds_phase(channel, phase)
                print(f"[AD9106Adapter] DDS{channel} phase set to {phase}")
                if result.is_failure:
                    raise RuntimeError(f"Failed to set DDS{channel} phase: {result.error}")
                print(f"[AD9106Adapter] DDS{channel} phase set successfully")

        if update_gains or mode_changed:
            self._publish_channel_config_changed(applied_gain_by_channel, dds_config["phases"])

        # Store current parameters
        self._current_params = params

    def set_gain(self, level_s1_s2_percent: float, level_s3_s4_percent: float) -> None:
        """
        Write only the DDS gain registers, leaving phase/frequency untouched
        — see IExcitationPort.set_gain. Doesn't publish DdsChannelConfigChanged:
        this is a transient scan-internal toggle, not a user-facing config
        change the Hardware Config tab should sync to.
        """
        if self._current_params is None:
            return  # nothing configured yet — nothing to mute/restore

        dds_config = self._map_excitation_mode_to_dds(self._current_params.mode)
        active_channels = dds_config["active_channels"]
        gain_by_channel = {
            1: int((level_s3_s4_percent / 100.0) * self.MAX_EXCITATION_GAIN) if 1 in active_channels else 0,
            2: int((level_s1_s2_percent / 100.0) * self.MAX_EXCITATION_GAIN) if 2 in active_channels else 0,
        }
        for channel in (1, 2):
            result = self._controller.set_dds_gain(channel, gain_by_channel[channel])
            if result.is_failure:
                raise RuntimeError(f"Failed to set DDS{channel} gain to {gain_by_channel[channel]}: {result.error}")

        self._current_params = replace(
            self._current_params,
            level_s1_s2=ExcitationLevel(level_s1_s2_percent),
            level_s3_s4=ExcitationLevel(level_s3_s4_percent),
        )

    def _publish_channel_config_changed(self, gain_by_channel: dict, phase_by_channel: dict) -> None:
        """Notify sync consumers (e.g. the Hardware Config tab) with the
        actual hardware-unit values just written — see
        DdsChannelConfigChanged intention.md."""
        if not self._event_bus:
            return
        for channel in (1, 2):
            self._event_bus.publish(
                "ddschannelconfigchanged",
                DdsChannelConfigChanged(
                    channel=channel,
                    gain=gain_by_channel[channel],
                    phase=phase_by_channel[channel],
                ),
            )

    def _map_excitation_mode_to_dds(self, mode: ExcitationMode) -> dict:
        """
        Map domain ExcitationMode to DDS channel configuration.
        
        Note: DDS3 and DDS4 are for synchronous detection and remain unchanged.
        Only DDS1 and DDS2 are used for excitation.
        
        Returns:
            Dictionary with:
            - phases: dict[channel] = phase_value
            - active_channels: list of channel numbers that should have gain
        """
        config = {
            "phases": {1: 0, 2: 0},
            "active_channels": []
        }
        
        # Map modes according to documentation (event_storming_aefi.md) and config (experimental_data_config_v3.json)
        # CORRECTED: X_DIR and Y_DIR were inverted in previous code
        if mode == ExcitationMode.Y_DIR:
            # X direction: DDS1 and DDS2 active, in phase (0°)
            # Documentation: X-Dir: DDS1=0°, DDS2=0° (In Phase)
            config["active_channels"] = [1, 2]
            config["phases"][1] = 0  # DDS1: 0°
            config["phases"][2] = 0  # DDS2: 0° (in phase)
            print(f"[AD9106Adapter] Y_DIR mode: DDS1 phase=0°, DDS2 phase=0° (in phase)")
            # DDS3 and DDS4 unchanged (synchronous detection)
            
        elif mode == ExcitationMode.X_DIR:
            # Y direction: DDS1 and DDS2 active, in opposition (180°)
            # Documentation: Y-Dir: DDS1=0°, DDS2=180° (Opposition)
            # Config JSON: ydir: dds1 phase_deg=180, dds2 phase_deg=0
            # Note: Config shows dds1=180, but documentation says DDS1=0°, DDS2=180°
            # Following documentation convention: DDS1=0°, DDS2=180°
            config["active_channels"] = [1, 2]
            config["phases"][1] = 0      # DDS1: 0°
            config["phases"][2] = 32768  # DDS2: 180° (Opposition)
            print(f"[AD9106Adapter] X_DIR mode: DDS1 phase=0°, DDS2 phase=180° (Opposition)")
            # DDS3 and DDS4 unchanged (synchronous detection)
            
        elif mode == ExcitationMode.CIRCULAR_PLUS:
            # Circular rotation (clockwise): DDS1 and DDS2 with +90° quadrature
            # Legacy: phase_dds1=0, phase_dds2=16384 (90°)
            config["active_channels"] = [1, 2]
            config["phases"][1] = 0      # DDS1: 0°
            config["phases"][2] = 16384  # DDS2: 90° (quadrature +)
            print(f"[AD9106Adapter] CIRCULAR_PLUS mode: DDS1 phase=0°, DDS2 phase=90° (16384)")
            # DDS3 and DDS4 unchanged (synchronous detection)
            
        elif mode == ExcitationMode.CIRCULAR_MINUS:
            # Circular rotation (counter-clockwise): DDS1 and DDS2 with -90° quadrature
            # Legacy: phase_dds1=0, phase_dds2=49152 (270° = -90°)
            config["active_channels"] = [1, 2]
            config["phases"][1] = 0      # DDS1: 0°
            config["phases"][2] = 49152  # DDS2: 270° (quadrature -)
            print(f"[AD9106Adapter] CIRCULAR_MINUS mode: DDS1 phase=0°, DDS2 phase=270° (49152)")
            # DDS3 and DDS4 unchanged (synchronous detection)
            
        elif mode == ExcitationMode.CUSTOM:
            # Custom mode: use current hardware state (no change to phases/modes)
            # Only frequency and level will be updated
            memory_state = self._controller.get_memory_state()
            # Determine active channels from current gain values (only DDS1/DDS2 for excitation)
            for channel in [1, 2]:
                if memory_state["DDS"]["Gain"][channel] > 0:
                    config["active_channels"].append(channel)
                config["phases"][channel] = memory_state["DDS"]["Phase"][channel]
            # DDS3 and DDS4 phases remain unchanged
        
        return config
    
    def get_controller(self) -> AD9106Controller:
        """Get the underlying AD9106Controller (for lifecycle initialization)."""
        return self._controller


