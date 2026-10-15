"""
BarTransmissionCalibrationService on fakes sharing a virtual clock: a fake
motor axis, a fake LIDAR seeing a noisy square wave (bar) as a function of the
fake axis position, in-memory repositories, synchronous task runner.
"""

import math
import random

import pytest

from application.services.bar_transmission_calibration_service.bar_transmission_calibration_service import (
    BarTransmissionCalibrationService,
)
from application.services.bar_transmission_calibration_service.dtos.bar_transmission_calibration_dtos import (
    BarCalibrationSettingsDTO,
)
from application.services.bar_transmission_calibration_service.errors.bar_transmission_calibration_error import (
    BarNotFound,
    BenchMotionFailed,
    InvalidMeasurementRequest,
    LidarStreamBusy,
    LidarUnavailable,
    MeasurementCancelled,
    MeasurementsNotComparable,
    MotionChainIncomplete,
    PositiveLimitNotReached,
    ScanRunning,
)
from application.services.bar_transmission_calibration_service.ports.i_bar_transmission_calibration_output_port import (
    IBarTransmissionCalibrationOutputPort,
)
from application.shared.exclusive_control.exclusive_control import ExclusiveControl
from domain.calibration.calibration import Calibration
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import HardwareComponentKind
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.fake.fake_clock import FakeClock
from infrastructure.execution.fake.fake_thread_pool_task_runner import FakeThreadPoolTaskRunner
from infrastructure.hardware.arcus_performax_4EX.fake.fake_raw_increment_motion_port import (
    FakeRawIncrementMotionPort,
)
from infrastructure.hardware.lsm9ds1.fake.fake_lidar_distance_port import FakeLidarDistancePort
from infrastructure.persistence.calibration.fake.fake_hardware_component_repository import (
    FakeHardwareComponentRepository,
)
from infrastructure.persistence.calibration.fake.fake_mechanical_transmission_calibration_repository import (
    FakeMechanicalTransmissionCalibrationRepository,
)

TRAVEL = 8_000
# Edges off the fly scan sampling grid: an edge exactly at a coarse front makes the first probe undecidable.
BAR = {"X": (2_010.4, 6_010.4), "Y": (1_513.6, 5_522.1)}
# 87.2 mm over 4000 increments = 21.8 µm/increment -> 69.76 mm/rev at 200 steps x 16 microsteps
BAR_LENGTH_MM = 87.2
SETTINGS = BarCalibrationSettingsDTO(settle_time_s=0.3, samples_per_point=6, k_sigma=3.0,
                                     fly_speed_increments_per_s=800, coarse_margin_s=0.5)


class Recorder(IBarTransmissionCalibrationOutputPort):
    def __init__(self):
        self.progress, self.measured, self.failed = [], [], []
        self.on_progress = None

    def present_measurement_progress(self, axis, message):
        self.progress.append(message)
        if self.on_progress:
            self.on_progress(message)

    def present_axis_measured(self, result):
        self.measured.append(result)

    def present_axis_failed(self, axis, error):
        self.failed.append(error)


def mount(components, kind, name, values):
    calibration = Calibration()
    components.add(calibration.record_hardware_component_characterization(kind, name, values))
    mounted = Calibration.mounted_component_name(components.find_selections(kind))
    components.add_selection(calibration.mount_hardware_component(kind, name, {name}, mounted))


class Bench:
    def __init__(self, bar_present=True, noise_mm=2.0, **motion_options):
        self.clock = FakeClock()
        self.motion = FakeRawIncrementMotionPort(clock=self.clock, plus_limit_increments=TRAVEL, **motion_options)
        self.rng = random.Random(7)
        self.bar_present = bar_present
        self.noise_mm = noise_mm
        self.axis = "X"
        self.lidar = FakeLidarDistancePort(self.distance_mm, self.clock)
        self.components = FakeHardwareComponentRepository()
        self.transmissions = FakeMechanicalTransmissionCalibrationRepository()
        self.bus = InMemoryEventBus()
        self.events = []
        self.bus.subscribe("mechanicaltransmissioncalibrationentryadded", self.events.append)
        self.control = ExclusiveControl("flux LIDAR", lambda owner: None)
        self.output = Recorder()
        self.service = BarTransmissionCalibrationService(
            self.motion, self.lidar, self.transmissions, self.components, self.bus,
            FakeThreadPoolTaskRunner(), lidar_stream_control=self.control, clock=self.clock,
        )
        self.service.set_output_port(self.output)

    def distance_mm(self):
        """Bar 1 m above the floor: 250 mm on the bar, 1250 mm off; spot softens the edges."""
        if not self.bar_present:
            return 1250.0 + self.rng.gauss(0.0, self.noise_mm)
        n = self.motion.get_position(self.axis)
        start, end = BAR[self.axis]
        coverage = _sigmoid((n - start) / 3.0) * _sigmoid((end - n) / 3.0)
        return 1250.0 - 1000.0 * coverage + self.rng.gauss(0.0, self.noise_mm)

    def mount_chain(self, microsteps=16):
        mount(self.components, HardwareComponentKind.MOTORS, "Igus", {"full_steps_per_revolution": 200})
        mount(self.components, HardwareComponentKind.STEPPER_DRIVER, "TB6600", {"max_current_a": 3.5})
        self.record_setting(microsteps)
        return self

    def record_setting(self, microsteps):
        motor = Calibration.current_mounting(self.components.find_selections(HardwareComponentKind.MOTORS))
        driver = Calibration.current_mounting(self.components.find_selections(HardwareComponentKind.STEPPER_DRIVER))
        self.transmissions.add(Calibration().record_mechanical_transmission_calibration_entry(
            motor.mounting_id, driver.mounting_id, microsteps, 3.5, 4.0, 70.0
        ))

    def measure(self, axis="X", settings=SETTINGS, length=BAR_LENGTH_MM, length_uncertainty=0.0):
        self.axis = axis
        return self.service.measure_axis(axis, length, length_uncertainty, settings)


def _sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x)) if x > -60 else 0.0


@pytest.fixture
def bench():
    return Bench().mount_chain()


def test_measures_n_and_the_transmission_with_its_uncertainty(bench):
    result = bench.measure("X")

    assert result.is_success
    assert bench.output.failed == []
    measured = bench.output.measured[0]
    true_n = BAR["X"][1] - BAR["X"][0]
    assert abs(measured.increments_between_fronts - true_n) <= measured.increments_uncertainty + 2
    assert measured.increments_uncertainty < 20
    assert measured.travel_per_motor_revolution_mm == pytest.approx(69.76, rel=5e-3)
    assert measured.threshold_mm == pytest.approx(750.0, abs=2.0)
    assert (measured.microsteps, measured.full_steps_per_revolution) == (16, 200.0)
    assert bench.motion.get_position("X") == 0  # parked at the origin
    assert (bench.lidar.open_count, bench.lidar.close_count) == (1, 1)
    assert not bench.service.is_measuring()
    assert bench.control.controller is None


def test_brackets_are_oriented_bar_side_then_floor_side(bench):
    bench.measure("X")
    measured = bench.output.measured[0]
    first, second = measured.first_front, measured.second_front
    assert first.on_bar_increment > first.off_bar_increment  # bar after the first front
    assert second.on_bar_increment < second.off_bar_increment  # bar before the second front
    assert abs(first.center_increment - BAR["X"][0]) <= first.half_width_increments + 1


def test_lidar_stream_is_held_during_the_measurement(bench):
    owners = []
    bench.output.on_progress = lambda message: owners.append(bench.control.controller)
    bench.measure("X")
    assert set(owners) == {"calibration de la transmission (barre)"}
    assert bench.control.controller is None


def test_refuses_when_the_panel_streams_the_lidar(bench):
    bench.lidar.streamed_elsewhere = True
    result = bench.measure("X")
    assert isinstance(result.error, LidarStreamBusy)
    assert not bench.motion.homed["X"]
    assert bench.lidar.open_count == 0


def test_refuses_when_another_owner_holds_the_stream(bench):
    bench.control.take("panneau")
    result = bench.measure("X")
    assert isinstance(result.error, LidarStreamBusy)


def test_refuses_during_a_scan(bench):
    bench.bus.publish("scanstarted", object())
    assert isinstance(bench.measure("X").error, ScanRunning)
    bench.bus.publish("scancompleted", object())
    assert bench.measure("X").is_success


def test_refuses_without_a_complete_motion_chain():
    bare = Bench()
    assert isinstance(bare.measure("X").error, MotionChainIncomplete)


def test_refuses_invalid_settings(bench):
    result = bench.measure("X", settings=BarCalibrationSettingsDTO(samples_per_point=1))
    assert isinstance(result.error, InvalidMeasurementRequest)
    assert isinstance(bench.measure("Z").error, InvalidMeasurementRequest)
    assert isinstance(bench.measure("X", length=0.0).error, InvalidMeasurementRequest)


def test_absent_bar_fails_typed_and_closes_the_stream():
    bench = Bench(bar_present=False).mount_chain()
    assert bench.measure("X").is_success  # started; the outcome comes through the output port
    assert isinstance(bench.output.failed[0], BarNotFound)
    assert bench.lidar.close_count == 1
    assert bench.control.controller is None


def test_axis_stopping_without_limit_switch_fails_typed():
    bench = Bench(limit_switch_present=False).mount_chain()
    bench.measure("X")
    assert isinstance(bench.output.failed[0], PositiveLimitNotReached)


def test_motion_failure_is_translated_and_releases_everything():
    bench = Bench(fail_on={"home"}).mount_chain()
    bench.measure("X")
    assert isinstance(bench.output.failed[0], BenchMotionFailed)
    assert bench.lidar.close_count == 1
    assert bench.control.controller is None
    assert not bench.service.is_measuring()


def test_silent_lidar_fails_typed(bench):
    bench.lidar._silent_after = 20
    bench.measure("X")
    assert isinstance(bench.output.failed[0], LidarUnavailable)


def test_cancel_stops_the_measurement(bench):
    bench.output.on_progress = lambda message: bench.service.cancel_measurement() if "Fly scan" in message else None
    bench.measure("X")
    assert isinstance(bench.output.failed[0], MeasurementCancelled)
    assert not bench.motion.is_moving("X")


def _measure_both(bench):
    bench.measure("X")
    bench.measure("Y")
    assert bench.output.failed == []
    return bench.output.measured


def test_record_writes_the_mean_with_the_current_chain_setting(bench):
    x, y = _measure_both(bench)
    result = bench.service.record(x, y)

    assert result.is_success
    recorded = result.value
    entries = bench.transmissions.find_all()
    assert len(entries) == 2
    newest = entries[-1]
    assert newest.entry_id == recorded.entry_id
    assert newest.travel_per_motor_revolution_mm == pytest.approx(
        (x.travel_per_motor_revolution_mm + y.travel_per_motor_revolution_mm) / 2
    )
    assert (newest.microsteps, newest.driver_current_a, newest.driver_peak_current_a) == (16, 3.5, 4.0)
    assert [e.entry.entry_id for e in bench.events] == [newest.entry_id]
    assert recorded.deviation_mm == pytest.approx(
        x.travel_per_motor_revolution_mm - y.travel_per_motor_revolution_mm
    )


def test_compare_writes_nothing(bench):
    x, y = _measure_both(bench)
    compared = bench.service.compare(x, y)
    assert compared.is_success and compared.value.entry_id is None
    assert len(bench.transmissions.find_all()) == 1
    assert bench.events == []


def test_record_refuses_two_measurements_of_the_same_axis(bench):
    bench.measure("X")
    x = bench.output.measured[0]
    assert isinstance(bench.service.record(x, x).error, MeasurementsNotComparable)


def test_record_refuses_when_microsteps_changed_since_the_measurement(bench):
    x, y = _measure_both(bench)
    bench.record_setting(microsteps=8)
    assert isinstance(bench.service.record(x, y).error, MeasurementsNotComparable)
