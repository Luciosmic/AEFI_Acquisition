"""Frequency sweep against the simulated MCU, through the real ADS131A04
adapter and the mock continuous acquisition (same stack as the throughput
characterization tests)."""

import unittest

from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from application.services.excitation_configuration_service.excitation_configuration_service import (
    ExcitationConfigurationService,
)
from application.services.frequency_sweep_service.dtos.frequency_sweep_dtos import FrequencySweepRequestDTO
from application.services.frequency_sweep_service.frequency_sweep_service import CONTROLLER, FrequencySweepService
from application.services.frequency_sweep_service.ports.i_frequency_sweep_output_port import IFrequencySweepOutputPort
from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode
from infrastructure.acquisition_conditions.fake.fake_acquisition_conditions import FakeAcquisitionConditionsPort
from infrastructure.in_memory_event_bus.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.fake.fake_thread_pool_task_runner import FakeThreadPoolTaskRunner
from infrastructure.hardware.micro_controller.ads131a04.adapter_i_acquistion_port_ads131a04 import ADS131A04Adapter
from infrastructure.hardware.micro_controller.fake.fake_acquisition_averaging_port import FakeAcquisitionAveragingPort
from infrastructure.hardware.micro_controller.fake.fake_mcu_serial_communicator import FakeMCUSerialCommunicator
from infrastructure.hardware.serial_link.fake.fake_usb_latency_timer_port import FakeUsbLatencyTimerPort
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.persistence.frequency_sweep.fake.fake_frequency_sweep_export_port import FakeFrequencySweepExportPort
from infrastructure.provenance.fake.fake_provenance import FakeSoftwareProvenancePort

OPERATOR_FREQUENCY_HZ = 1000.0
ADC_CONFIG = {
    "channels": {str(ch): {"gain": 1, "enabled": True} for ch in range(1, 9)},
    "oversampling_ratio": 4096,
    "reference_voltage": 2.442,
}
REQUEST = FrequencySweepRequestDTO(
    role="background", start_hz=100.0, stop_hz=10000.0, frequency_count=3, samples_per_frequency=4,
    table_height_mm=42.5, operator_name="Luis", operator_id="op-1",
)


class RecordingOutputPort(IFrequencySweepOutputPort):
    def __init__(self, on_point=None):
        self.steps, self.points, self.ended, self.failed = [], [], [], []
        self._on_point = on_point

    def present_frequency_sweep_step(self, message):
        self.steps.append(message)

    def present_frequency_point_measured(self, point):
        self.points.append(point)
        if self._on_point is not None:
            self._on_point(point)

    def present_frequency_sweep_ended(self, result):
        self.ended.append(result)

    def present_frequency_sweep_failed(self, reason):
        self.failed.append(reason)


class TestFrequencySweepService(unittest.TestCase):
    def setUp(self) -> None:
        self.event_bus = InMemoryEventBus()
        self.excitation_port = MockExcitationPort()
        self.excitation_service = ExcitationConfigurationService(self.excitation_port, self.event_bus)
        self.excitation_service.set_excitation(ExcitationMode.X_DIR, 40.0, 40.0, OPERATOR_FREQUENCY_HZ)
        communicator = FakeMCUSerialCommunicator(acquisition_delay_s=0.001, adc_output_rate_hz=2000.0)
        communicator.connect("COM_TEST")
        adc = ADS131A04Adapter(communicator, n_avg_reader=FakeAcquisitionAveragingPort(n_avg=1).get_n_avg)
        adc.load_config(ADC_CONFIG)
        self.acquisition_service = AefiAcquisitionService(MockAefiAcquisitionExecutor(self.event_bus), adc, self.event_bus)
        self.export = FakeFrequencySweepExportPort()
        self.output = RecordingOutputPort()
        self.published = []
        for topic in ("frequencypointacquired", "frequencysweepcompleted"):
            self.event_bus.subscribe(topic, self.published.append)

    def _service(self, **overrides):
        kwargs = dict(
            excitation_service=self.excitation_service,
            acquisition_service=self.acquisition_service,
            export_port=self.export,
            task_runner=FakeThreadPoolTaskRunner(),
            event_bus=self.event_bus,
            conditions_port=FakeAcquisitionConditionsPort(),
            software_provenance_port=FakeSoftwareProvenancePort(),
            usb_latency_timer_port=FakeUsbLatencyTimerPort(latency_ms=1.0),
            settle_delay_s=0.0,
            frequency_timeout_s=10.0,
        )
        kwargs.update(overrides)
        service = FrequencySweepService(**kwargs)
        service.set_output_port(self.output)
        return service

    def test_acquires_every_grid_frequency_with_the_operator_excitation(self):
        applied = []
        self.output = RecordingOutputPort(on_point=lambda p: applied.append(self.excitation_port.last_parameters))

        self._service().start_sweep(REQUEST)

        self.assertEqual(self.output.failed, [])
        self.assertEqual([p.frequency_hz for p in self.output.points], [100.0, 1000.0, 10000.0])
        self.assertEqual([p.frequency for p in applied], [100.0, 1000.0, 10000.0])
        self.assertTrue(all(p.mode == ExcitationMode.X_DIR and p.level_s1_s2.value == 40.0 for p in applied))
        self.assertTrue(all(p.samples_count == 4 and len(p.mean_v) == 6 and len(p.std_v) == 6 for p in self.output.points))
        (result,) = self.output.ended
        self.assertEqual((result.status, result.role, result.table_height_mm), ("completed", "background", 42.5))
        self.assertEqual(result.export_path, FakeFrequencySweepExportPort.LOCATION)

    def test_restores_the_operator_frequency_and_releases_the_controls(self) -> None:
        self._service().start_sweep(REQUEST)

        self.assertEqual(self.excitation_service.get_current_parameters().frequency, OPERATOR_FREQUENCY_HZ)
        self.assertIsNone(self.excitation_service.get_controller())
        self.assertIsNone(self.acquisition_service.get_controller())
        self.assertFalse(self.acquisition_service.is_acquisition_running())

    def test_publishes_one_event_per_frequency_then_completion(self) -> None:
        self._service().start_sweep(REQUEST)
        names = [type(e).__name__ for e in self.published]
        self.assertEqual(names, ["FrequencyPointAcquired"] * 3 + ["FrequencySweepCompleted"])

    def test_exports_raw_samples_and_the_parameters_of_the_sweep(self) -> None:
        self._service().start_sweep(REQUEST)

        self.assertEqual(self.export.opened, [("background", 42.5)])
        self.assertEqual(len(self.export.last_samples), 3 * 4)
        statuses = [w.activity.status for w in self.export.parameters_writes]
        self.assertEqual(statuses, ["running", "completed"])
        activity = self.export.last_parameters.activity
        self.assertEqual(activity.frequencies_hz, (100.0, 1000.0, 10000.0))
        self.assertEqual((activity.table_height_mm, activity.operator_name, activity.controller), (42.5, "Luis", CONTROLLER))
        self.assertEqual(activity.excitation.operator_frequency_hz, OPERATOR_FREQUENCY_HZ)
        self.assertTrue(activity.excitation_restored)
        self.assertEqual(activity.acquired_frequency_count, 3)
        self.assertEqual(self.export.last_parameters.files, FakeFrequencySweepExportPort.FILES)

    def test_stop_ends_the_sweep_after_the_current_frequency_and_exports_it(self):
        service = self._service()
        self.output = RecordingOutputPort(on_point=lambda p: service.stop_sweep())
        service.set_output_port(self.output)

        service.start_sweep(REQUEST)

        (result,) = self.output.ended
        self.assertEqual((result.status, len(result.points)), ("cancelled", 1))
        self.assertEqual(self.export.last_parameters.activity.status, "cancelled")
        self.assertEqual(self.excitation_service.get_current_parameters().frequency, OPERATOR_FREQUENCY_HZ)

    def test_refuses_without_table_height_and_starts_nothing(self) -> None:
        from dataclasses import replace

        self._service().start_sweep(replace(REQUEST, table_height_mm=None))

        self.assertIn("hauteur de la table", self.output.failed[0])
        self.assertEqual(self.export.opened, [])
        self.assertIsNone(self.excitation_service.get_controller())

    def test_refuses_an_excitation_that_is_off_or_custom(self) -> None:
        self.excitation_service.set_excitation(ExcitationMode.X_DIR, 0.0, 0.0, OPERATOR_FREQUENCY_HZ)
        self._service().start_sweep(REQUEST)
        self.excitation_service.set_excitation(ExcitationMode.CUSTOM, 40.0, 40.0, OPERATOR_FREQUENCY_HZ)
        self._service().start_sweep(REQUEST)

        self.assertIn("éteinte", self.output.failed[0])
        self.assertIn("personnalisé", self.output.failed[1])
        self.assertEqual(self.export.opened, [])

    def test_refused_while_a_scan_holds_the_excitation(self) -> None:
        self.excitation_service.take_control("scan")

        self._service().start_sweep(REQUEST)

        self.assertEqual(len(self.output.failed), 1)
        self.assertEqual(self.export.opened, [])
        self.assertIsNone(self.acquisition_service.get_controller())

    def test_a_frequency_without_samples_fails_and_exports_what_was_acquired(self):
        service = self._service(frequency_timeout_s=0.2)
        self.output = RecordingOutputPort(on_point=lambda p: self.acquisition_service.stop_acquisition(controller=CONTROLLER))
        service.set_output_port(self.output)

        service.start_sweep(REQUEST)

        self.assertIn("échantillons reçus", self.output.failed[0])
        self.assertEqual(self.export.last_parameters.activity.status, "failed")
        self.assertEqual(len(self.export.exports[-1][0].points), 1)
        self.assertEqual(self.excitation_service.get_current_parameters().frequency, OPERATOR_FREQUENCY_HZ)


if __name__ == "__main__":
    unittest.main()
