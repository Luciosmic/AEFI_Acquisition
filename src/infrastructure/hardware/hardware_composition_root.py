"""
Hardware Composition Root

Responsibility:
- Select real vs. mock hardware per subsystem (motion, MCU, electric field probe)
  from a `hardware_config` dict, and assemble the resulting ports.
- Wrap the acquisition port with the excitation-aware simulation wrapper when
  the MCU subsystem runs in mock mode.

Rationale:
- Composes ArcusCompositionRoot + MCUCompositionRoot + the Narda probe adapter
  into the single hardware bundle main.py needs, the same way ArcusCompositionRoot
  and MCUCompositionRoot each compose their own subsystem — keeps main.py from
  carrying this branching logic directly.
"""

import logging

from application.services.motion_control_service.ports.i_motion_port import IMotionPort
from application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort
from application.services.excitation_configuration_service.ports.i_excitation_port import IExcitationPort
from application.services.aefi_acquisition_service.ports.i_aefi_acquisition_executor import IAefiAcquisitionExecutor
from application.services.electric_field_probe_service.ports.i_electric_field_probe_port import IElectricFieldProbePort
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

from infrastructure.hardware.arcus_performax_4EX.composition_root_arcus import ArcusCompositionRoot
from infrastructure.hardware.micro_controller.mcu_composition_root import MCUCompositionRoot
from infrastructure.hardware.narda_ep600.adapter_electric_field_probe_port import NardaEP601ProbeAdapter

logger = logging.getLogger(__name__)


class HardwareCompositionRoot:
    """
    Composes the three hardware subsystems (motion, MCU, electric field probe)
    per `hardware_config`, and exposes the ports/roots the application
    composition root (main.py) injects into its services.
    """

    def __init__(self, hardware_config: dict, event_bus: IDomainEventBus, narda_com_port: str):
        self.lifecycle_adapters: list = []

        # --- Motion (Arcus) ---
        # "mock" still builds a real ArcusCompositionRoot — just with a faked
        # controller instead of the real DLL/USB one — so Hardware Config, the
        # startup/shutdown lifecycle, and ArcusAdapter's real worker/monitor
        # threads all run identically to the real-hardware path.
        if hardware_config["motion"] == "real":
            logger.info("Motion -> real (ArcusCompositionRoot)")
            self.arcus_root = ArcusCompositionRoot(event_bus=event_bus)
        else:
            from infrastructure.hardware.arcus_performax_4EX.fake.fake_arcus_performax4ex_controller import (
                FakeArcusPerformax4EXController,
            )
            logger.info("Motion -> mock (ArcusCompositionRoot, simulated controller)")
            self.arcus_root = ArcusCompositionRoot(event_bus=event_bus, controller=FakeArcusPerformax4EXController())
        self.motion_port: IMotionPort = self.arcus_root.motion
        self.lifecycle_adapters.append(self.arcus_root.lifecycle)

        # --- Acquisition (ADS131) + Excitation (AD9106) + Continuous — all part of MCU ---
        # Same principle: "mock" builds a real MCUCompositionRoot with a faked
        # serial transport, so AD9106/ADS131 controllers, configurators (Hardware
        # Config entries), and the excitation frequency-sync event all behave
        # exactly like real hardware.
        if hardware_config["aefi_device"] == "real":
            logger.info("Acquisition -> real (MCUCompositionRoot)")
            self.mcu_root = MCUCompositionRoot(event_bus=event_bus)
        else:
            from infrastructure.hardware.micro_controller.fake.fake_mcu_serial_communicator import (
                FakeMCUSerialCommunicator,
            )
            logger.info("Acquisition -> mock (MCUCompositionRoot, simulated communicator)")
            self.mcu_root = MCUCompositionRoot(event_bus=event_bus, communicator=FakeMCUSerialCommunicator())

        base_acquisition_port = self.mcu_root.acquisition
        self.excitation_port: IExcitationPort = self.mcu_root.excitation
        self.continuous_executor: IAefiAcquisitionExecutor = self.mcu_root.continuous
        self.lifecycle_adapters.append(self.mcu_root.lifecycle)
        logger.info(f"Excitation -> {hardware_config['aefi_device']} (from MCUCompositionRoot)")
        logger.info(f"Continuous -> {hardware_config['aefi_device']} (from MCUCompositionRoot)")

        # --- Wrap acquisition port with excitation-aware wrapper (only in mock mode) ---
        # This simulates the physical coupling between excitation and acquisition —
        # the fake serial transport itself only returns noise, it doesn't model this.
        # For real hardware, the coupling is physical and doesn't need simulation.
        if hardware_config["aefi_device"] == "mock":
            from infrastructure.mocks.adapter_mock_excitation_aware_acquisition import ExcitationAwareAcquisitionPort
            # Field simulation (4-sphere point-charge model + 8mm cube sensor,
            # empty-bench baseline) loads its geometry/gain/orientation from
            # .aefi_acquisition/configs/aefi_device_config.json — including
            # sensor.calibration.sources_to_sensor_rotation (ideal mounting
            # angles), not an arbitrary demo angle.
            self.acquisition_port: IAcquisitionPort = ExcitationAwareAcquisitionPort(
                base_acquisition_port=base_acquisition_port,
                excitation_port=self.excitation_port,
            )
            logger.info("Acquisition -> wrapped with ExcitationAwareAcquisitionPort (simulation)")
        else:
            # Use base acquisition port directly for real hardware
            self.acquisition_port: IAcquisitionPort = base_acquisition_port
            logger.info("Acquisition -> using base port directly (real hardware)")

        # --- Electric Field Probe (Narda EP-601) ---
        # Deliberately NOT added to lifecycle_adapters: this probe is auto-off and
        # times out often, so it must never block or fail app startup. Connection
        # is a manual action from the panel (Connect button), not a startup step.
        if hardware_config["electric_field_probe"] == "real":
            logger.info(f"Electric field probe -> real (Narda EP-601 on {narda_com_port})")
            self.probe_port: IElectricFieldProbePort = NardaEP601ProbeAdapter(port=narda_com_port)
        else:
            from infrastructure.hardware.narda_ep600.fake.fake_electric_field_probe_adapter import FakeElectricFieldProbeAdapter
            logger.info("Electric field probe -> mock")
            self.probe_port: IElectricFieldProbePort = FakeElectricFieldProbeAdapter()

        # Rule-6: non-obvious branch decision, per the "Deliberately NOT added to
        # lifecycle_adapters" comment above — worth a log line since a future
        # reader debugging a startup hang/failure needs to know the probe is not
        # part of the startup sequence at all.
        logger.debug(
            "Electric field probe deliberately excluded from hardware lifecycle "
            "(auto-off, frequent timeouts) — connection is manual via the panel."
        )
