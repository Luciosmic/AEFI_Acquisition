# bench_configuration_panel — Intention

## Rationale

The component catalog (declare a component, record its characterization,
mount it) first lived in the Calibration panel, next to the sensor
calibration and the transmission. The two belong to different contexts of
the bench: `test_bench_configuration` says what the bench is made of,
`test_bench_calibration` measures how it behaves. Mixed in one dock, the
operator could not tell "which board is mounted" from "what did I measure",
and on 2026-11-27 the human asked to stop mixing the contexts.

## Responsibility

- Host one `QTabWidget` with one tab per hardware component kind, through
  `add_hardware_component_tab(kind_dto)`; the kinds are listed by the
  application layer and added by the wiring.
- Group the tabs by what the operator works on: « Capteur » top-level,
  « Électronique » (conditioning board, excitation amplification, and the
  « Unité de conversion entre signaux numériques et analogiques » holding
  the DDS, the ADC and the microcontroller, from the kind's
  `assembly_key`), « Mouvement » (motors, stepper driver).
- Expose each component tab in `hardware_component_panels[kind_key]` so
  `dashboard_wiring.py` connects it directly, including the prefill of the
  microcontroller and ADC forms by the measurements of the Calibration panel.
- Hold no calibration.

## Design

- `QWidget` wrapping a `QTabWidget`, zero business logic, zero Qt signals of
  its own; groups are created with their first tab.
- Registered in `Dashboard.panels["bench_configuration"]`, shown as
  « Configuration du banc » in the Hardware group of the taskbar.
