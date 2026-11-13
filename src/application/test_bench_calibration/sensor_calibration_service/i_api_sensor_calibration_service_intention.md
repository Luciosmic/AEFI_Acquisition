---
type: port::solidai-hexagonal
tldr: "Port entrant `i_api_sensor_calibration_service` : `record_calibration(theta_x_degrees, theta_y_degrees, theta_z_degrees)`: the command exposed by the \"Enregistrer calibration\" button."
sens: entrant
code: "[[src/application/test_bench_calibration/sensor_calibration_service/i_api_sensor_calibration_service.py]]"
---
# i_api_sensor_calibration_service — Intention

## Rationale

Mirrors `IApiSynchronousDetectionService`: gives `SensorCalibrationPresenter`
a stable inbound contract to depend on, independent of the concrete service
implementation.

## Responsibility

- `record_calibration(theta_x_degrees, theta_y_degrees, theta_z_degrees)`:
  the command exposed by the "Enregistrer calibration" button.
- `get_latest_calibration()`: the query used to populate the "last
  calibration" label on panel load and after each successful record.

## Design

- Pure `ABC`, no state. Implemented by `SensorCalibrationService`.
