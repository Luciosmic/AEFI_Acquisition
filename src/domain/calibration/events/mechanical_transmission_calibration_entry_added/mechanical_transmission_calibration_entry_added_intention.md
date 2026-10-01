# mechanical_transmission_calibration_entry_added — Intention

## Rationale

A new motion chain setting changes the distance per motor pulse, hence every
position the bench reports. Without an event, whatever must follow that
change (the motion controller's conversion, the export snapshot, a future
panel) would have to poll the registry or be wired by hand to the service.

## Responsibility

- Signal that a new `MechanicalTransmissionCalibrationEntry` was recorded.
- Carry the full entry so subscribers need no follow-up read.

## Design

- `@dataclass(frozen=True)` inheriting `DomainEvent`.
- `entry: MechanicalTransmissionCalibrationEntry` — the entry just recorded.
- Topic of publication: `"mechanicaltransmissioncalibrationentryadded"`.
