---
type: racine-d-agregat::solidai-ddd
tldr: "Hold the domain-level, persisted synchronous_detection_compensation_enabled flag and mutate it idempotently, emitting…"
code: ["[[src/domain/test_bench_calibration/calibration.py]]"]
cause_de_changement: regle-metier
repositories:
  - ^: i-sensor-calibration-repository
    type: interface-de-repository::solidai-ddd
    tldr: "add(entry) : ajouter une entrée au registre sans jamais écraser ; find_all() et find_by_hardware_signature(signature) : relire les entrées."
    sens: sortant
    code: "[[src/domain/test_bench_calibration/repositories/i_sensor_calibration_repository.py]]"
  - ^: i-source-geometry-calibration-repository
    type: interface-de-repository::solidai-ddd
    tldr: "add(entry) : ajouter une entrée sans jamais écraser ; find_all() : relire toutes les entrées."
    sens: sortant
    code: "[[src/domain/test_bench_calibration/repositories/i_source_geometry_calibration_repository.py]]"
  - ^: i-mechanical-transmission-calibration-repository
    type: interface-de-repository::solidai-ddd
    tldr: "add(entry) : ajouter une entrée sans jamais écraser ; find_all() : relire toutes les entrées, dans l'ordre stocké."
    sens: sortant
    code: "[[src/domain/test_bench_calibration/repositories/i_mechanical_transmission_calibration_repository.py]]"
  - ^: i-synchronous-detection-phase-calibration-repository
    type: interface-de-repository::solidai-ddd
    tldr: "add(entry) : ajouter une entrée sans jamais écraser ; find_by_hardware_signature(signature) ; load et save de l'état du drapeau de compensation."
    sens: sortant
    code: "[[src/domain/test_bench_calibration/repositories/i_synchronous_detection_phase_calibration_repository.py]]"
---
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
- Mint new `MechanicalTransmissionCalibrationEntry` records via
  `record_mechanical_transmission_calibration_entry`, emitting
  `MechanicalTransmissionCalibrationEntryAdded` — the motion chain as set up
  on the bench (motor and stepper driver mountings by identity, microsteps,
  driver current, distance per motor pulse), source of the distance per
  motor pulse. Refused when no motor or no driver is mounted.
  `current_mechanical_transmission(entries, motor_mounting_id,
  driver_mounting_id)`: the latest entry set up with the motor and driver
  mounted now — None after a swap until a new transmission is recorded.
- Hardware components (boards, signal generation chip, ADC, microcontroller,
  motors — `HardwareComponentKind`) are no longer this root's concern: their
  characterization, mounting and the resolution of the hardware signature
  moved to the `BenchConfiguration` root of `test_bench_configuration`.
  Calibration entries reference a mounting by identity (`sensor_mounting_id`,
  `motor_mounting_id`) and a `HardwareSignature` by value; this aggregate
  imports the configuration, never the other way round.
- Provide `reconstitute(...)`, the single explicit entry point to rebuild
  the aggregate from persisted repository state (rehydration) — distinct
  from the default constructor `Calibration()`, which represents a
  brand-new aggregate. `reconstitute()` never emits domain events: reading
  back persisted state is not a business transition.
- Stay "behavioral": it does NOT hold the full, unbounded history of
  calibration entries in memory (append-only, unlimited) — the repository
  is authoritative for reading history.

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
