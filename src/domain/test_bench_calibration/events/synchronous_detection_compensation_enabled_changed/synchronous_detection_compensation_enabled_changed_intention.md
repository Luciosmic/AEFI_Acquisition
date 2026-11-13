---
type: evenement-de-domaine::solidai-ddd
tldr: "Signal that `Calibration.synchronous_detection_compensation_enabled` actually changed value."
code: ["[[src/domain/test_bench_calibration/events/synchronous_detection_compensation_enabled_changed/synchronous_detection_compensation_enabled_changed.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/test_bench_calibration/calibration_intention]]"
---
# synchronous_detection_compensation_enabled_changed — Intention

## Rationale

Enabling/disabling the synchronous detection phase compensation is a
domain-level, persisted flag with an application-visible side effect
(immediate re-application of the correction on ch3). The UI toggle and any
other subscriber (e.g. the synchronous detection presenter) need to be
notified exactly once per actual state change, not on every click of an
idempotent no-op.

## Responsibility

- Signal that `Calibration.synchronous_detection_compensation_enabled`
  actually changed value.
- Published once per actual change — `Calibration.set_synchronous_detection_compensation_enabled`
  is idempotent and does not emit this event when the value is unchanged.

## Design

- `@dataclass(frozen=True)` inheriting `DomainEvent`.
- `enabled: bool` — the new state.
- Topic of publication: `"synchronousdetectioncompensationenabledchanged"`.
