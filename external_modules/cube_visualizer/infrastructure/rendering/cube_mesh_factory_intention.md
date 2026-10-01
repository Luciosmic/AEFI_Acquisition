# cube_mesh_factory — Intention

## Rationale

The cube shows how the sensor is mounted. With the same color on the +X and
−X faces and nothing else, a 180° flip about any axis looks identical to the
original pose: the operator cannot tell which face of the sensor points
toward a source axis, which is exactly what a mounting error looks like. On
the physical bench the negative faces carry a piece of green electrical
tape: the same mark on screen shows the sign of each sensor axis and lets
the operator compare the cube with the real sensor directly, without
translating one convention into another.

## Responsibility

- Build the cube mesh with one color per sensor axis (X blue, Y yellow,
  Z red, matching the axis arrows), same color on both faces of an axis.
- Build the green markers mirroring the bench tape: one green disc centered
  on each negative face (−X, −Y, −Z), to be rotated with the cube.
- Apply a rotation to a mesh (returns a rotated copy).

## Design

- Each face color is derived from the face normal (axis = largest
  component), never from PyVista's cell order, which is
  `−X, +X, −Y, +Y, −Z, +Z` and not documented as stable.
- The sign is carried only by the marker (a darker negative face was tried
  on 2026-10-01 and dropped: redundant with the tape mark, and confusable
  with lighting shade at grazing angles).
- Markers: `create_negative_face_markers(size)` returns one merged mesh of
  three discs (`MARKER_RADIUS_RATIO` × size), lifted by
  `MARKER_OFFSET_RATIO` × size off the face to avoid z-fighting; colored
  `MARKER_COLOR` (dark grass green, like electrical tape) by the adapter.
