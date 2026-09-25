# calibration_panel — Intention

## Rationale

`SensorCalibrationPanel` was first shipped as its own dock. When
`SourceGeometryCalibrationPanel` was added, the user asked to group every
calibration type in the same UI location instead of adding a second
separate dock. `CalibrationPanel` is the thin composition that makes this
possible without touching either sub-panel's internals: each stays a fully
self-contained, independently testable widget, and this wrapper just tabs
them together.

## Responsibility

- Host one `QTabWidget` with one tab per calibration type.
- Expose each sub-panel as a public attribute (`sensor_calibration_panel`,
  `source_geometry_panel`, and `hardware_component_panels[kind_key]`) so
  `dashboard_wiring.py` connects directly to their signals/slots — exactly as
  if each were still its own dock. No signal relaying, no logic of its own.
- `add_hardware_component_tab(kind_dto)`: one generic `HardwareComponentPanel`
  tab per hardware component kind (boards, signal generation chip, ADC,
  microcontroller, motors), added by the wiring since the kinds are listed by
  the application layer.
- Adding a future calibration type means adding one more sub-panel instance
  + one more `tabs.addTab(...)` line here — the sub-panel itself is built
  exactly like the first two, unaware it lives inside a tab.

## Design

- `QWidget` wrapping a `QTabWidget`. Zero business logic, zero Qt signals
  defined on `CalibrationPanel` itself.
- Registered in `Dashboard.panels["calibration"]` (replacing the earlier
  standalone `"sensor_calibration"` dock entry) — see `dashboard.py`.
