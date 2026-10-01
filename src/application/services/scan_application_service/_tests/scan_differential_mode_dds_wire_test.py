"""
E2E test: differential measurement, verified on the (fake) DDS wire.

scan_differential_mode_integration_test.py already proves mute()/unmute()
eliminate the excitation offset — but it drives ExcitationConfigurationService
through MockExcitationPort, which bypasses AdapterExcitationConfigurationAD9106
and AD9106Controller entirely (no redundant-update check, no
DdsChannelConfigChanged self-echo, no two-step address/data protocol).

This test runs the same differential scan through the REAL adapter/controller
stack app.py wires for "mock mode" (MCUCompositionRoot + FakeMCUSerialCommunicator,
see main.py's aefi_device == "mock" branch) and inspects the raw commands that
would have gone out over the wire — the only way to catch a bug where the
domain-level mute/unmute round-trips correctly but the actual DDS gain
register write gets skipped or reordered.
"""
import threading
import unittest

from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.scan_application_service.dtos.scan_dtos import Scan2DConfigDTO
from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from application.services.excitation_configuration_service.excitation_configuration_service import (
    ExcitationConfigurationService,
)
from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.thread_pool_task_runner import ThreadPoolTaskRunner
from infrastructure.execution.event_bus_motion_synchronizer import EventBusMotionSynchronizer
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor
from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort
from infrastructure.hardware.micro_controller.mcu_composition_root import MCUCompositionRoot
from infrastructure.hardware.micro_controller.fake.fake_mcu_serial_communicator import FakeMCUSerialCommunicator
from infrastructure.hardware.micro_controller.ad9106.adapter_excitation_configuration_ad9106 import (
    AdapterExcitationConfigurationAD9106,
)
from infrastructure.hardware.micro_controller.ad9106.ad9106_controller import AD9106Controller


class _SpySerialCommunicator(FakeMCUSerialCommunicator):
    """Records every command reaching the (fake) wire, so the test can assert
    on the actual two-step 'a<addr>' / 'd<value>' register writes a scan
    produces, instead of trusting the domain-level ExcitationParameters."""

    def __init__(self):
        super().__init__()
        self.commands: list[str] = []

    def send_command(self, command: str):
        self.commands.append(command)
        return super().send_command(command)

    def gain_writes(self, address: int) -> list[int]:
        """Reconstruct the sequence of values written to one DDS gain
        register from the raw address-select/data-write command pairs."""
        values = []
        pending_addr = None
        for cmd in self.commands:
            body = cmd.rstrip("*")
            if body.startswith("a") and body[1:].isdigit():
                pending_addr = int(body[1:])
            elif body.startswith("d") and body[1:].isdigit() and pending_addr == address:
                values.append(int(body[1:]))
        return values


class TestScanDifferentialModeDdsWire(unittest.TestCase):
    EXCITATION_LEVEL_PERCENT = 80.0
    GAIN_ADDR_CH1 = AD9106Controller.DDS_ADDRESSES["Gain"][1]
    GAIN_ADDR_CH2 = AD9106Controller.DDS_ADDRESSES["Gain"][2]

    def setUp(self):
        self.event_bus = InMemoryEventBus()

        self.communicator = _SpySerialCommunicator()
        self.communicator.connect()
        self.mcu_root = MCUCompositionRoot(event_bus=self.event_bus, communicator=self.communicator)

        self.excitation_service = ExcitationConfigurationService(
            excitation_port=self.mcu_root.excitation, event_bus=self.event_bus
        )
        # Excitation ON before the scan starts, exactly as a real acquisition
        # would have it configured — the loop must mute it (on the wire) for
        # the baseline window and restore this exact state for the excited one.
        self.excitation_service.set_excitation(
            ExcitationMode.X_DIR,
            level_s1_s2_percent=self.EXCITATION_LEVEL_PERCENT,
            level_s3_s4_percent=self.EXCITATION_LEVEL_PERCENT,
            frequency=1000.0,
        )

        self.motion_port = MockMotionPort(event_bus=self.event_bus, motion_delay_ms=1)
        acquisition_port = RandomNoiseAcquisitionPort(noise_std=0.0, seed=42)
        continuous_service = AefiAcquisitionService(
            MockAefiAcquisitionExecutor(self.event_bus), acquisition_port
        )
        self.service = ScanApplicationService(
            self.motion_port,
            continuous_service,
            self.event_bus,
            task_runner=ThreadPoolTaskRunner(),
            motion_sync=EventBusMotionSynchronizer(self.event_bus),
            excitation_service=self.excitation_service,
        )

    def _wait_for_completion(self, timeout: float = 10.0) -> bool:
        done = threading.Event()
        self.event_bus.subscribe("scancompleted", lambda e: done.set())
        return done.wait(timeout=timeout)

    def test_differential_scan_toggles_dds_gain_off_then_on_on_the_wire(self):
        expected_gain = int(
            self.EXCITATION_LEVEL_PERCENT / 100.0 * AdapterExcitationConfigurationAD9106.MAX_EXCITATION_GAIN
        )

        scan_dto = Scan2DConfigDTO(
            x_min=0, x_max=1, x_nb_points=1,
            y_min=0, y_max=1, y_nb_points=1,
            scan_pattern="RASTER",
            stabilization_delay_ms=0,
            averaging_per_position=5,
            uncertainty_volts=1e-6,
            differential_mode=True,
            differential_settle_delay_ms=20,
        )

        self.assertTrue(self.service.execute_scan(scan_dto))
        self.assertTrue(self._wait_for_completion(), "Scan did not complete within timeout")

        ch1_writes = self.communicator.gain_writes(self.GAIN_ADDR_CH1)
        ch2_writes = self.communicator.gain_writes(self.GAIN_ADDR_CH2)

        # Pre-scan set_excitation already wrote the real gain once on each channel.
        self.assertIn(expected_gain, ch1_writes)
        self.assertIn(expected_gain, ch2_writes)

        # The scan loop must round-trip through zero (mute) and back to the
        # real gain (unmute) on the actual wire — proof the baseline window
        # is physically excitation-free, not just muted in the domain model.
        zero_index_ch1 = ch1_writes.index(0)
        zero_index_ch2 = ch2_writes.index(0)
        self.assertGreater(
            len(ch1_writes), zero_index_ch1 + 1,
            "No gain write after mute on DDS1 (Gain addr 53) — excitation never restored on the wire",
        )
        self.assertGreater(
            len(ch2_writes), zero_index_ch2 + 1,
            "No gain write after mute on DDS2 (Gain addr 52) — excitation never restored on the wire",
        )
        self.assertEqual(ch1_writes[zero_index_ch1 + 1], expected_gain)
        self.assertEqual(ch2_writes[zero_index_ch2 + 1], expected_gain)


if __name__ == "__main__":
    unittest.main()
