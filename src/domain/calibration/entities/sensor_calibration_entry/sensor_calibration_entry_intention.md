# sensor_calibration_entry — Intention

## Rationale

The mounting angles of the AEFI sensor are a property of how the sensor sits
on the bench, not of the sensor as a product (its identity and transduction
gain live in the hardware component catalog) nor of the electronic boards.
They are measured when the sensor is mounted, and only hold for that
mounting and for the source geometry they were measured against. Copying the
geometry values or the sensor identity into each entry would hide which
mounting and which caliper measurement were used; unmounting and remounting
the same sensor would silently reuse angles that may no longer be true.

## Responsibility

- Bundle one calibrated `SensorRotationAngles` with the identities of the
  sensor mounting (`sensor_mounting_id` = the `HardwareComponentSelection`
  of the sensor) and of the source geometry entry
  (`source_geometry_entry_id`) it was measured on, plus the timestamp.
- Stay immutable and identity-bearing (`entry_id`) — the registry never
  edits or removes an entry, only appends new ones.

## Design

- `@dataclass(frozen=True)`: `entry_id`, `sensor_mounting_id: UUID`,
  `source_geometry_entry_id: UUID`, `angles`, `recorded_at` — cross-references
  by identity only (DDD).
- `single(sensor_mounting_id, source_geometry_entry_id, angles)` static
  factory — `entry_id=uuid4()`, `recorded_at=datetime.now(timezone.utc)`.
- Minted by `Calibration.record_sensor_calibration_entry`, which refuses to
  record angles when no sensor is mounted.
