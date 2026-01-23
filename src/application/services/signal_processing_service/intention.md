# Signal Processing Service Intention

## Responsibility
The **Signal Processing Service** is responsible for correcting raw voltage measurements using calibration parameters. It acts as the central orchestrator for:
1.  **Noise Correction**: Removing instrumental DC offsets.
2.  **Phase Alignment**: Rotating the complex signal to alignment with the In-Phase axis.
3.  **Primary Field Subtraction**: Taring the signal against a reference excitation field.

## Scope
- **Input**: Raw `VoltageMeasurement` (from Acquisition Port).
- **Processing**: Applying corrections based on the active `VoltageMeasurementReference`.
- **Calibration**: Performing calibration routines (Noise, Phase, Primary) and updating the reference.
- **Output**: Corrected `VoltageMeasurement`.

## Dependencies
- **Domain Layer**: `VoltageMeasurement` (Entity), `VoltageMeasurementReference` (Value Object), `SignalCalibrationService` (Domain Logic).
- **Ports**: None direct (orchestrated by Presenter usually, but may use Repositories potentially).

## Design Pattern
- **Application Service**: Orchestrates domain objects.
- **DTO**: Uses strict Request/Response DTOs for all API methods to ensure stability and versioning.
