import pytest

from interface.presentation.sample_rate_meter import SampleRateMeter


def test_rate_is_none_below_two_samples():
    m = SampleRateMeter(window_size=10)
    assert m.rate_hz is None
    m.add(1.0)
    assert m.rate_hz is None


def test_rate_is_mean_rate_over_the_window():
    m = SampleRateMeter(window_size=100)
    for k in range(26):
        m.add(k * 0.04)  # 25 Hz
    assert m.rate_hz == pytest.approx(25.0)


def test_window_forgets_old_samples():
    m = SampleRateMeter(window_size=5)
    for k in range(10):
        m.add(k * 1.0)  # 1 Hz
    for k in range(5):
        m.add(10.0 + k * 0.1)  # 10 Hz
    assert m.rate_hz == pytest.approx(10.0)


def test_identical_timestamps_give_none_not_division_by_zero():
    m = SampleRateMeter(window_size=5)
    m.add(1.0)
    m.add(1.0)
    assert m.rate_hz is None


def test_reset_clears_the_window():
    m = SampleRateMeter(window_size=5)
    m.add(0.0)
    m.add(1.0)
    m.reset()
    assert m.rate_hz is None
