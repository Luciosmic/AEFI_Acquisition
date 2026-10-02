"""Throughput characterization against the simulated MCU: T(n) = T0 + n/ODR,
white noise averaged as 1/√n (FakeMCUSerialCommunicator), through the real
ADS131A04 adapter and the mock continuous acquisition."""

import unittest
from types import SimpleNamespace

from application.services.acquisition_throughput_characterization_service.acquisition_throughput_characterization_service import (
    CONTROLLER,
    AcquisitionThroughputCharacterizationService,
)
from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    AcquisitionThroughputRequestDTO,
)
from application.services.acquisition_throughput_characterization_service.ports.i_acquisition_throughput_output_port import (
    IAcquisitionThroughputOutputPort,
)
from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from application.services.excitation_configuration_service.excitation_configuration_service import (
    ExcitationConfigurationService,
)
from application.services.hardware_configuration_service.hardware_configuration_service import (
    HardwareConfigurationService,
)
from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.fake.fake_thread_pool_task_runner import FakeThreadPoolTaskRunner
from infrastructure.hardware.micro_controller.ads131a04.adapter_i_acquistion_port_ads131a04 import ADS131A04Adapter
from infrastructure.hardware.micro_controller.fake.fake_acquisition_averaging_port import FakeAcquisitionAveragingPort
from infrastructure.hardware.micro_controller.fake.fake_mcu_serial_communicator import FakeMCUSerialCommunicator
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.persistence.acquisition_throughput.fake.fake_acquisition_throughput_export_port import (
    FakeAcquisitionThroughputExportPort,
)

ADC_OUTPUT_RATE_HZ = 2000.0
OPERATOR_N_AVG = 127
GRID = (1, 8, 32)
ADC_CONFIG = {
    "channels": {str(ch): {"gain": 1, "enabled": True} for ch in range(1, 9)},
    "oversampling_ratio": 4096,
    "reference_voltage": 2.442,
}


class RecordingOutputPort(IAcquisitionThroughputOutputPort):
    def __init__(self, on_point=None):
        self.steps, self.points, self.succeeded, self.failed = [], [], [], []
        self._on_point = on_point

    def present_throughput_characterization_step(self, message):
        self.steps.append(message)

    def present_throughput_point_measured(self, point):
        self.points.append(point)
        if self._on_point is not None:
            self._on_point()

    def present_throughput_characterization_succeeded(self, result):
        self.succeeded.append(result)

    def present_throughput_characterization_failed(self, reason):
        self.failed.append(reason)


class TestAcquisitionThroughputCharacterization(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.excitation_port = MockExcitationPort()
        self.excitation_service = ExcitationConfigurationService(self.excitation_port, self.event_bus)
        self.excitation_service.set_excitation(ExcitationMode.X_DIR, 40.0, 40.0, 1000.0)

        self.averaging = FakeAcquisitionAveragingPort(n_avg=OPERATOR_N_AVG)
        communicator = FakeMCUSerialCommunicator(
            acquisition_delay_s=0.002, adc_output_rate_hz=ADC_OUTPUT_RATE_HZ, noise_std_counts=200.0
        )
        communicator.connect("COM_TEST")
        adc = ADS131A04Adapter(communicator, n_avg_reader=self.averaging.get_n_avg)
        adc.load_config(ADC_CONFIG)
        self.acquisition_service = AefiAcquisitionService(MockAefiAcquisitionExecutor(self.event_bus), adc, self.event_bus)
        # Only the ids matter to the lock: no configuration is applied in these tests.
        self.hardware_configuration = HardwareConfigurationService(
            [SimpleNamespace(hardware_id="mcu"), SimpleNamespace(hardware_id="ads131a04")], self.event_bus
        )
        self.export = FakeAcquisitionThroughputExportPort()
        self.output = RecordingOutputPort()

    def _make_service(self, **overrides):
        kwargs = dict(
            excitation_service=self.excitation_service,
            acquisition_service=self.acquisition_service,
            averaging_port=self.averaging,
            export_port=self.export,
            task_runner=FakeThreadPoolTaskRunner(),
            event_bus=self.event_bus,
            hardware_configuration=self.hardware_configuration,
            settle_delay_s=0.0,
            sample_timeout_s=10.0,
        )
        kwargs.update(overrides)
        service = AcquisitionThroughputCharacterizationService(**kwargs)
        service.set_output_port(self.output)
        return service

    def _run(self, request=AcquisitionThroughputRequestDTO(n_avg_values=GRID, samples_per_point=12), **overrides):
        self._make_service(**overrides).start_characterization(request)

    def test_measures_every_n_avg_and_recovers_the_adc_output_rate(self):
        self._run()

        self.assertEqual(self.output.failed, [])
        self.assertEqual([p.n_avg for p in self.output.points], list(GRID))
        result = self.output.succeeded[0]
        self.assertAlmostEqual(result.adc_output_rate_hz, ADC_OUTPUT_RATE_HZ, delta=0.25 * ADC_OUTPUT_RATE_HZ)
        periods = [p.sample_period_s for p in result.points]
        self.assertEqual(periods, sorted(periods))  # more averaging, slower output

    def test_averaging_lowers_the_noise_per_sample(self):
        self._run()
        noise = {p.n_avg: max(p.noise_v_rms) for p in self.output.points}
        self.assertLess(noise[32], noise[1] / 2)

    def test_result_carries_the_measurement_context_and_component_values(self):
        self._run()
        result = self.output.succeeded[0]
        self.assertEqual(result.oversampling_ratio, 4096)
        self.assertEqual(result.excitation, "coupée")
        self.assertEqual(result.export_path, FakeAcquisitionThroughputExportPort.LOCATION)
        curve = result.component_values["optimal_acquisition_rate_per_s"]
        self.assertEqual([n for n, _ in curve], list(GRID))
        self.assertAlmostEqual(result.component_values["max_acquisition_rate_per_s"], max(r for _, r in curve))

    def test_raw_samples_are_exported_per_n_avg(self):
        self._run()
        samples = self.export.last_samples
        self.assertEqual({s.n_avg for s in samples}, set(GRID))
        self.assertEqual(len(samples), 12 * len(GRID))
        self.assertEqual(len(samples[0].values_v), 6)

    def test_excitation_is_cut_during_the_sweep_then_restored(self):
        def applied_levels():
            params = self.excitation_port.last_parameters
            return params.level_s1_s2.value, params.level_s3_s4.value

        levels_while_measuring = []
        self.output = RecordingOutputPort(on_point=lambda: levels_while_measuring.append(applied_levels()))
        controllers = []
        self.event_bus.subscribe("excitationcontrolchanged", lambda e: controllers.append(e.controller))
        before = self.excitation_service.get_current_parameters()

        self._run()

        self.assertEqual(levels_while_measuring, [(0.0, 0.0)] * len(GRID))
        self.assertEqual(applied_levels(), (40.0, 40.0))
        self.assertEqual(controllers, [CONTROLLER, None])
        self.assertEqual(self.excitation_service.get_current_parameters(), before)

    def test_stream_and_n_avg_osr_settings_cannot_be_changed_by_hand_during_the_sweep(self):
        """2026-10-02 on the bench: a manual Stop in Continuous Reading stalled
        a characterization for 58 s. During the sweep, Stop and the Hardware
        Advanced Config of n_avg / OSR are refused."""
        attempts = []

        def try_by_hand():
            attempts.append((
                self.acquisition_service.stop_acquisition().is_failure,
                self.hardware_configuration.apply_config("mcu", {"n_avg": 4}).is_failure,
                self.hardware_configuration.reset_to_default("ads131a04").is_failure,
            ))

        self.output = RecordingOutputPort(on_point=try_by_hand)

        self._run()

        self.assertEqual(self.output.failed, [])
        self.assertEqual(attempts, [(True, True, True)] * len(GRID))
        self.assertIsNone(self.acquisition_service.get_controller())
        self.assertIsNone(self.hardware_configuration.get_controller("mcu"))
        self.assertIsNone(self.hardware_configuration.get_controller("ads131a04"))

    def test_refused_while_the_stream_is_controlled_and_takes_nothing(self):
        self.acquisition_service.take_control("scan")

        self._run()

        self.assertIn("scan", self.output.failed[0])
        self.assertIsNone(self.excitation_service.get_controller())  # given back
        self.assertIsNone(self.hardware_configuration.get_controller("mcu"))

    def test_restores_the_operator_n_avg_and_stops_the_acquisition_it_started(self):
        self._run()
        self.assertEqual(self.averaging.get_n_avg(), OPERATOR_N_AVG)
        self.assertEqual(self.averaging.history, [*GRID, OPERATOR_N_AVG])
        self.assertFalse(self.acquisition_service.is_acquisition_running())

    def test_refused_while_a_scan_controls_the_excitation(self):
        self.excitation_service.take_control("scan")

        self._run()

        self.assertIn("scan", self.output.failed[0])
        self.assertEqual(self.averaging.history, [])
        self.assertEqual(self.excitation_service.get_controller(), "scan")

    def test_invalid_grids_are_refused_before_touching_anything(self):
        for request in (
            AcquisitionThroughputRequestDTO(n_avg_values=(8, 8), samples_per_point=12),
            AcquisitionThroughputRequestDTO(n_avg_values=(1, 200), samples_per_point=12),
            AcquisitionThroughputRequestDTO(n_avg_values=(1, 8), samples_per_point=2),
        ):
            self._run(request)
        self.assertEqual(len(self.output.failed), 3)
        self.assertEqual(self.averaging.history, [])
        self.assertIsNone(self.excitation_service.get_controller())

    def test_unwritable_n_avg_fails_and_still_restores_everything(self):
        self.averaging = FakeAcquisitionAveragingPort(n_avg=OPERATOR_N_AVG, fail_on_set=True)

        self._run(averaging_port=self.averaging)

        self.assertEqual(len(self.output.failed), 1)
        self.assertIn("non inscriptible", self.output.failed[0])
        self.assertIsNone(self.excitation_service.get_controller())
        self.assertFalse(self.acquisition_service.is_acquisition_running())

    def test_export_failure_keeps_the_result(self):
        self._run(export_port=FakeAcquisitionThroughputExportPort(fail=True))
        self.assertEqual(len(self.output.succeeded), 1)
        self.assertIsNone(self.output.succeeded[0].export_path)


if __name__ == "__main__":
    unittest.main()
