---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure `fake_thread_pool_task_runner` : Implement `IAsyncTaskRunner` for tests: `submit(task)` calls `task()` synchronously and returns a completed `TaskHandle`."
code: ["[[src/infrastructure/execution/fake/fake_thread_pool_task_runner.py]]"]
cause_de_changement: outil
implements: ["[[src/application/shared/ports/i_async_task_runner_intention]]"]
double_de: "[[src/infrastructure/execution/thread_pool_task_runner_intention]]"
---
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
