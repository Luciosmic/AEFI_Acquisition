import pytest

from infrastructure.hardware.lsm9ds1.lsm9ds1_stream_protocol import (
    STOP_COMMAND,
    LineSplitter,
    expected_field_count,
    normalize_sensors,
    parse_stream_line,
    start_commands,
)

ALL = ["accelerometer", "gyroscope", "magnetometer", "lidar"]


def test_stop_command():
    assert STOP_COMMAND == "S*"


def test_start_commands_follow_labview_order():
    assert start_commands(["lidar", "accelerometer", "magnetometer", "gyroscope"]) == [
        "A9*",
        "G9*",
        "M9*",
        "L9*",
    ]
    assert start_commands(["accelerometer"]) == ["A9*"]


def test_no_command_contains_a_line_feed():
    for c in start_commands(ALL) + [STOP_COMMAND]:
        assert "\n" not in c and "\r" not in c and c.endswith("*")


def test_normalize_rejects_unknown_and_empty():
    with pytest.raises(ValueError):
        normalize_sensors(["accelerometer", "temperature"])
    with pytest.raises(ValueError):
        normalize_sensors([])


def test_expected_field_count():
    assert expected_field_count(["accelerometer"]) == 3
    assert expected_field_count(["accelerometer", "lidar"]) == 4
    assert expected_field_count(ALL) == 10


def test_parse_full_line_fixed_field_order_magnetometer_accelerometer_gyroscope_lidar():
    line = b"-3473\t1212\t-2211\t16970\t-165\t1184\t-157\t37\t-662\t1259\n"
    assert parse_stream_line(line, ALL) == {
        "magnetometer": (-3473, 1212, -2211),
        "accelerometer": (16970, -165, 1184),
        "gyroscope": (-157, 37, -662),
        "lidar": (1259,),
    }


def test_parse_accelerometer_lidar_line_uses_trailing_tab_then_lidar_without_tab():
    d = parse_stream_line(b"16868\t-120\t1186\t1190\n", ["accelerometer", "lidar"])
    assert d == {"accelerometer": (16868, -120, 1186), "lidar": (1190,)}


def test_parse_accelerometer_only_line_with_trailing_tab():
    assert parse_stream_line(b"16896\t-165\t1148\t\n", ["accelerometer"]) == {
        "accelerometer": (16896, -165, 1148)
    }


def test_parse_lidar_only():
    assert parse_stream_line(b"1285\n", ["lidar"]) == {"lidar": (1285,)}


@pytest.mark.parametrize("line", [b"1\t2\t\n", b"1\t2\t3\t4\t\n", b"a\tb\tc\t\n", b"\n", b""])
def test_parse_returns_none_for_out_of_regime_lines(line):
    assert parse_stream_line(line, ["accelerometer"]) is None


def test_transient_shorter_line_is_dropped_in_full_regime():
    assert parse_stream_line(b"16943\t100\t1177\t-57\t32\t-674\t\n", ALL) is None


def test_splitter_keeps_partial_line_across_chunks():
    sp = LineSplitter()
    assert sp.feed(b"1\t2\t3\t\n4\t5") == [b"1\t2\t3\t\n"]
    assert sp.feed(b"\t6\t\n7") == [b"4\t5\t6\t\n"]
    assert sp.feed(b"\n") == [b"7\n"]


def test_splitter_empty_chunk():
    assert LineSplitter().feed(b"") == []
