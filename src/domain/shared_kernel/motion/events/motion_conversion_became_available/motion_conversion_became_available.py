from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class MotionConversionBecameAvailable(DomainEvent):
    """Event published when the mm/pulse conversion has been applied to the motion port:
    motion and scan are accepted from now on."""

    microns_per_pulse: float
    motor_name: str
    stepper_driver_name: str
