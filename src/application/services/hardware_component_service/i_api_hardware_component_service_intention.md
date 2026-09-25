# i_api_hardware_component_service — Intention

## Rationale

Without an inbound contract, the presenter would depend on the concrete
service and its tests would need a real repository and event bus.

## Responsibility

- Query the kinds (`list_kinds`), the catalog (`list_components`) and the
  mounted component (`get_mounted_component`) of a kind.
- Commands: `record_characterization`, `mount_component`.

## Design

- ABC, `i_api_` prefix = inbound (Adapters -> Application). Kinds by string
  key so callers never import the domain enum.
