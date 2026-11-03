"""ExpectedSource value object (see expected_source_intention.md)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExpectedSource:
    count: int
    required: bool = True

    def __post_init__(self):
        if self.count < 1:
            raise ValueError("count must be >= 1")
