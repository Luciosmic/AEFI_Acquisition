---
description: 'Create domain event'
---

# Create Domain Event

Scaffold a new domain event representing a significant state transition in the AEFI system. Domain events are the only sanctioned mechanism for cross-layer communication.

## When to Use

- A domain aggregate transitions to a new state that other layers need to know about
- Adding a new hardware lifecycle event (e.g., calibration started, sensor connected)
- Extending an existing event file with a new event type

## Checkpoints

- Which domain concept does this event belong to (scan, motion, system, acquisition)?
- What data must the event carry to allow downstream consumers to act?
- Is there an existing events file for this concept (e.g., `scan_events.py`) or do you need a new one?
- Which domain invariant must hold for this event to be emissible?
- What is the Domain error name (ubiquitous language, not exception class) returned when the invariant refuses?

## Steps

### 1. Locate or create the events file

Events are grouped by domain concept in `src/domain/events/`:
- `scan_events.py` — scan lifecycle events
- `motion_events.py` — motion/positioning events
- `system_events.py` — system startup/shutdown
- `continuous_acquisition_events.py` — streaming acquisition

For a new concept, create `src/domain/events/<concept>_events.py`.

### 2. Define the event dataclass

```python
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from domain.events.domain_event import DomainEvent

@dataclass
class <EventName>(DomainEvent):
    """Raised when <describe the state transition>."""
    <relevant_field>: <Type>
    # Add all data consumers will need — avoid requiring them to query back
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
```

### 2.5. Guard the invariant with a Domain error before emission

Before publishing the event, the aggregate method must validate the invariant. On violation, return `Err(<DomainInvariantError>)` from the aggregate mutation method — never publish the event and never raise. Only on `Ok` does emission proceed.

```python
def <mutation>(self, ...) -> OperationResult[None, <DomainInvariantError>]:
    if not self._invariant_holds(...):
        return OperationResult.fail(<DomainInvariantError>(...))
    # invariant OK → mutation + emission proceed
    self._state = ...
    self._pending_events.append(<EventName>(...))
    return OperationResult.ok(None)
```

The Domain error is named after the *refused promise* in ubiquitous language (e.g., `ScanAlreadyRunning`) — never after the exception mechanism (e.g., `IllegalStateException`).

### 3. Publish in the aggregate or service

Domain events represent facts that *happened*. If the invariant refused, no fact happened — so no event is emitted. The publish call is reachable only on the `Ok` branch of the aggregate mutation:

```python
# invariant already checked upstream; event is emitted ONLY on the Ok branch of the aggregate mutation
event = <EventName>(<relevant_field>=<value>)
self._event_bus.publish("<eventname>", event)  # lowercase class name
```

### 4. Subscribe in the consumer

In the application service or presenter that reacts to the event:

```python
self._event_bus.subscribe("<eventname>", self._on_<event_name>)
```

### 5. Add to output port (if UI needs to react)

If the presenter must forward the event to the view, add a `present_<event_name>` method to the output port interface and implement it in the presenter.
