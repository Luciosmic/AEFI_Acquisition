from dataclasses import dataclass

@dataclass(frozen=True)
class ExcitationLevel:
    """
    Value object representing the excitation intensity level as a percentage.
    
    Range: 0.0 to 100.0
    """
    value: float

    def __post_init__(self):
        if not (0.0 <= self.value <= 100.0):
            raise ValueError(f"ExcitationLevel must be between 0.0 and 100.0, got {self.value}")

    @staticmethod
    def off() -> 'ExcitationLevel':
        return ExcitationLevel(0.0)

    @staticmethod
    def max() -> 'ExcitationLevel':
        return ExcitationLevel(100.0)
