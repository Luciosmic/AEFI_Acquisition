import unittest
from types import SimpleNamespace
from uuid import uuid4

from application.services.sensor_calibration_service.dtos.sensor_calibration_dto import ActiveSensorRotationDTO
from domain.calibration.entities.hardware_component_selection.hardware_component_selection import (
    HardwareComponentSelection,
)
from domain.calibration.entities.sensor_calibration_entry.sensor_calibration_entry import SensorCalibrationEntry
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import HardwareComponentKind
from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import SensorRotationAngles
from infrastructure.acquisition_conditions.acquisition_conditions_reader import AcquisitionConditionsReader
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.persistence.calibration.fake.fake_hardware_component_repository import (
    FakeHardwareComponentRepository,
)
from infrastructure.persistence.calibration.fake.fake_sensor_calibration_repository import (
    FakeSensorCalibrationRepository,
)

# Shape of AcquisitionSnapshotReader.read() (committed contract).
SNAPSHOT = {
    "hardware_configuration": {
        "adc": {
            "component_name": "ADS131A04", "entry_id": "e-adc", "recorded_at": "2026-09-30T08:00:00+00:00",
            "characterization": {"full_scale_v": 2.442, "noise_v_rms": None}, "units": {"full_scale_v": "V", "noise_v_rms": "V RMS"},
        },
        "microcontroller": {
            "component_name": "MCU AEFI", "entry_id": "e-mcu", "recorded_at": "2026-09-30T08:00:00+00:00",
            "characterization": {"optimal_acquisition_rate_per_s": ((1, 130.0), (8, 110.0))},
            "units": {"optimal_acquisition_rate_per_s": "mesures/s"},
        },
    },
    "hardware_settings": {
        "ads131a04": {
            "reference_voltage": 2.442, "reference_source": "Internal", "high_resolution": True,
            "negative_charge_pump": False, "clkin_divider": 2, "iclk_divider": 2, "oversampling_ratio": 1024,
            "channels": {str(ch): {"gain": 2, "enabled": True} for ch in range(1, 9)},
        },
        "ad9106": {"link_dds1_dds2": True, "enforce_dds3_dds4_quadrature": True},
    },
}
AD9106_MEMORY = {
    "DDS": {
        "Frequence": 1000, "Mode": {ch: "AC" for ch in (1, 2, 3, 4)},
        "Gain": {1: 0, 2: 0, 3: 10000, 4: 10000}, "Offset": {ch: 0 for ch in (1, 2, 3, 4)},
        "Phase": {1: 0, 2: 32768, 3: 16384, 4: 0}, "Const": {ch: 0 for ch in (1, 2, 3, 4)},
    }
}


def _raise(error):
    def fail(*_args, **_kwargs):
        raise error

    return fail


class TestAcquisitionConditionsReader(unittest.TestCase):
    def setUp(self):
        self.components = FakeHardwareComponentRepository()
        self.mounting = HardwareComponentSelection.now(HardwareComponentKind.SENSOR, "capteur cube 8 mm")
        self.components.add_selection(self.mounting)
        self.calibrations = FakeSensorCalibrationRepository()
        self.entry = SensorCalibrationEntry.single(self.mounting.mounting_id, uuid4(), SensorRotationAngles(1.0, 2.0, 3.0))
        self.calibrations.add(self.entry)
        self.rotation = ActiveSensorRotationDTO(1.0, 2.0, 3.0, is_calibrated=True, is_trial=False,
                                                recorded_at=self.entry.recorded_at, mounting_matrix=())

    def reader(self, **overrides):
        kwargs = dict(
            snapshot_reader=SimpleNamespace(read=lambda: SNAPSHOT),
            hardware_component_repository=self.components,
            sensor_calibration_repository=self.calibrations,
            active_rotation=lambda: self.rotation,
            compensation_enabled=lambda: False,
            ad9106_memory_state=lambda: AD9106_MEMORY,
            oversampling_ratio=lambda: 4096,
            serial_communicator=SimpleNamespace(port="COM10", baudrate=1500000),
            motion_port=MockMotionPort(),
            hardware_backends={"aefi_device": "real"},
        )
        kwargs.update(overrides)
        return AcquisitionConditionsReader(**kwargs)

    def test_motors_settings_from_the_arcus_and_motion_configs(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest import mock

        from infrastructure.acquisition_conditions import acquisition_conditions_reader as module

        with tempfile.TemporaryDirectory() as tmp:
            arcus, motion = Path(tmp) / "arcus.json", Path(tmp) / "motion.json"
            arcus.write_text(json.dumps({
                "microns_per_step": 21.8, "x_ls": 10, "x_hs": 1500, "x_acc": 300, "x_dec": 300,
                "y_ls": 20, "y_hs": 1000, "y_acc": 200, "y_dec": 250,
            }), encoding="utf-8")
            motion.write_text(json.dumps({"speed_mode": "fast", "referential_mode": "centered"}), encoding="utf-8")
            with mock.patch.object(module, "ARCUS_CONFIG", arcus), mock.patch.object(module, "MOTION_CONFIG", motion):
                motors = self.reader().read_conditions().motors
        self.assertEqual(motors.microns_per_step, 21.8)
        self.assertEqual(motors.y.deceleration_ms, 250.0)
        self.assertEqual((motors.speed_mode, motors.referential), ("fast", "centered"))

    def test_missing_arcus_config_makes_the_motors_unknown_with_a_reason(self):
        from pathlib import Path
        from unittest import mock

        from infrastructure.acquisition_conditions import acquisition_conditions_reader as module

        with mock.patch.object(module, "ARCUS_CONFIG", Path("does/not/exist.json")):
            conditions = self.reader().read_conditions()
        self.assertIsNone(conditions.motors)
        self.assertIn("motors", conditions.unknown)

    def test_catalog_comes_from_the_snapshot_with_every_kind(self):
        conditions = self.reader().read_conditions()
        by_kind = {c.kind: c for c in conditions.components}
        self.assertEqual(set(by_kind), {k.value for k in HardwareComponentKind})
        self.assertEqual(by_kind["adc"].entry_id, "e-adc")
        self.assertIsNone(by_kind["sensor"].name)  # absent from the snapshot = nothing mounted
        self.assertEqual(by_kind["microcontroller"].curve_x_labels, {"optimal_acquisition_rate_per_s": "n_avg"})

    def test_adc_osr_is_the_controller_memory_not_the_file(self):
        adc = self.reader().read_conditions().adc
        self.assertEqual(adc.oversampling_ratio, 4096)
        self.assertEqual(adc.channel_gains["5"], 2)

    def test_ad9106_comes_from_controller_memory_with_policy_flags(self):
        chip = self.reader().read_conditions().signal_generation
        self.assertEqual(chip.channels["1"].gain_code, 0)
        self.assertEqual(chip.channels["3"].phase_code, 16384)
        self.assertTrue(chip.link_dds1_dds2)
        self.assertIsNone(chip.link_dds3_dds4_gain)  # not in the resolved config: unknown

    def test_sensor_deployment_names_the_applied_calibration(self):
        deployment = self.reader().read_conditions().sensor_deployment
        self.assertEqual(deployment.mounting_id, str(self.mounting.mounting_id))
        self.assertEqual(deployment.rotation_origin, "calibrated")
        self.assertEqual(deployment.calibration_id, str(self.entry.entry_id))

    def test_host_link_from_the_communicator(self):
        link = self.reader().read_conditions().host_link
        self.assertEqual((link.serial_port, link.baud_rate), ("COM10", 1500000))

    def test_simulated_transport_has_no_port(self):
        link = self.reader(serial_communicator=SimpleNamespace(ser=None)).read_conditions().host_link
        self.assertIsNone(link.serial_port)

    def test_a_failing_source_is_unknown_with_its_reason_and_the_rest_is_read(self):
        conditions = self.reader(
            snapshot_reader=SimpleNamespace(read=_raise(OSError("disque illisible"))),
            ad9106_memory_state=_raise(KeyError("DDS")),
        ).read_conditions()
        self.assertEqual(conditions.components, ())
        self.assertIn("disque illisible", conditions.unknown["components"])
        self.assertIsNone(conditions.adc)
        self.assertIn("adc", conditions.unknown)
        self.assertIsNone(conditions.signal_generation)
        self.assertIn("KeyError", conditions.unknown["signal_generation"])
        self.assertIsNotNone(conditions.sensor_deployment)

    def test_bench_position(self):
        self.assertEqual(self.reader().read_bench_position().value.x_mm, 0.0)

    def test_disconnected_motors_are_a_failure(self):
        motion = SimpleNamespace(get_current_position=_raise(RuntimeError("Arcus controller not connected")))
        result = self.reader(motion_port=motion).read_bench_position()
        self.assertTrue(result.is_failure)
        self.assertIn("not connected", result.error)


if __name__ == "__main__":
    unittest.main()
