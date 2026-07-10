# thread_pool_task_runner — Intention

## Rationale

The Application layer needs to run callables in the background without knowing the concurrency mechanism. `ThreadPoolTaskRunner` is the default production implementation: one daemon thread per submitted task.

## Responsibility

Implement `IAsyncTaskRunner` using `threading.Thread(daemon=True)`.  
Single cause of change: the concurrency primitive (thread per task → asyncio → process pool).

## Design

- `submit(task)` spawns a daemon thread and returns `_ThreadTaskHandle` immediately.
- `TaskHandle.wait()` delegates to `Thread.join(timeout)`.
- No knowledge of domain aggregates, events, or scan/probe business logic.
