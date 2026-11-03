# i_mechanical_transmission_calibration_repository — Intention

## Rationale

Defines the persistence contract for the mechanical transmission registry,
same Repository pattern as the source geometry registry: the domain declares
WHAT to persist (an append-only registry of entries), infrastructure decides
HOW (a JSON file, see `RealMechanicalTransmissionCalibrationRepository`).

## Responsibility

- `add(entry)`: append an entry — never overwrite or remove one.
- `find_all()`: every entry, in stored order. The caller picks the current
  one (`Calibration.current_mechanical_transmission`); an empty result is
  also the composition root's "seed it from the template?" check.

## Design

- ABC in `domain/calibration/repositories/`; implemented by
  `RealMechanicalTransmissionCalibrationRepository` (JSON,
  `.aefi_acquisition/calibrations/mechanical_transmission_calibration.json`)
  and `FakeMechanicalTransmissionCalibrationRepository` (in-memory), both in
  `infrastructure/persistence/calibration/`.
