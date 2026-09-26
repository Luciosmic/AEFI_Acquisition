# calibration — Intention

## Rationale

Calibration is a broader concept than synchronous detection phase alone
(sensor gain calibration already exists as static JSON in
`aefi_device_config.json` and is expected to move into this same domain
later). Rather than name the aggregate after the one concrete calibration
type this iteration implements, `Calibration` is deliberately generic: a
single aggregate root meant to grow, over time, to manage every form of
calibration the system needs — each with its own explicitly-named methods
(`..._synchronous_detection_...` today) so a future addition (e.g. sensor
gain) adds its own fields/methods without renaming the aggregate or
breaking existing callers.

## Responsibility

- Hold the domain-level, persisted `synchronous_detection_compensation_enabled`
  flag and mutate it idempotently, emitting `SynchronousDetectionCompensationEnabledChanged`
  only on an actual change.
- Mint new `SynchronousDetectionPhaseCalibrationEntry` records via
  `record_synchronous_detection_phase_entry`, emitting
  `SynchronousDetectionPhaseCalibrationEntryAdded`.
- Mint new `SensorCalibrationEntry` records via
  `record_sensor_calibration_entry`, emitting
  `SensorCalibrationEntryAdded` — the sensor-mount rotation angle
  counterpart, referencing by identity the sensor mounting
  (`sensor_mounting_id`) and the source geometry entry
  (`source_geometry_entry_id`) it was measured on — refused when no sensor
  is mounted. The sensor itself is a hardware component (kind `SENSOR`).
- Mint new `SourceGeometryCalibrationEntry` records via
  `record_source_geometry_calibration_entry`, emitting
  `SourceGeometryCalibrationEntryAdded` — the caliper-measured 4-sphere
  geometry (diameters + extremity-to-extremity distances). This registry is
  the live source of the current geometry, referenced by sensor calibration
  entries through its `entry_id`; the raw JSON device config is only its
  one-time seed on first boot.
- Hardware components (boards, signal generation chip, ADC, microcontroller,
  motors — `HardwareComponentKind`) are product modules: each has a unique
  name and a characterization (the kind's essential quantities, each
  possibly "not characterized") that can be completed over time.
  - `record_hardware_component_characterization(kind, name, values)`: mint a
    characterization entry, emitting `HardwareComponentCharacterized`.
    Recording again under the same name completes that component's history.
  - `mount_hardware_component(kind, name, known_names, mounted_name)`:
    declare the mounted component. Refused (`ValueError`) if never
    characterized; logged no-op if already mounted; otherwise returns a
    `HardwareComponentSelection` and emits `HardwareComponentMounted`.
  - `mounted_component_name(selections)` / `current_characterization(entries,
    name)`: the two reading rules (latest selection = mounted, latest entry =
    current characterization), stated once so the service and the acquisition
    export can't diverge.
  - `resolve_current_hardware_signature(fallback, mounted_conditioning,
    mounted_excitation)`: the board parts of `HardwareSignature` are the
    mounted boards; the template `fallback` (generic names) only fills a kind
    nobody selected yet, with a WARNING (incomplete configuration). The
    sensor part stays with `SensorCalibrationService`.
- Provide `reconstitute(...)`, the single explicit entry point to rebuild
  the aggregate from persisted repository state (rehydration) — distinct
  from the default constructor `Calibration()`, which represents a
  brand-new aggregate. `reconstitute()` never emits domain events: reading
  back persisted state is not a business transition.
- Stay "behavioral": it does NOT hold the full, unbounded history of
  calibration entries in memory (append-only, unlimited) — the repository
  is authoritative for reading history, mirroring the existing separation
  between `StepScan._points` and `IAcquisitionDataRepository`.

## Design

- `@dataclass` (aggregate root, mutable — matches `StepScan`'s pattern,
  not frozen).
- `synchronous_detection_compensation_enabled: bool = False`.
- `_domain_events: List[DomainEvent]` — internal, drained via the
  `domain_events` property (get-and-clear, exactly like `StepScan.domain_events`).
- No dependency on `IDomainEventBus` — the aggregate only appends to its
  internal event list; publishing is the application service's job.
- `reconstitute()` is a `@staticmethod` factory: the application service
  must always call `Calibration.reconstitute(calibration_repository.load_compensation_enabled())`
  rather than constructing `Calibration(...)` positionally for rehydration,
  keeping one explicit, extensible point of reconstruction.
