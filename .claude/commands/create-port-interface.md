---
description: 'Create port interface'
---

# Create Port Interface

Scaffold a new port interface (ABC) to abstract an infrastructure dependency. Port interfaces allow application services to be tested without real hardware.

## When to Use

- Introducing a new hardware adapter that a service needs to use
- Extracting a hard dependency from a service into a testable abstraction
- Defining the contract for a new output port (service → UI notification)

## Checkpoints

- What is the role of this port (e.g., `motion`, `acquisition`, `export`, `output`)?
- Which service will consume this port?
- Is it an input port (service calls infrastructure) or output port (infrastructure/service notifies UI)?
- What are the technical failure modes this port exposes (the members of the port error union)?
- Which third-party exceptions inside the Real adapter map to each variant?

## Steps

### 1. Create the port file

Place the file alongside the consuming service:
`src/application/services/<service_name>/i_<role>_port.py`

### 2. Implement the ABC

```python
"""
<Role> Port Interface

Responsibility:
- Define abstract interface for <role> operations

Rationale:
- Hexagonal Architecture: application depends on ports, not concrete adapters
- Enables testing with fake implementations

Design:
- Abstract Base Class (ABC)
- Pure interface, no implementation
- Methods return `Result[T, <Role>Error]` — never bare types for fallible operations
"""
from abc import ABC, abstractmethod

class I<Role>Port(ABC):
    @abstractmethod
    def <primary_method>(self) -> Result[<T>, <Role>Error]:
        """<What this method does and what it returns>."""
        # No third-party exception (pyserial, PySide6, requests) may appear in this signature.
        # Those are caught once inside the Real adapter and translated to a <Role>Error variant.
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Check if the <role> is ready."""
        pass
```

### 2.5. Declare the port-scoped error type

For infrastructure-facing (outbound) ports, create `src/infrastructure/<adapter>/errors/<adapter>_errors.py` with a sealed union of technical failure modes:

```python
type <Role>Error = DeviceNotConnected | ProtocolTimeout | ChecksumMismatch
```

Rules:
- The port's ABC methods return `Result[T, <Role>Error]` (never `Result[T, Exception]`, `Result[T, Any]`, or a `Result` typed with a domain/application error).
- The union is closed: every technical failure mode of the underlying dependency is a named variant.
- No third-party exception type appears in this union — variants are named after the *refused promise*, not the exception class.

### 3. Create the Fake and align its failure modes with Real

Create `src/infrastructure/<adapter>/fake/fake_<adapter>.py` implementing the port with predictable test behavior. The Fake MUST return the same `Result` variants under the same triggers as the Real adapter — this Fake↔Real failure-mode symmetry is the invariant that lets application tests using the Fake match production behavior.

### 4. Update the consuming service

Inject the port via the service constructor and use only the abstract interface methods. The consuming service is responsible for unwrapping `Result[T, <Role>Error]` and translating each variant into its own use-case error union.

### 5. Document the failure-mode contract for Real and Fake

In the port's `intention.md` (or module docstring), enumerate the failure modes both Real and Fake must reproduce. This documented contract is the acceptance criterion for both implementations.
