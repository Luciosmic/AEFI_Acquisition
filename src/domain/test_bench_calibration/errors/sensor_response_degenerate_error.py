"""
Sensor Response Degenerate Error

See sensor_response_degenerate_error_intention.md.
"""


class SensorResponseDegenerateError(ValueError):
    """The sensor responses to X and Y excitation do not determine the mounting angles."""
