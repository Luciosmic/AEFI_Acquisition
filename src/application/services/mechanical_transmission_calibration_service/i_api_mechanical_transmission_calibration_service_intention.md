# i_api_mechanical_transmission_calibration_service — Intention

## Rationale

Gives the composition root and the export a stable inbound contract,
independent of the concrete service.

## Responsibility

- `record_calibration(microsteps, driver_current_a, driver_peak_current_a,
  travel_per_motor_revolution_mm)`: record the motion chain as set up now.
- `get_current_calibration()`: the current transmission (or `None`).

## Design

- Pure `ABC`, implemented by `MechanicalTransmissionCalibrationService`.
