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
