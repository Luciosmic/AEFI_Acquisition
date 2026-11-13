class MotionConversionUnavailableError(RuntimeError):
    """The motion port has no mm/pulse conversion yet: it refuses to move, set a speed in mm/s or
    read a position in mm until set_microns_per_pulse() has been called."""

    def __init__(self, operation: str) -> None:
        super().__init__(
            f"{operation}: no mm/pulse conversion applied — the mechanical transmission is not calibrated"
        )
        self.operation = operation
