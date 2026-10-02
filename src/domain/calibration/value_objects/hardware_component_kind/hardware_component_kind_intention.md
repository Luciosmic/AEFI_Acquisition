# hardware_component_kind — Intention

## Rationale

The bench is assembled from product modules — the AEFI sensor, conditioning
and excitation boards, a signal generation chip (AD9106), an ADC, a microcontroller, motors, a stepper driver.
Each changes only when the module is swapped, and each is described by a few
essential physical quantities. Without one place stating which kinds exist
and which quantities matter for each, every kind would grow its own value
object, entity, repository, service and panel — six near-identical copies
drifting apart — and "what characterizes an ADC" would be scattered across
the code instead of being part of the domain.

## Responsibility

- Enumerate the component kinds (`HardwareComponentKind`), each with a
  display label and its tuple of `QuantitySpec`.
- `QuantitySpec(key, label, unit, curve_x_label=None)`: a scalar quantity,
  or a curve y(x) when `curve_x_label` is set (microcontroller optimal
  acquisition rate vs n_avg).

## Design

- `Enum` + module-level tables: adding or changing a quantity is one line
  in `_QUANTITIES`, and the UI tab, persistence and export follow.
- Keys are persisted: renaming one orphans recorded values (they are then
  read as not characterized). Conditioning board keys keep the names used by
  the first, board-specific registry (`gain`, `bandwidth_hz`,
  `noise_density_v_per_sqrt_hz`).
- Quantity lists are a starting point (2026-09-25): ADC quantities are
  proposals, meant to be refined as they get characterized.
- Motors and stepper driver (2026-10-01) carry only what belongs to the
  product: steps per revolution and rated current for the motor, max current
  for the driver. Distance per pulse depends on the whole chain (microstepping
  set on the driver, mechanics) and lives in the mechanical transmission
  calibration, which references both mountings. The motors' former
  `step_um`, `max_speed_mm_per_s`, `acceleration_mm_per_s2` were never
  recorded and are removed.
