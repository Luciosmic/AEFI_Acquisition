# mechanical_transmission_calibration_service — Intention

## Rationale

Every position the bench reports goes through the distance per motor pulse.
Without a service owning it, the composition root would read the motor's
characterization, the mountings and the transmission registry by hand to
configure the motion controller, the export would do the same to describe
the acquisition, and the two could disagree on which transmission is
current — positions converted with one factor, recorded with another.

## Responsibility

- `record_calibration(microsteps, driver_current_a, driver_peak_current_a,
  travel_per_motor_revolution_mm)`: record the motion chain as set up now,
  with the currently mounted motor and stepper driver (refused by the
  aggregate when either is missing), persist it, publish
  `MechanicalTransmissionCalibrationEntryAdded`. Used by the composition
  root to seed the registry from `config_templates/` on first boot — same
  path as any future UI, no separate seeding code.
- `get_current_calibration()`: the transmission set up with the motor and
  driver mounted now, with its derived distance per pulse and the driver
  current warning — `None` (WARNING logged) when there is no such
  transmission or the motor's steps per revolution is not characterized:
  then nothing can convert positions, and the motion controller stays
  unconfigured (it refuses to move) rather than guessing.

## Design

- Constructor: transmission repository, hardware component repository
  (read only: mountings and the motor's characterization), event bus. Reads
  the catalog through its repository, not through `HardwareComponentService`
  (no application-to-application call); the reading rules are the
  aggregate's (`current_mounting`, `current_characterization`,
  `current_mechanical_transmission`).
- The driver current warning is logged (WARNING) each time it is read and
  carried in the DTO for the export: permanent on this bench (TB6600 max
  3.5 A, Igus motor rated 4.2 A), a fact to keep visible, not a blocker.
- Topic: `mechanicaltransmissioncalibrationentryadded`.
- Applying the factor to the motion controller happens at startup only
  (composition root): a new transmission is applied after a restart (said in
  the log when one is recorded).
