---
description: 'Scaffold and publish a new domain event dataclass in the appropriate `src/domain/events/*_events.py` file to standardize cross-layer communication and ensure downstream consumers have all required state-change data when aggregates transition or new hardware lifecycle events are introduced.'
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

### 3. Publish in the aggregate or service

In the domain aggregate or application service, after the state change:

```python
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
