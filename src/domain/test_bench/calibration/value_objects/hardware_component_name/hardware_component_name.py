"""
Hardware Component Name — typed identity

Responsibility:
- The identity of a hardware component (board, chip, ADC, microcontroller,
  motors): its unique name, e.g. "Final_v4_ASSOCE".
"""

from typing import NewType

HardwareComponentName = NewType("HardwareComponentName", str)
