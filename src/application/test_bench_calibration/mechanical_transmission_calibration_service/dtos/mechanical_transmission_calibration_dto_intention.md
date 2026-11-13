---
type: atome::solidai-atome
tldr: "DTO `mechanical_transmission_calibration_dto` : Carry the current transmission's settings, the names of the mounted motor and."
code: ["[[src/application/test_bench_calibration/mechanical_transmission_calibration_service/dtos/mechanical_transmission_calibration_dto.py]]"]
cause_de_changement: orchestration
---
# mechanical_transmission_calibration_dto — Intention

## Rationale

The composition root (motion controller factor) and the export (acquisition
metadata) need the current transmission without importing domain entities.

## Responsibility

Carry the current transmission's settings, the names of the mounted motor and
driver, the derived distance per pulse (µm) and the driver current warning.

## Design

- `@dataclass(frozen=True)`, primitives only.
- Built by `MechanicalTransmissionCalibrationService.get_current_calibration()`,
  which returns `None` instead when there is no usable transmission.
