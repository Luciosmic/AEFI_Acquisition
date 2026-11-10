import pytest

from application.services.inertial_probe_service.ports.i_inertial_probe_stream_port import (
    IInertialProbeStreamPort,
)
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.hardware.hardware_composition_root import HardwareCompositionRoot
from infrastructure.hardware.lsm9ds1.adapter_inertial_probe_stream_port import (
    Lsm9ds1InertialProbeStreamAdapter,
)
from infrastructure.hardware.lsm9ds1.fake.fake_inertial_probe_stream_adapter import (
    FakeInertialProbeStreamAdapter,
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
        inertial_probe_config=CONFIG,
    )


def test_missing_key_defaults_to_mock_fake():
    hw = HardwareCompositionRoot(BASE, InMemoryEventBus(), "COM_TEST")
    assert isinstance(hw.inertial_probe_port, IInertialProbeStreamPort)
    assert isinstance(hw.inertial_probe_port, FakeInertialProbeStreamAdapter)


def test_mock_mode_builds_the_fake():
    assert isinstance(build(inertial_probe="mock").inertial_probe_port, FakeInertialProbeStreamAdapter)


def test_real_mode_builds_the_lsm9ds1_adapter_without_opening_the_port():
    hw = build(inertial_probe="real")
    assert isinstance(hw.inertial_probe_port, Lsm9ds1InertialProbeStreamAdapter)
    assert not hw.inertial_probe_port.is_connected()


def test_real_mode_without_config_is_refused():
    with pytest.raises(ValueError, match="lsm9ds1_config"):
        HardwareCompositionRoot({**BASE, "inertial_probe": "real"}, InMemoryEventBus(), "COM_TEST")


def test_inertial_probe_is_not_part_of_the_startup_lifecycle():
    assert len(build(inertial_probe="real").lifecycle_adapters) == len(
        build(inertial_probe="mock").lifecycle_adapters
    )
