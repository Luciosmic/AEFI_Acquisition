import pytest

from application.services.inertial_sensor_service.ports.i_inertial_sensor_stream_port import (
    IInertialSensorStreamPort,
)
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.hardware.hardware_composition_root import HardwareCompositionRoot
from infrastructure.hardware.lsm9ds1.adapter_inertial_sensor_stream_port import (
    Lsm9ds1InertialSensorStreamAdapter,
)
from infrastructure.hardware.lsm9ds1.fake.fake_inertial_sensor_stream_adapter import (
    FakeInertialSensorStreamAdapter,
)
from infrastructure.hardware.lsm9ds1.lsm9ds1_config_loader import Lsm9ds1Config

BASE = {"motion": "mock", "aefi_device": "mock", "electric_field_probe": "mock", "oscilloscope": "mock"}
CONFIG = Lsm9ds1Config(
    com_port="COM_TEST", baudrate=256000, channels=("accelerometer",), rate_hz=None
)


def build(**overrides):
    return HardwareCompositionRoot(
        hardware_config={**BASE, **overrides},
        event_bus=InMemoryEventBus(),
        narda_com_port="COM_TEST",
        inertial_sensor_config=CONFIG,
    )


def test_missing_key_defaults_to_mock_fake():
    hw = HardwareCompositionRoot(BASE, InMemoryEventBus(), "COM_TEST")
    assert isinstance(hw.inertial_sensor_port, IInertialSensorStreamPort)
    assert isinstance(hw.inertial_sensor_port, FakeInertialSensorStreamAdapter)


def test_mock_mode_builds_the_fake():
    assert isinstance(build(inertial_sensor="mock").inertial_sensor_port, FakeInertialSensorStreamAdapter)


def test_real_mode_builds_the_lsm9ds1_adapter_without_opening_the_port():
    hw = build(inertial_sensor="real")
    assert isinstance(hw.inertial_sensor_port, Lsm9ds1InertialSensorStreamAdapter)
    assert not hw.inertial_sensor_port.is_connected()


def test_real_mode_without_config_is_refused():
    with pytest.raises(ValueError, match="lsm9ds1_config"):
        HardwareCompositionRoot({**BASE, "inertial_sensor": "real"}, InMemoryEventBus(), "COM_TEST")


def test_inertial_sensor_is_not_part_of_the_startup_lifecycle():
    assert len(build(inertial_sensor="real").lifecycle_adapters) == len(
        build(inertial_sensor="mock").lifecycle_adapters
    )
