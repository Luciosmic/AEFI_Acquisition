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
- Enables testing with mock implementations

Design:
- Abstract Base Class (ABC)
- Pure interface, no implementation
"""
from abc import ABC, abstractmethod

class I<Role>Port(ABC):
    @abstractmethod
    def <primary_method>(self) -> <ReturnType>:
        """<What this method does and what it returns>"""
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Check if the <role> is ready."""
        pass
```

### 3. Create a mock adapter

Add `src/infrastructure/mocks/adapter_mock_i_<role>_port.py` implementing the new interface with predictable test behavior.

### 4. Update the consuming service

Inject the port via the service constructor and use only the abstract interface methods.
