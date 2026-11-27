---
type: value-object::solidai-ddd
tldr: "Enumerate the component kinds (`HardwareComponentKind`), each with a display label, its tuple of `QuantitySpec` and the assembly it belongs to (the digital-analog-signals-processing-unit groups the DDS, the ADC and the microcontroller)."
code: ["[[src/domain/test_bench_configuration/value_objects/hardware_component_kind/hardware_component_kind.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/test_bench_configuration/bench_configuration_intention]]"
---
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

The thesis graph splits a detection into two parts: the conditioning board,
and the digital-analog-signals-processing-unit ("unité de conversion entre
signaux numériques et analogiques"), which groups the ADC, the DDS and the
microcontroller. Without that grouping stated here, the application would
show three unrelated tabs where the thesis speaks of one unit, and the
conditioning board would sit among them as if it were a fourth member.

On 2026-11-27 the conditioning board in use turned out to output its
quadrature channels with P and N swapped (routing without crossing, straight
connectors to the unit): the ADC reads -Q. That sign belongs to the board,
and nowhere recorded it.

## Responsibility

- Enumerate the component kinds (`HardwareComponentKind`), each with a
  display label and its tuple of `QuantitySpec`.
- `QuantitySpec(key, label, unit, curve_x_label=None, allowed_values=None)`:
  a scalar quantity, a curve y(x) when `curve_x_label` is set
  (microcontroller optimal acquisition rate vs n_avg), or a scalar limited
  to `allowed_values` (a sign: -1 or +1).
- `HardwareComponentKind.assembly`: the `HardwareAssembly` the kind is part
  of, or None. Today one assembly,
  `DIGITAL_ANALOG_SIGNALS_PROCESSING_UNIT`, of the signal generation chip,
  the ADC and the microcontroller.
- The conditioning board declares `quadrature_output_sign`: -1 when it
  outputs -Q, +1 when it outputs Q, not characterized until checked.

## Design

- `Enum` + module-level tables: adding or changing a quantity is one line
  in `_QUANTITIES`, and the UI tab, persistence and export follow; the
  grouping is one line per kind in `_ASSEMBLIES`.
- Names follow the thesis graph: `digital_analog_signals_processing_unit`
  is its reference key, "Unité de conversion entre signaux numériques et
  analogiques" its label.
- Keys are persisted: renaming one orphans recorded values (they are then
  read as not characterized). Conditioning board keys keep the names used by
  the first, board-specific registry (`gain`, `bandwidth_hz`,
  `noise_density_v_per_sqrt_hz`); boards recorded before
  `quadrature_output_sign` existed read it as not characterized.
- The sign's unit is written `±1` in the catalog and exported as the UCUM
  dimensionless `1`.
- Quantity lists are a starting point (2026-09-25): ADC quantities are
  proposals, meant to be refined as they get characterized.
- Motors and stepper driver (2026-10-01) carry only what belongs to the
  product: steps per revolution and rated current for the motor, max current
  for the driver. Distance per pulse depends on the whole chain (microstepping
  set on the driver, mechanics) and lives in the mechanical transmission
  calibration, which references both mountings. The motors' former
  `step_um`, `max_speed_mm_per_s`, `acceleration_mm_per_s2` were never
  recorded and are removed.
