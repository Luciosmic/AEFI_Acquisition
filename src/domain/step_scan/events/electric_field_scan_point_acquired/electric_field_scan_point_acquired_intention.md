# electric_field_scan_point_acquired — Intention

## Rationale
Represent the acquisition of an electric field measurement at a specific scan point, enabling separate processing and export of electric field data alongside voltage measurements in scan operations.

## Responsibility
- Event emitted when an electric field measurement is acquired at a scan point
- Carry all necessary information: scan_id, point_index, position, and field measurement
- Enable decoupled handling of electric field data from voltage data in the scan pipeline

## Design
- Domain event (immutable, past-tense)
- Contains scan_id, point_index, position, and field_measurement
- Topic: "electricfieldscanpointacquired"
- Complements (does not replace) the existing ScanPointAcquired event for voltage measurements
