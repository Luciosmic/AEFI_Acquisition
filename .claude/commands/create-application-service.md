---
description: 'Create application service'
---

# Create Application Service

Scaffold a new application service following the AEFI DDD structure: a dedicated folder under `src/application/services/`, a service class, one or more port interfaces, and a test subfolder.

## When to Use

- Adding a new hardware capability that requires application-level orchestration
- Extracting logic from a presenter or infrastructure adapter into a proper service
- Adding a new use-case that coordinates multiple ports

## Checkpoints

- What is the name of the new service (e.g., `calibration`, `signal_processing`)?
- Which hardware ports does it need (motion, acquisition, export, or new)?
- Does it need an output port to notify the UI?
- What are the business-refusal outcomes of this use case (members of the Use Case error union)?
- Which infrastructure errors from each injected port must this service translate, and to which use-case error variant?

## Steps

### 1. Create the service folder

Create `src/application/services/<name>_service/` with the following structure:
- `__init__.py` (empty)
- `<name>_service.py`
- `i_<dependency>_port.py` for each infrastructure dependency
- `i_<name>_output_port.py` if the service needs to notify the UI
- `tests/__init__.py`
- `tests/<name>_service_test.py`

### 2. Implement the service class

```python
class <Name>Service:
    def __init__(self, <dependency>_port: I<Dependency>Port, event_bus: IDomainEventBus) -> None:
        self._<dependency>_port = <dependency>_port
        self._event_bus = event_bus

    def <command>(self, ...) -> OperationResult[<T>, <Name>UseCaseError]:
        """Command method. Enumerate every variant of <Name>UseCaseError this can return."""
        ...
```

Return expected failures via `OperationResult`. Raise ONLY for programmer errors (bug, precondition violated by caller code). Follow the application-service-structure standard: constructor injection only, no direct infrastructure imports.

### 3. Define port interfaces

For each dependency, create `i_<dependency>_port.py` using the port-interface-naming standard:

```python
from abc import ABC, abstractmethod

class I<Dependency>Port(ABC):
    @abstractmethod
    def <method>(self) -> <ReturnType>:
        pass
```

### 3.5. Declare the Use Case error union

Create `src/application/services/<name>_service/<name>_errors.py` declaring the closed union of business-refusal outcomes visible to callers:

```python
type <Name>UseCaseError = <DomainErrorA> | <DomainErrorB> | <ApplicationRefusalC>
```

Rules:
- Name variants after the *refused promise* in ubiquitous language — never after exception mechanisms.
- The union MUST NOT be `Exception` or `Any`, and MUST NOT include infrastructure error types directly.
- Infrastructure error types from ports are translated into use-case variants inside the service (see 3.6).

### 3.6. Translate infrastructure errors at the service boundary

Every port method returning `Result[T, <PortError>]` is unwrapped inside the service and mapped to a `<Name>UseCaseError` variant. Third-party exceptions never cross into the service — they are caught inside the adapter (see `/create-port-interface`). The service is the single cross-layer translation site.

### 4. Write first test

In `tests/<name>_service_test.py`, inherit from `DiagramFriendlyTest`, inject mock ports from `src/infrastructure/mocks/`, and test the main command method. Add at least one test per variant of `<Name>UseCaseError` proving the service *returns* the correct refusal (not that it raises).

### 5. Register in composition root

Add the service instantiation in `src/main.py` or the relevant composition root, wiring real infrastructure adapters to the new port interfaces.
