# Cube Sensor Field Simulator — Intention

## Rationale

The AEFI sensor is a physical 8mm cube, not a point — per user decision
2026-07-31, each of its 6 faces reads the *spatial average* of the potential
over that face's area, not a single point sample. Per axis, the field is the
finite-difference between the two opposing faces' averaged potentials,
divided by the cube dimension — this is what the physical differential
electrodes actually measure, and it captures the field's curvature across
the sensor's finite extent instead of a point-gradient approximation.

The cube's orientation reuses `external_modules/cube_visualizer/domain/
sensor_rotation.py` (the canonical source of truth for sensor-orientation
math in this repo, per user pointer 2026-07-31) rather than re-deriving
rotation math locally, and defaults to `aefi_device_config.json`'s measured
`sensor.calibration.sensor_to_lab_rotation` — the real calibrated
orientation, not the arbitrary demo angles `main.py` used to hardcode.

Noise placement (per user correction 2026-07-31): the MCU/ADC's own
quantization noise is negligible at this signal scale and stays in
`FakeMCUSerialCommunicator` (+/-2 raw counts — genuine dither, not an
injected floor). The noise that actually matters physically belongs at the
DDS *source* (amplitude stability jitter) and at the *sensor* (its own +
conditioning-electronics read noise) — both modeled here, since this class
is where a single "instant sample" of the whole excitation+sensing chain is
computed.

## Responsibility

- Own the sensor's physical properties: cube dimension, orientation
  (rotation), and calibration gain (field-to-voltage conversion) — none of
  which belong in `PointChargeFieldSimulator` (spheres-only physics).
- For each local axis (sensor's own X/Y/Z), sample a grid of points across
  both opposing faces, transform them into source frame via the sensor
  rotation (sensor center fixed at the exact geometric center of the 4
  spheres — the 2026-07-31 "point sensor" simplification still holds for
  cube *placement*, only its *extent* changes), average the potential
  (`PointChargeFieldSimulator.potential_at`) over each face, then
  finite-difference: `E_axis = (V_neg_face_avg - V_pos_face_avg) / dimension`.
- Convert each axis field (V/m) to simulated sensor voltage via the gain
  (`sensor.calibration.gain`, `[V/m]/V` — same convention as before).
- Model source jitter (`source_level_noise_std_percent`, applied to the
  driven DDS level) and sensor read noise (`sensor_noise_std_v`, applied to
  the final per-axis voltage) — both default to 0.0 (deterministic) in
  `__init__`/`from_config`, so existing tests are unaffected; only
  `from_default_config()` (the real app's mock wiring) turns them on, with
  placeholder magnitudes (0.01 percentage-points, 0.02mV — reduced 10x from
  the initial guess per user feedback 2026-07-31) pending real measured
  values.

## Design

- `FACE_GRID_POINTS = 5` (25 samples/face, cell-center sampling — avoids
  double-counting shared edges/corners across faces). Cheap: 6 faces * 25
  points * 4 spheres = 600 potential terms per `compute_axis_voltages` call.
- Because the sensor's own local axes are used directly as the face-pair
  axes, the finite-difference result is already expressed in the *sensor
  frame* — no separate post-hoc rotation step is needed (unlike the earlier
  point-model, which rotated a single Source Frame vector). This subsumes
  what `ExcitationAwareAcquisitionPort._sensor_rotation` used to do.
- Source jitter is drawn *once* per `compute_axis_voltages()` call, shared
  by all 150 face-grid potential evaluations within that call — it
  represents the driven voltage at one instant, not per-point spatial noise;
  redrawing it per point would be physically wrong (and would partially
  average itself out across the face, understating the jitter).
