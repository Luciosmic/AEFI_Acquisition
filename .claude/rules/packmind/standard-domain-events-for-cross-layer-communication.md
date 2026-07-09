---
name: 'Domain Events for Cross-Layer Communication'
alwaysApply: true
description: 'Standardize cross-layer state-change communication in the AEFI system by modeling each transition as a `DomainEvent` dataclass in `src/domain/events/`, publishing via `IDomainEventBus` with the lowercase class name as the topic, subscribing in application service `__init__`, and forwarding only to interface `present_*` methods to keep services and presenters decoupled and avoid leaking infrastructure events.'
---

# Standard: Domain Events for Cross-Layer Communication

Standardize cross-layer state-change communication in the AEFI system by modeling each transition as a `DomainEvent` dataclass in `src/domain/events/`, publishing via `IDomainEventBus` with the lowercase class name as the topic, subscribing in application service `__init__`, and forwarding only to interface `present_*` methods to keep services and presenters decoupled and avoid leaking infrastructure events. :
* Application services subscribe to events in their `__init__` — never poll service state from the presenter
* Define every new state transition as a dataclass in `src/domain/events/` — one file per domain concept (e.g., `scan_events.py`, `motion_events.py`)
* Inherit from `DomainEvent` base class (`src/domain/events/domain_event.py`)
* Never publish infrastructure-level events (serial errors, raw ADC reads) to the domain event bus — wrap them as domain events first
* Output port methods (`present_*`) are the only consumers of forwarded events in the interface layer
* Publish events to `IDomainEventBus` using the lowercase class name as topic (e.g., `"scanstarted"`)

Full standard is available here for further request: [Domain Events for Cross-Layer Communication](../../../.packmind/standards/domain-events-for-cross-layer-communication.md)