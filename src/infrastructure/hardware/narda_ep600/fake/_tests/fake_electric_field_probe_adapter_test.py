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


def test_refresh_battery_noop_when_not_connected():
    adapter = FakeElectricFieldProbeAdapter()
    adapter.refresh_battery()  # must not raise
    assert adapter.get_probe() is None


def test_refresh_battery_updates_probe_battery_fields():
    adapter = FakeElectricFieldProbeAdapter()
    adapter.connect()
    probe_before = adapter.get_probe()

    adapter.refresh_battery()

    probe_after = adapter.get_probe()
    assert probe_after is not probe_before
    assert probe_after.battery_voltage_v is not None
    assert probe_after.serial_number == probe_before.serial_number


def test_apply_frequency_correction_out_of_range_below_10khz():
    adapter = FakeElectricFieldProbeAdapter()
    result = adapter.apply_frequency_correction(5_000.0)

    assert result.in_range is False
    assert result.applied_hz is None
    assert result.requested_hz == 5_000.0


def test_apply_frequency_correction_in_range():
    adapter = FakeElectricFieldProbeAdapter()
    result = adapter.apply_frequency_correction(50_000.0)

    assert result.in_range is True
    assert result.applied_hz == 50_000.0
    assert result.error is None
