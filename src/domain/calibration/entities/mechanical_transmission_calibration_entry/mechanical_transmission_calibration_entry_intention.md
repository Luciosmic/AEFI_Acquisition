# mechanical_transmission_calibration_entry — Intention

## Rationale

Every position the bench reports and every position a scan asks for goes
through one conversion: distance per motor pulse. Without it in the domain,
the factor lives in the motion controller's config file (`microns_per_step`
in `arcus_default_config.json`), as if it were a property of the Arcus
controller — which means that changing the driver's microstepping or the
mechanics changes every measured position without leaving any trace, and
that a missing file silently falls back to a stale constant (43.6 µm, the
1/8 microstepping value: positions off by 2). It also means a fly scan has
no way to know the speed in mm/s: only the controller knows its pulse rate.

The factor is not a property of one component: it comes from the whole
chain — the motor, the stepper driver *as set* (microstepping), and the
mechanics — and it is characterized as such, pulse by pulse: measured on
the bench (lidar against the pulse count), not derived from a travel per
motor revolution that nothing on the bench measures. Same
reasoning as the sensor's mounting angles: the products live in the
component catalog, how they are assembled on this bench is a bench
calibration that references their mountings.

## Responsibility

- Bundle, with identity and timestamp: the motor mounting and the stepper
  driver mounting it was set up with (by identity), the driver settings
  (microsteps, set current and its peak), and the distance per motor pulse
  (`microns_per_pulse`, µm) — the one conversion every position goes
  through.
- Refuse non-physical values (microsteps < 1, currents or distance per
  pulse <= 0, peak below set current).
- `driver_current_shortfall(rated_current_a)`: a readable warning when the
  current set on the driver is below the motor's rated current, else None.
  Not blocking: on this bench the TB6600 tops out at 3.5 A (4.0 A peak),
  under the Igus motor's 4.2 A — a known fact to keep visible, not an error.
  Both driver values are shown: the motor datasheet does not say whether
  4.2 A is RMS or peak.

## Design

- `@dataclass(frozen=True)`, `single(...)` factory (`entry_id`,
  `recorded_at` = now UTC) — same shape as `SensorCalibrationEntry`.
- Cross-references by identity only (`motor_mounting_id`,
  `stepper_driver_mounting_id`): the motor's rated current is read from its
  catalog characterization by the caller, never copied here.
- One transmission for both axes: X and Y use the same motor, driver
  setting and mechanics today (as the controller adapter always assumed).
  Split per axis if the two chains ever differ.
- µm/pulse is stored as characterized, with the `microsteps` it was measured
  at: changing the microstepping means a new measurement, a new entry. History:
  until 2026-11-10 the entry stored a travel per motor revolution (69.76 mm =
  21.8 µm × 200 × 16, itself 43.6 µm at 1/8 ÷ 2, never measured at 1/16); the
  lidar then measured 21.11 µm/pulse at 1/16
  (`_system/documentation/hardware_datasheet/motorisation/TB6600_Working_Configuration.md`).
