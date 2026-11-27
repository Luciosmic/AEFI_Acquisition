# calibration_panel — Intention

## Rationale

`SensorCalibrationPanel` was first shipped as its own dock. When
`SourceGeometryCalibrationPanel` was added, the user asked to group every
calibration type in the same UI location instead of adding a second
separate dock. `CalibrationPanel` is the thin composition that makes this
possible without touching either sub-panel's internals: each stays a fully
self-contained, independently testable widget, and this wrapper just tabs
them together.

The component catalog later grew inside this panel, mixing the bench
configuration (what is mounted) with its calibration (what was measured).
On 2026-11-27 the human asked to stop mixing the two contexts: the catalog
moved to `BenchConfigurationPanel`, and this panel keeps only what belongs
to `test_bench_calibration`.

## Responsibility

- Host one `QTabWidget`: « Calibration capteur », « Géométrie source »,
  « Transmission », and « Unité de conversion entre signaux numériques et
  analogiques », which groups the measurements of that unit:
  « Microcontrôleur : débit d'acquisition » (`acquisition_throughput_widget`)
  and « ADC : cadence de sortie » (`adc_output_rate_widget`, ODR measured on
  DRDY at the oscilloscope).
- Expose each sub-panel as a public attribute so `dashboard_wiring.py`
  connects directly to its signals and slots. No signal relaying, no logic
  of its own.
- Hold no component catalog: the measured values prefill the microcontroller
  and ADC forms of the configuration panel, where the operator records them.
- Adding a future calibration type means adding one more sub-panel instance
  and one more `addTab(...)` line here.

## Design

- `QWidget` wrapping a `QTabWidget`. Zero business logic, zero Qt signals
  defined on `CalibrationPanel` itself.
- Registered in `Dashboard.panels["calibration"]` — see `dashboard.py`.
