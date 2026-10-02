"""MechanicalTransmissionCalibrationService on in-memory repositories."""
import logging

import pytest

from application.services.mechanical_transmission_calibration_service.mechanical_transmission_calibration_service import (
    MECHANICAL_TRANSMISSION_CALIBRATION_ENTRY_ADDED_TOPIC,
    MechanicalTransmissionCalibrationService,
)
from domain.calibration.calibration import Calibration
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import HardwareComponentKind
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.persistence.calibration.fake.fake_hardware_component_repository import (
    FakeHardwareComponentRepository,
)
from infrastructure.persistence.calibration.fake.fake_mechanical_transmission_calibration_repository import (
    FakeMechanicalTransmissionCalibrationRepository,
)

MOTORS = HardwareComponentKind.MOTORS
DRIVER = HardwareComponentKind.STEPPER_DRIVER
IGUS = {"full_steps_per_revolution": 200, "rated_current_a": 4.2}
BENCH_SETTING = dict(microsteps=16, driver_current_a=3.5, driver_peak_current_a=4.0, travel_per_motor_revolution_mm=69.76)


def mount(components, kind, name, values):
    calibration = Calibration()
    components.add(calibration.record_hardware_component_characterization(kind, name, values))
    mounted = Calibration.mounted_component_name(components.find_selections(kind))
    components.add_selection(calibration.mount_hardware_component(kind, name, {name}, mounted))


@pytest.fixture
def components():
    return FakeHardwareComponentRepository()


@pytest.fixture
def bus():
    return InMemoryEventBus()


@pytest.fixture
def service(components, bus):
    return MechanicalTransmissionCalibrationService(FakeMechanicalTransmissionCalibrationRepository(), components, bus)


@pytest.fixture
def bench(components):
    mount(components, MOTORS, "Igus MOT-AN-S-060-035-060-L-A-AAAA", IGUS)
    mount(components, DRIVER, "TB6600", {"max_current_a": 3.5})


def test_current_calibration_derives_the_bench_factor(bench, service):
    service.record_calibration(**BENCH_SETTING)

    current = service.get_current_calibration()

    assert current.microns_per_pulse == pytest.approx(21.8)
    assert (current.motor_name, current.stepper_driver_name) == ("Igus MOT-AN-S-060-035-060-L-A-AAAA", "TB6600")
    assert current.microsteps == 16


def test_driver_current_below_motor_rating_is_warned(bench, service, caplog):
    service.record_calibration(**BENCH_SETTING)

    with caplog.at_level(logging.WARNING):
        current = service.get_current_calibration()

    assert "4.2" in current.driver_current_warning
    assert current.driver_current_warning in caplog.text


def test_record_publishes_the_entry_added_event(bench, service, bus):
    received = []
    bus.subscribe(MECHANICAL_TRANSMISSION_CALIBRATION_ENTRY_ADDED_TOPIC, received.append)

    service.record_calibration(**BENCH_SETTING)

    assert len(received) == 1


def test_record_is_refused_without_a_mounted_driver(components, service):
    mount(components, MOTORS, "Igus", IGUS)

    with pytest.raises(ValueError):
        service.record_calibration(**BENCH_SETTING)


def test_no_current_calibration_when_nothing_recorded(bench, service):
    assert service.get_current_calibration() is None


def test_a_driver_swap_invalidates_the_transmission(bench, components, service):
    service.record_calibration(**BENCH_SETTING)

    mount(components, DRIVER, "DM542", {"max_current_a": 4.2})

    assert service.get_current_calibration() is None


def test_no_factor_without_the_motor_steps_per_revolution(components, service):
    mount(components, MOTORS, "Unknown motor", {"rated_current_a": 4.2})
    mount(components, DRIVER, "TB6600", {"max_current_a": 3.5})
    service.record_calibration(**BENCH_SETTING)

    assert service.get_current_calibration() is None
