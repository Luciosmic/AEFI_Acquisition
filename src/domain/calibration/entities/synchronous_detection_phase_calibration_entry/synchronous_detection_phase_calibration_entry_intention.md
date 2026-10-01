# synchronous_detection_phase_calibration_entry — Intention

## Rationale

The calibration registry is append-only and constructive: each time an
operator records a calibration point, a new immutable entry is added,
never merged into or overwriting a previous one (decided explicitly with
the user). An entry needs its own identity (`entry_id`) so the repository
can reference/list individual records, distinguishing it from the
value objects it carries.

## Responsibility

- Bundle the hardware setup (`HardwareSignature`) with the calibration
  point(s) (`SynchronousDetectionPhaseCalibrationPoint`) measured on it,
  and the timestamp the entry was recorded.
- Guarantee an entry always carries at least one point — an entry with no
  points would be meaningless data.
- Provide `single(...)`, the only way `Calibration.record_synchronous_detection_phase_entry`
  mints a new entry from one freshly measured point, so `entry_id` and
  `recorded_at` are always generated consistently (fresh `uuid4()`, UTC
  `datetime.now()`), never passed in by a caller.

## Design

- `@dataclass(frozen=True)` — entity (identity = `entry_id`), immutable
  once recorded (append-only registry, per the constructive decision).
- `entry_id: UUID`, `hardware_signature: HardwareSignature`,
  `points: Tuple[SynchronousDetectionPhaseCalibrationPoint, ...]`,
  `recorded_at: datetime`.
- `__post_init__` raises `ValueError` if `points` is empty.
- `single(hardware_signature, point)` static factory: wraps one point into
  a one-element tuple, mints `uuid4()` and `datetime.now(timezone.utc)`.
