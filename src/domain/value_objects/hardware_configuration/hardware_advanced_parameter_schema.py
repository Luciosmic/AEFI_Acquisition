from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Tuple

class ParameterType(Enum):
    NUMBER = "number"   # Float or Int with range
    ENUM = "enum"       # Discrete choices
    BOOLEAN = "bool"    # True/False

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
