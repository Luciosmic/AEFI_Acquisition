# fake_thread_pool_task_runner — Intention

## Rationale

`ThreadPoolTaskRunner` spawns daemon threads, making test assertions timing-dependent. `FakeThreadPoolTaskRunner` removes all threading by executing the callable synchronously in the calling thread.

## Responsibility

Implement `IAsyncTaskRunner` for tests: `submit(task)` calls `task()` synchronously and returns a completed `TaskHandle`.

## Design

- No threads, no daemons, no joins.
- `_CompletedTaskHandle.is_running()` always returns `False`.
- `_CompletedTaskHandle.wait()` is a no-op.
- Tests can assert state immediately after `submit()` returns.
