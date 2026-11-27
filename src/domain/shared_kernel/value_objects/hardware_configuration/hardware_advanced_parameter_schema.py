from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Tuple

class ParameterType(Enum):
    NUMBER = "number"   # Float or Int with range
    ENUM = "enum"       # Discrete choices
    BOOLEAN = "bool"    # True/False
    DISPLAY = "display" # Read-only value, never part of the applied config

@dataclass(frozen=True)
class HardwareAdvancedParameterSchema:
    """
    Base Value Object for a self-describing hardware parameter.
    """
    key: str
    display_name: str
    description: str = ""
    default_value: Any = None
    group: str = "General"
    
    @property
    def kind(self) -> ParameterType:
        raise NotImplementedError

@dataclass(frozen=True)
class NumberParameterSchema(HardwareAdvancedParameterSchema):
    min_value: float = 0.0
    max_value: float = 100.0
    unit: str = ""
    step: float = 1.0
    
    @property
    def kind(self) -> ParameterType:
        return ParameterType.NUMBER

@dataclass(frozen=True)
class EnumParameterSchema(HardwareAdvancedParameterSchema):
    choices: Tuple[str, ...] = field(default_factory=tuple)
    
    @property
    def kind(self) -> ParameterType:
        return ParameterType.ENUM

@dataclass(frozen=True)
class BooleanParameterSchema(HardwareAdvancedParameterSchema):
    @property
    def kind(self) -> ParameterType:
        return ParameterType.BOOLEAN

@dataclass(frozen=True)
class DisplayParameterSchema(HardwareAdvancedParameterSchema):
    """
    Read-only value shown next to the settings, never part of the applied config.

    Without source_key, default_value is shown as is (a fixed quantity).
    With source_key, the text follows that parameter: text_by_source_value maps
    each of its values to the text to show, so the hardware adapter keeps the
    formula and the view only looks the text up.
    """
    source_key: str = ""
    text_by_source_value: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    @property
    def kind(self) -> ParameterType:
        return ParameterType.DISPLAY

    def text_for(self, source_value: Any) -> str:
        return dict(self.text_by_source_value).get(str(source_value), str(self.default_value))
