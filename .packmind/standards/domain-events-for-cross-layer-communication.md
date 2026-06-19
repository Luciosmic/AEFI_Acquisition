# Domain Events for Cross-Layer Communication

All significant state changes in the AEFI system are communicated across layers via domain events published on `IDomainEventBus`. This keeps services and presenters decoupled: the service does not know who is listening.

Evidence: `src/domain/events/scan_events.py`, `src/domain/events/motion_events.py`, `src/domain/events/system_events.py`, `src/application/services/scan_application_service/scan_application_service.py:68-78` (subscriptions), `src/interface/presenters/scan_presenter.py:35` (output port receives forwarded events)

## Scope

Python files that communicate state changes across `src/application/`, `src/domain/`, and `src/interface/`.

## Rules

* Define every new state transition as a dataclass in `src/domain/events/` — one file per domain concept (e.g., `scan_events.py`, `motion_events.py`)
* Inherit from `DomainEvent` base class (`src/domain/events/domain_event.py`)
* Publish events to `IDomainEventBus` using the lowercase class name as topic (e.g., `"scanstarted"`)
* Application services subscribe to events in their `__init__` — never poll service state from the presenter
* Never publish infrastructure-level events (serial errors, raw ADC reads) to the domain event bus — wrap them as domain events first
* Output port methods (`present_*`) are the only consumers of forwarded events in the interface layer
