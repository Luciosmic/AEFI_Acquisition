from infrastructure.hardware.lsm9ds1.lsm9ds1_conversion import (
    ACCELEROMETER_FULL_SCALE_G,
    GYROSCOPE_FULL_SCALE_DPS,
    MAGNETOMETER_FULL_SCALE_UT,
    LIDAR_MM_PER_LSB,
    lidar_raw_to_mm,
    raw_to_physical,
)


def test_half_scale_is_half_full_scale_for_accelerometer():
    assert raw_to_physical((16384, 0, -32768), ACCELEROMETER_FULL_SCALE_G) == (1.0, 0.0, -2.0)


def test_full_scale_constants():
    assert (
        ACCELEROMETER_FULL_SCALE_G,
        GYROSCOPE_FULL_SCALE_DPS,
        MAGNETOMETER_FULL_SCALE_UT,
    ) == (2, 490, 400)


def test_gyroscope_and_magnetometer_use_their_own_full_scale():
    assert raw_to_physical((16384,), GYROSCOPE_FULL_SCALE_DPS) == (245.0,)
    assert raw_to_physical((16384,), MAGNETOMETER_FULL_SCALE_UT) == (200.0,)


def test_lidar_raw_is_millimetres_factor_one():
    assert LIDAR_MM_PER_LSB == 1.0
    assert lidar_raw_to_mm(1234) == 1234.0
    assert isinstance(lidar_raw_to_mm(1234), float)


def test_returns_tuple():
    assert isinstance(raw_to_physical([1, 2, 3], 2), tuple)
