---
type: adaptateur::solidai-hexagonal
tldr: "Adaptateur `thread_pool_task_runner` : Implement `IAsyncTaskRunner` using `threading.Thread(daemon=True)`."
code: ["[[src/infrastructure/execution/thread_pool_task_runner.py]]"]
cause_de_changement: outil
implements: ["[[src/application/shared/ports/i_async_task_runner_intention]]"]
---
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
