# fake_event_bus_motion_synchronizer — Intention

## Rationale

`EventBusMotionSynchronizer` blocks until bus events arrive, which requires real hardware in tests. `FakeEventBusMotionSynchronizer` replaces the blocking wait with pre-programmed `OperationResult` values.

## Responsibility

Implement `IMotionSynchronizer` for tests: each `wait_for_motion()` call pops the next pre-programmed `OperationResult` from the configured list.

## Design

- Constructor accepts `List[OperationResult]` — the "program" for the test.
- Pops results in FIFO order; raises `IndexError` when exhausted (test bug detector).
- `call_count` and `received_motion_ids` are public for test assertions.
- Must reproduce all 4 `MotionSyncError` variants: `MotionTimeout`, `MotionHardwareFailed`, `EmergencyStop`, `MotionStoppedExternally`.
