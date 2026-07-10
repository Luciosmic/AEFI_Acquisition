# field_measurement_statistics_service — Intention

## Rationale
Provide domain-level statistics calculation for electric field measurements, enabling averaging and uncertainty estimation during scan operations. This service mirrors the functionality of `MeasurementStatisticsService` but operates on `FieldMeasurement` value objects instead of `VoltageMeasurement`.

## Responsibility
- Calculate mean and standard deviation across a list of `FieldMeasurement` objects
- Return a new `FieldMeasurement` with averaged components and computed standard deviations
- Handle edge cases (empty list, single measurement)
- Validate that all measurements have the same dimensionality (same number of components)

## Design
- Static service (no internal state)
- Operates on immutable `FieldMeasurement` value objects
- Returns a new `FieldMeasurement` with the same timestamp as the last measurement
- Computes standard deviations using Bessel's correction (n-1 divisor) for sample standard deviation
- Validates that all measurements have consistent component counts
