# event_bus_motion_synchronizer — Intention

## Rationale

Motion completion arrives asynchronously via the domain event bus. The scan loop (Application layer) needs a blocking primitive that returns typed `OperationResult` instead of subscribing to events itself. This adapter bridges those two worlds.

## Responsibility

Implement `IMotionSynchronizer` by subscribing to 4 motion event topics and translating each terminal state into `OperationResult[None, MotionSyncError]`.

## Design

- Subscribes at construction to: `motioncompleted`, `motionfailed`, `motionstopped`, `emergencystoptriggered`.
- `wait_for_motion(motion_id, timeout)` blocks on a `threading.Event` keyed by `motion_id`.
- `MotionStopped` / `EmergencyStopTriggered` have no `motion_id` → cancel all pending waits.
- No terminal outcome is lost: one published before the wait registers is kept for it; one landing as a wait times out is set under the lock and re-checked there by the waiter. A caller may therefore poll with short waits (the fly scan does, to project samples while the motor moves) — before this, a completion landing at a timeout edge was dropped and a whole line timed out.
- Always returns `OperationResult` — never raises for expected outcomes.
- `close()` unsubscribes from the bus to avoid memory leaks.
