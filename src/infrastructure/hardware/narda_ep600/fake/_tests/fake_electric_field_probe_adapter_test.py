import pytest

from infrastructure.hardware.narda_ep600.fake.fake_electric_field_probe_adapter import (
    FakeElectricFieldProbeAdapter,
)


def test_not_connected_initially():
    adapter = FakeElectricFieldProbeAdapter()
    assert not adapter.is_connected()
    assert adapter.get_probe() is None


def test_connect_sets_probe_identity():
    adapter = FakeElectricFieldProbeAdapter()
    adapter.connect()
    assert adapter.is_connected()
    assert adapter.get_probe().axis_labels == ("X", "Y", "Z")


def test_disconnect_clears_state():
    adapter = FakeElectricFieldProbeAdapter()
    adapter.connect()
    adapter.disconnect()
    assert not adapter.is_connected()
    assert adapter.get_probe() is None


def test_acquire_sample_requires_connection():
    adapter = FakeElectricFieldProbeAdapter()
    with pytest.raises(RuntimeError):
        adapter.acquire_sample()


def test_acquire_sample_returns_three_components_once_connected():
    adapter = FakeElectricFieldProbeAdapter(noise_std=0.0)
    adapter.connect()
    sample = adapter.acquire_sample()
    assert len(sample.components) == 3


def test_simulated_connection_failure_raises():
    adapter = FakeElectricFieldProbeAdapter(simulate_connection_failure=True)
    with pytest.raises(TimeoutError):
        adapter.connect()
    assert not adapter.is_connected()
