"""LSM9DS1 board stream protocol (pure, no I/O).

Established by the 2026-10-12 serial-protocol note of the thesis working folder
"Hardware - Drivers/LSM9DS1" (14 experiments on the real board): 'A9*' / 'G9*' /
'M9*' / 'L9*' add a sensor to a cumulative stream, 'S*' stops everything.
A line carries the active sensors in the FIXED order magnetometer,
accelerometer, gyroscope, lidar (3, 3, 3, 1 integers; TAB-separated,
accelerometer/gyroscope/magnetometer groups end with a TAB, lidar has none).
Never send LF/CRLF: it invalidates the next frame.
"""

from typing import Dict, Iterable, List, Optional, Sequence, Tuple

STOP_COMMAND = "S*"
VALID_RATES_HZ = (25, 50, 100)

ACCELEROMETER = "accelerometer"
GYROSCOPE = "gyroscope"
MAGNETOMETER = "magnetometer"
# ponytail: the lidar measures a distance, it is not an inertial sensor. It is a
# channel of the same stream only because it sits on the same board and serial
# link (an infrastructure fact). Ceiling: one stream carries both. Upgrade: a
# separate lidar port/concept; the shared board/link stays an infrastructure detail.
LIDAR = "lidar"

# order of the fields inside a streamed line
LINE_ORDER = (MAGNETOMETER, ACCELEROMETER, GYROSCOPE, LIDAR)
# order of the start commands (LabVIEW sequence A, G, M, L)
COMMAND_ORDER = (ACCELEROMETER, GYROSCOPE, MAGNETOMETER, LIDAR)
FIELD_COUNT = {MAGNETOMETER: 3, ACCELEROMETER: 3, GYROSCOPE: 3, LIDAR: 1}
START_COMMAND = {ACCELEROMETER: "A9*", GYROSCOPE: "G9*", MAGNETOMETER: "M9*", LIDAR: "L9*"}


def normalize_sensors(sensors: Iterable[str]) -> Tuple[str, ...]:
    chosen = set(sensors)
    unknown = chosen - set(FIELD_COUNT)
    if unknown:
        raise ValueError(f"unknown sensors: {sorted(unknown)}")
    if not chosen:
        raise ValueError("at least one sensor is required")
    return tuple(s for s in LINE_ORDER if s in chosen)


def start_commands(sensors: Iterable[str]) -> List[str]:
    chosen = set(normalize_sensors(sensors))
    return [START_COMMAND[s] for s in COMMAND_ORDER if s in chosen]


def expected_field_count(sensors: Iterable[str]) -> int:
    return sum(FIELD_COUNT[s] for s in normalize_sensors(sensors))


def parse_stream_line(line: bytes, sensors: Sequence[str]) -> Optional[Dict[str, Tuple[int, ...]]]:
    """Parse one complete line in the steady regime; None if it has another shape."""
    order = normalize_sensors(sensors)
    try:
        values = [int(v) for v in line.decode("ascii").split()]
    except (UnicodeDecodeError, ValueError):
        return None
    if len(values) != sum(FIELD_COUNT[s] for s in order):
        return None
    out: Dict[str, Tuple[int, ...]] = {}
    i = 0
    for s in order:
        n = FIELD_COUNT[s]
        out[s] = tuple(values[i : i + n])
        i += n
    return out


class LineSplitter:
    """Accumulates bytes, returns complete lines (with their trailing LF)."""

    def __init__(self) -> None:
        self._buf = b""

    def feed(self, chunk: bytes) -> List[bytes]:
        self._buf += chunk
        lines: List[bytes] = []
        while True:
            i = self._buf.find(b"\n")
            if i < 0:
                return lines
            lines.append(self._buf[: i + 1])
            self._buf = self._buf[i + 1 :]
