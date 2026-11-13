---
type: port::solidai-hexagonal
tldr: "Port entrant `i_api_mechanical_transmission_calibration_service` : `record_calibration(microsteps, driver_current_a, driver_peak_current_a, microns_per_pulse)`: record the motion chain as set up now."
sens: entrant
code: "[[src/application/test_bench_calibration/mechanical_transmission_calibration_service/i_api_mechanical_transmission_calibration_service.py]]"
---
# i_api_mechanical_transmission_calibration_service — Intention

## Rationale

Gives the composition root and the export a stable inbound contract,
independent of the concrete service.

## Responsibility

- `record_calibration(microsteps, driver_current_a, driver_peak_current_a,
  microns_per_pulse)`: record the motion chain as set up now.
- `get_current_calibration()`: the current transmission (or `None`).

## Design

- Pure `ABC`, implemented by `MechanicalTransmissionCalibrationService`.
