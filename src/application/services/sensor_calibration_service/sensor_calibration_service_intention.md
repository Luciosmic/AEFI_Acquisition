# sensor_calibration_service — Intention

> 2026-09-25: the sensor became a hardware component (identity + transduction
> gain, 'Capteur' tab, `HardwareComponentService`). This service now only
> handles the **mounting angles**: each calibration references the sensor's
> current mounting (`sensor_mounting_id`) and the current source geometry
> entry; recording with no sensor mounted is refused; a new mounting
> (`hardwarecomponentmounted` event for the sensor) or a new geometry entry
> falls back to the ideal angles until recalibrated. Sections below that
> mention sensor identity / hardware signature predate this change.

## Rationale

The sensor calibration procedure (thesis vault) yields the 3 mounting angles
P (brings the sensor from the sources frame to its current mounting;
measurement E_sensor = Pᵀ·E_sources; correction E_sources = P·E_sensor; frames
and definition of P: `domain/calibration/value_objects/rotation_convention/rotation_convention_intention.md`)
that must be recorded with full traceability — which sensor, which hardware,
which sphere geometry, when — and later retrieved for the current setup.
The sensor identity (version + serial number) used to live in
`aefi_device_config.json`, edited by hand and disconnected from the
calibration it qualifies: swapping the sensor without editing the JSON
would silently tag every calibration with the wrong sensor. Declaring the
identity together with the sensor calibration makes this registry the single
source of truth for which sensor is mounted. Mirrors
`SynchronousDetectionService`'s split between a command
(`save_calibration_point`) and queries reading back the append-only
registry, but for a different calibration type on the same `Calibration`
aggregate.

These angles are also what the application applies to every sensor sample
(`TransformationService`). Before, that rotation came from a separate,
non-persisted panel (Sensor Transformation), so the calibration registry was
recorded but never used.

## Responsibility

- At construction, adopt the sensor identity of the most recent registry
  entry (all signatures/geometries) on top of the injected board versions.
  Empty registry -> keep the device-config seed and log a WARNING.
- `record_calibration(sensor_version, sensor_serial_number, theta_x, theta_y, theta_z)`:
  tag the entry with the entered sensor identity, build a
  `SensorRotationAngles`, call
  `Calibration.record_sensor_calibration_entry(...)`, persist the
  minted entry via the repository, publish the resulting domain event(s).
- `get_latest_calibration()`: read all entries for the injected
  `HardwareSignature`, filter to those referencing the current source
  geometry entry (`source_geometry_entry_id` — an entry recorded against
  another geometry entry is not applicable to the current one), return the most
  recent as a DTO — `None` if nothing matches yet.
- `get_current_sensor_identity()`: the sensor currently considered mounted.
- `preview_rotation(theta_x, theta_y, theta_z)`: set trial angles for the
  trial-and-error tuning and apply them live (publish the active rotation).
  The trial is not persisted; it is discarded by `record_calibration()` and
  by a source geometry change. A future automatic calibration service will
  drive this same preview.
- `reset_to_default()`: take the ideal `default_angles` as trial angles
  (restart the tuning from the ideal mounting).
- `get_active_rotation()`: the rotation applied to sensor readings — the
  trial angles when a trial is in progress (`is_trial`), else the latest
  calibration for the current hardware signature and source geometry, else
  the injected ideal `default_angles` (never `None`).
- Publish `ActiveSensorRotationChanged` whenever the active rotation may
  have changed: after `record_calibration()`, `preview_rotation()`,
  `reset_to_default()`, and when a new source geometry
  is recorded (`SOURCE_GEOMETRY_CALIBRATION_ENTRY_ADDED_TOPIC`) — a new
  geometry has no sensor calibration yet, so the ideal angles apply.
  `TransformationService` subscribes to it.
- Follow the current source geometry: the injected geometric configuration
  is only the startup value; a recorded source geometry replaces it (an
  identical geometry is logged and ignored).
- `get_current_hardware_signature()` (not on the inbound API — composition
  root only): board versions + current sensor identity, injected into the
  other calibration services (synchronous detection phase, conditioning
  electronics board).

## Design

- A sensor identity change at runtime is applied to this service
  immediately, but the other services received the signature once at
  startup: a WARNING says a restart is needed (`ponytail:` debt — a shared
  signature provider is the upgrade path).
- Constructor receives `calibration_repository`, `hardware_signature`,
  `source_geometry_entry_id`, `default_angles`, `event_bus`. The startup
  geometry entry comes from `SourceGeometryCalibrationService.get_current_entry_id()`
  (composition root); a newly recorded geometry entry (event) replaces it —
  by identity: a re-measurement is a new entry even with identical values,
  so the rotation falls back to the ideal angles until recalibrated;
  `default_angles` from `IdealSensorRotationReader`
  (`sensor.calibration.sources_to_sensor_rotation` of the device config).
- The ideal angles are a fallback, never a registry entry: an entry means
  "calibrated on date X for geometry Y" — seeding ideal angles would fake
  that traceability.
- `ActiveSensorRotationChanged` is published by this application service,
  not minted by the `Calibration` aggregate: it is a derived fact (which
  angles apply now), not a registry transition. Precedent:
  `TransformationService` publishing `SensorTransformationAnglesUpdated`.
- `record_calibration()` builds a **fresh** `Calibration()` instance (not
  `reconstitute`) — unlike the phase-compensation flag, recording an angle
  entry has no persisted state to rehydrate first; the aggregate here is
  used purely for its event-minting behavior, matching how
  `record_synchronous_detection_phase_entry` itself doesn't read
  `synchronous_detection_compensation_enabled` either.
- Domain events are published with `type(event).__name__.lower()` as topic,
  same convention as `SynchronousDetectionService._publish_domain_events`.
- `SENSOR_CALIBRATION_ENTRY_ADDED_TOPIC = "sensorcalibrationentryadded"`
  exported as a module constant for presenters/tests to subscribe to,
  mirroring `SYNCHRONOUS_DETECTION_PHASE_CALIBRATION_ENTRY_ADDED_TOPIC`.
- `ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC = "activesensorrotationchanged"`
  exported the same way.
- The rotation itself is applied by `TransformationService`, not here.
