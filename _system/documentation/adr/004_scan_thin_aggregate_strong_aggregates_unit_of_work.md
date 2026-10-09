# ADR-004: Thin `Scan` Aggregate, Strong Acquisition Aggregates, One Aggregate per Transaction

## Status
Accepted — implemented 2026-10-09 (steps 1-9 of the scan domain refactoring), amended 2026-10-09 with the fly-scan line rollback on pause (see "Fly-scan line atomicity"). Hardware validation of the fly-scan and Narda paths is still pending (see Consequences).

## Context

Before this refactoring, `StepScan` was one large aggregate that did three jobs at once: it carried the scan lifecycle (status, pause/resume/cancel/fail), it **contained** every acquired point, and it **completed itself** when the last point arrived. The fly-scan was a transient `StepScan` subclass (`FlyScan`) with the same flaw. Consequences:

- A single aggregate, loaded with measurements, carried the transaction of every point: one acquired point locked the whole scan.
- No aggregate said "this point has exactly N valid samples": a point built from fewer samples than requested looked like a complete point.
- There was a double state (points held in `StepScan` and again in the application service's progress counters), and several emitters of `ScanCompleted` depending on configuration.
- The Narda electric-field probe published its averaged measurement straight onto the event bus, outside any aggregate and any transaction. The scan could not know whether its field measurements were complete.

The starting note is [`inbox/le-scan-est-un-artefact-de-tracage-gdc-qui-denote-le-processus-physique-et-non-l-occurrent-lui-meme.md`](../../../inbox/le-scan-est-un-artefact-de-tracage-gdc-qui-denote-le-processus-physique-et-non-l-occurrent-lui-meme.md) (commit `cd54cab`, session 2026-10-08). It is kept as the source of the reasoning; this ADR is the consolidated decision.

## Decision

### Ontological frame

A `Scan` is **not** the physical acquisition process. It is the information artefact that *denotes* that process: a Generically Dependent Continuant (GDC) in BFO/IAO terms. The bridge to DDD:

| Ontology | DDD |
|---|---|
| Independent continuant (bench, spheres, electrode) | Aggregate root |
| Occurrent (the physical scan) | Sequence of Domain Events |
| Process boundaries | Immutable events (`ScanStarted`, `ScanCompleted`) |
| Scalar measurement | Value object `Sample` |
| `PENDING` | "the artefact does not yet denote a completed process" |

### Aggregates

- **`Scan`** (thin, `src/domain/scan/`). References acquisitions **by identity**, never by containment. Observable lifecycle `PENDING` -> `STARTED` -> `COMPLETED`. It declares its expected **sources** as `ExpectedSource(count, required)`; `mark_acquired(source, acquisition_id)` is idempotent per (source, id) and the scan becomes `COMPLETED` when every *required* source has received its `count`. It is agnostic of the probe: source names are constants owned by the emitting aggregates.
- **`AefiPoint`** (strong, step-scan). Exactly N valid samples, recorded atomically, otherwise `AefiPointIncompleteError` and no state change. An incomplete point does not exist in the domain.
- **`AefiLine`** (strong, fly-scan, deliberately *exploratory*). Grid points are projected value objects `LineGridPoint`, not aggregates. Invariant: all points of the line or nothing; one transaction per line (~81 for the default grid).
- **`NardaPoint`** (strong, electric-field probe). N field samples (plus N baseline samples when differential), or nothing. Carries `point_index` because export and UI correlate by index.

All acquisition events share the contract `ProbeAcquisitionEvent` (`scan_id`, `source`, `acquisition_id`). **Adding a sensor = its aggregate + its topic in `ScanClosureHandler` (wired in `main.py`) + its source declaration in the `Scan`.**

### Unit of Work rule

- **One aggregate per transaction** (`IUnitOfWork`, `InMemoryUnitOfWork`). Events are published **after** commit.
- `ScanClosureHandler` listens to the acquisition topics and closes the `Scan` in a **separate** UoW (eventual consistency between acquisition and scan completion).
- **Handler failure: no automatic retry** (principle "no hidden automation": visible state and operator-triggered actions only). The handler publishes a visible `ScanClosureFailed` (source, acquisition_id, reason) and logs it. Because `InMemoryEventBus` swallows handler exceptions, the handler catches its own errors. The step-scan application service subscribes to `ScanClosureFailed`, fails the scan and publishes `ScanFailed` (commit `bf741df`), otherwise the scan would block silently and the export stay open.

### Fly-scan line atomicity: a pause inside a line rolls the line back

`AefiLine` is atomic, so a line interrupted by a pause is **abandoned and redone from its start**; partial data never exists in the domain nor in the export.

- The fly-scan loop buffers the grid points of the line being swept. The legacy `ScanPointAcquired` of a line are published **only once the line is complete, right before its commit** (all of them before `ScanCompleted`; `_acquired_count` and `get_status` advance by line, the pause index is a line start). Nothing of an uncommitted line reaches the export or the counters.
- `pause_scan` increments a `_pause_epoch` (plain int, read across threads like `_acquired_count`). The loop snapshots it at the start of each line attempt and compares it after the start move, at each polling turn of the sweep (~20 ms), after the sweep and just before the publication. A changed epoch (even if the scan was resumed since) abandons the line: partial points dropped, **motor stopped at once** via `IMotionPort.stop()` (not left to finish its sweep), `is_moving()` polled until it stops, ADC/position queues drained, a visible `AefiLineAbandoned(scan_id, line_index, reason, discarded_points)` published on the bus (no UoW: the line never existed as an aggregate), then the loop waits for the resume and redoes the **same** line from its start. A pause landing after the last comparison takes effect on the next line (this one is complete and gets committed).
- A **provisional preview** keeps the live view: `AefiLinePreviewPointAcquired` is published during the sweep for the UI only (`present_scan_line_preview`); the export and the counters ignore it, and the definitive `ScanPointAcquired` of the commit overwrite it by position.
- A line is committed only while the scan is still `RUNNING` (a cancelled or failed scan never commits its line in progress).

Alternatives not retained: **publish points live and withdraw them from the export on abandon** (the CSV writer has no withdraw primitive, HDF5 would need new code, and every future consumer would need the same retraction); **let the line finish and keep the passed points in `pending`** (the previous behaviour: the motor kept moving while paused, and the line committed after the pause mixed two operator contexts). The loss of the "points emitted live" requirement (and of its test) is accepted and replaced by the preview.

`StepScan` remains as a **lifecycle shell** (statuses, pause/resume/cancel/fail, legacy events); it no longer holds points nor emits `ScanCompleted`. `FlyScan` is deleted; the fly-scan goes through `AefiLine` and the thin `Scan`.

## Alternatives considered, not retained

- **`StepScan` keeping its points and self-completing** (the previous state): double state, no "N samples" invariant, per-point locking of a large aggregate.
- **`Scan` with two exclusive modes** (`expected_points` XOR `expected_lines`): couples the scan to each acquisition kind; every new probe would change the aggregate. Replaced by declared sources.
- **Fly-scan grid points as `AefiPoint` aggregates**: 6561 transactions for an exploratory measurement; strong-aggregate rigour not justified there.
- **Separate `FlyScan` aggregate / transient subclass**: first narrowed to a subclass of `StepScan` (`85be3c2`), then deleted (`8deb0c3`) once `AefiLine` existed.
- **`Scan` indifferent to Narda**: rejected, the scan must be able to reference any probe and know it is complete only with its field measurements.
- **Automatic retry / reconciliation** of a failed closure: hidden behaviour, contrary to the visible-state principle.
- **Modifying `Scan` and `AefiPoint` in the same UoW**: a sign that the boundaries were drawn wrongly, the exact smell the refactoring removes.

## Consequences

### Positive
- A point (AEFI or field) or a line is complete or does not exist; a scan is complete only when every required source says so.
- `ScanCompleted` has a single emitter (the thin `Scan`); no double state in `StepScan`.
- Probe-agnostic scan: a new sensor does not touch the `Scan` aggregate beyond its source declaration.
- A closure failure is visible (event + log), never silent.

### Negative / known debt
- The thin `Scan` stays `STARTED` after a cancellation or failure: there is no `CANCELLED`/`FAILED` terminal state. An operator reconciliation command is still to be built.
- Decided, not yet implemented: an optional source that fails must emit a visible event (today an optional source failing is silent).
- `AefiPoint` carries neither index nor baseline. The baseline still travels through the legacy `ScanPointAcquired`, emitted by `StepScan` **before** the commit; export remains subscribed to legacy events (reading through repositories was postponed).
- `ScanStarted` of the new model is absent: `Scan.start()` emits nothing (the legacy `ScanStarted` requires a scan config and has the same topic name).
- Measured cost per point in synchronous step-scan: about +25 us at WARNING level and about +150 us at INFO level compared to before, mostly logging. Negligible against motion time, to be measured on real hardware. ADR-003 places the timing uncertainty in the FTDI/MCU chain, not in Python.
- The UoW is a single, non-thread-safe instance. Only the scan loop commits; pause/cancel/`get_status` never touch the UoW; progress uses local counters `_acquired_count`/`_expected_total`.
- The Narda probe is declared required at scan start if it is ready; a visible failure occurs if it disappears mid-scan. The fly-scan ignores auxiliary probes (logged warning, `ponytail:` in `scan_application_service.py`).
- `Position2D` units are not declared in the events (gap against the schema-first self-describing contracts standard).
- Vocabulary trap: the **line-scan** (step-scan along a straight line, built on `AefiPoint`) is not `AefiLine` (the swept line of the fly-scan).
- The immediate motor stop on pause (`IMotionPort.stop()`, a decelerating normal stop) is implemented on the application side and tested on the bench-faithful fake controller only; its behaviour on the real Arcus controller is **to be validated on the bench**. The Arcus worker still publishes a late `MotionCompleted` for the aborted move (harmless: the next wait uses another motion id).
- A cancel landing in the few microseconds of the synchronous publication of a line's points can leave up to N-1 published points of an uncommitted line (the commit is refused); accepted, the window is not worth a two-phase publication.

## References

Commits (checked with `git log`): `cd54cab` (source note), `2c58abd` (UoW), `7cdfd5b` and `cd35d1a` (`AefiPoint` and repository), `1265eab` (thin `Scan`), `dfd89dc` (closure handler), `704a556`..`8588fb3` (step-scan wired on the thin `Scan`, incl. `bf741df` `ScanClosureFailed`), `2514ea7`..`e904fb7` (`StepScan` without points, thin `Scan` sole emitter of `ScanCompleted`), `15a2c11` (cancel fix) and `a230f38` (source-agnostic `Scan`), `6d0e864`..`8deb0c3` (`AefiLine`, `FlyScan` deleted), `1d8e8f7`..`33eb642` (`NardaPoint`). Related: ADR-003 (timing budget).
