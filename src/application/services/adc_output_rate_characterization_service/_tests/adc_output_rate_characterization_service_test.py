"""ODR characterization against the simulated ADC register and DRDY capture."""

import unittest
from types import SimpleNamespace

from application.services.adc_output_rate_characterization_service.adc_output_rate_characterization_service import (
    CONTROLLER,
    AdcOutputRateCharacterizationService,
)
from application.services.adc_output_rate_characterization_service.dtos.adc_output_rate_dtos import (
    AdcOutputRateRequestDTO,
)
from application.services.adc_output_rate_characterization_service.ports.i_adc_output_rate_output_port import (
    IAdcOutputRateOutputPort,
)
from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from application.services.aefi_acquisition_service.dtos.aefi_acquisition_dtos import AefiAcquisitionConfig
from application.services.hardware_configuration_service.hardware_configuration_service import (
    HardwareConfigurationService,
)
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.fake.fake_thread_pool_task_runner import FakeThreadPoolTaskRunner
from infrastructure.hardware.micro_controller.ads131a04.fake.fake_adc_oversampling_port import FakeAdcOversamplingPort
from infrastructure.hardware.oscilloscope_dsox2014.fake.fake_drdy_capture_port import FakeDrdyCapturePort
from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor
from infrastructure.persistence.adc_output_rate.fake.fake_adc_output_rate_export_port import (
    FakeAdcOutputRateExportPort,
)

F_MOD = 4.096e6


class RecordingOutputPort(IAdcOutputRateOutputPort):
    def __init__(self):
        self.steps, self.points, self.succeeded, self.failed = [], [], [], []

    def present_output_rate_step(self, message):
        self.steps.append(message)

    def present_output_rate_point_measured(self, point):
        self.points.append(point)

    def present_output_rate_characterization_succeeded(self, result):
        self.succeeded.append(result)

    def present_output_rate_characterization_failed(self, reason):
        self.failed.append(reason)


class TestAdcOutputRateCharacterization(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.osr = FakeAdcOversamplingPort(oversampling_ratio=4096)
        self.capture = FakeDrdyCapturePort(self.osr.get_oversampling_ratio)
        self.export = FakeAdcOutputRateExportPort()
        self.acquisition = AefiAcquisitionService(
            MockAefiAcquisitionExecutor(self.event_bus), RandomNoiseAcquisitionPort(noise_std=0.0, seed=1), self.event_bus
        )
        self.hardware_configuration = HardwareConfigurationService([SimpleNamespace(hardware_id="ads131a04")], self.event_bus)
        self.output = RecordingOutputPort()

    def tearDown(self):
        self.acquisition.stop_acquisition()

    def _run(self, request=AdcOutputRateRequestDTO(), **overrides):
        kwargs = dict(oversampling_port=self.osr, capture_port=self.capture, export_port=self.export,
                      acquisition_service=self.acquisition, hardware_configuration=self.hardware_configuration,
                      task_runner=FakeThreadPoolTaskRunner(), settle_delay_s=0.0)
        kwargs.update(overrides)
        service = AdcOutputRateCharacterizationService(**kwargs)
        service.set_output_port(self.output)
        service.start_characterization(request)

    def test_current_osr_only_changes_nothing(self):
        self._run()
        self.assertEqual(self.output.failed, [])
        (point,) = self.output.points
        self.assertEqual(point.oversampling_ratio, 4096)
        self.assertAlmostEqual(point.output_rate_hz, 1000.0, delta=0.01)
        self.assertEqual(self.osr.history, [4096])  # only the final restore, same value

    def test_sweep_measures_each_osr_and_finds_one_modulator_frequency(self):
        self._run(AdcOutputRateRequestDTO(oversampling_ratios=(4096, 512, 32)))
        result = self.output.succeeded[0]
        self.assertEqual([p.oversampling_ratio for p in result.points], [4096, 512, 32])
        for p in result.points:
            self.assertAlmostEqual(p.output_rate_hz, F_MOD / p.oversampling_ratio, delta=1e-3 * F_MOD / p.oversampling_ratio)
        self.assertAlmostEqual(result.mean_modulator_frequency_hz, F_MOD, delta=1e-3 * F_MOD)
        self.assertLess(result.max_modulator_frequency_relative_deviation, 1e-3)
        curve = result.component_values["output_data_rate_hz"]
        self.assertEqual([osr for osr, _ in curve], [4096, 512, 32])

    def test_capture_window_follows_the_expected_period(self):
        self._run(AdcOutputRateRequestDTO(oversampling_ratios=(4096, 32), periods_per_capture=50))
        windows = [r.window_s for r in self.capture.requests]
        self.assertAlmostEqual(windows[0], 50 * 4096 / F_MOD, delta=1e-6)
        self.assertAlmostEqual(windows[1], 50 * 32 / F_MOD, delta=1e-6)

    def test_osr_not_applied_by_the_chip_shows_as_a_modulator_frequency_deviation(self):
        self.capture = FakeDrdyCapturePort(self.osr.get_oversampling_ratio, applied_oversampling_ratio=4096)
        self._run(AdcOutputRateRequestDTO(oversampling_ratios=(4096, 512)))
        self.assertGreater(self.output.succeeded[0].max_modulator_frequency_relative_deviation, 0.5)

    def test_restores_the_original_osr_and_releases_everything(self):
        self._run(AdcOutputRateRequestDTO(oversampling_ratios=(2048, 32)))
        self.assertEqual(self.osr.get_oversampling_ratio(), 4096)
        self.assertEqual(self.osr.history, [2048, 32, 4096])
        self.assertIsNone(self.hardware_configuration.get_controller("ads131a04"))
        self.assertIsNone(self.acquisition.get_controller())
        self.assertEqual(self.output.succeeded[0].restored_oversampling_ratio, 4096)

    def test_adc_configuration_is_locked_during_the_sweep(self):
        locked = []
        self.output.present_output_rate_point_measured = lambda point: locked.append(
            (self.hardware_configuration.get_controller("ads131a04"), self.acquisition.get_controller())
        )
        self._run(AdcOutputRateRequestDTO(oversampling_ratios=(4096, 512)))
        self.assertEqual(locked, [(CONTROLLER, CONTROLLER)] * 2)

    def test_sweep_refused_while_continuous_reading_runs(self):
        self.acquisition.start_acquisition(AefiAcquisitionConfig())
        self._run(AdcOutputRateRequestDTO(oversampling_ratios=(4096, 512)))
        self.assertIn("lecture continue", self.output.failed[0])
        self.assertEqual(self.osr.history, [])
        self.assertIsNone(self.acquisition.get_controller())

    def test_no_instrument_fails_and_still_restores(self):
        self.capture = FakeDrdyCapturePort(self.osr.get_oversampling_ratio, fail_reason="aucun oscilloscope VISA détecté")
        self._run(AdcOutputRateRequestDTO(oversampling_ratios=(512,)))
        self.assertIn("aucun oscilloscope", self.output.failed[0])
        self.assertEqual(self.osr.get_oversampling_ratio(), 4096)
        self.assertIsNone(self.hardware_configuration.get_controller("ads131a04"))

    def test_invalid_requests_are_refused_before_touching_anything(self):
        for request in (
            AdcOutputRateRequestDTO(scope_channel=5),
            AdcOutputRateRequestDTO(probe_ratio=0),
            AdcOutputRateRequestDTO(oversampling_ratios=(1000,)),
            AdcOutputRateRequestDTO(periods_per_capture=2),
        ):
            self._run(request)
        self.assertEqual(len(self.output.failed), 4)
        self.assertEqual(self.capture.requests, [])
        self.assertIsNone(self.hardware_configuration.get_controller("ads131a04"))

    def test_export_receives_every_capture(self):
        self._run(AdcOutputRateRequestDTO(oversampling_ratios=(4096, 64)))
        result, captures = self.export.exports[0]
        self.assertEqual([osr for osr, _ in captures], [4096, 64])
        self.assertEqual(self.output.succeeded[0].export_path, FakeAdcOutputRateExportPort.LOCATION)


if __name__ == "__main__":
    unittest.main()
