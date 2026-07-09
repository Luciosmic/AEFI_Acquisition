# coordinate_transformer

## Responsibility
Thin interface-layer utility that applies 3-axis Euler rotations (XYZ, extrinsic) to convert vectors between Sensor and Source coordinate frames.

## Rationale
The interface layer needs a simple, DTO-free API for coordinate conversion — e.g., for UI panels that allow the user to inspect or verify transformation results without going through the full application service protocol. The `TransformationService` in the application layer uses `SetRotationAnglesDTO` and guards behind an `enabled` flag; this class exposes the same scipy rotation logic with a direct, stateless-style API suitable for interface-level use.

## Design
- `set_rotation_angles(theta_x, theta_y, theta_z)` stores angles in degrees and builds a `scipy.spatial.transform.Rotation` with `from_euler('XYZ', ...)`.
- `sensor_to_source` applies the direct rotation; `source_to_sensor` applies the inverse.
- No enable/disable flag — the transformer always applies the rotation once angles are set.
- No domain imports, no event bus — pure computation.
