# Responsibility
Translate a flat speed-config dictionary into per-axis `set_axis_params` calls on `ArcusPerformax4EXController`. Handles axis-specific keys (`x_hs`, `y_dec`, …) and global keys (`hs`, `dec`, …) with axis-specific keys taking priority. Skips an axis entirely when no parameter applies to it.

# Rationale
Decouples configuration representation (flat dict from UI or file) from the low-level driver API. Keeps the driver free of dispatch logic and makes the mapping rule testable in isolation without hardware.

# Design
- Iterates over a fixed axis list `("x", "y")` and param list `("ls", "hs", "acc", "dec")`.
- For each (axis, param) pair: prefers the axis-scoped key, falls back to the global key, defaults to `None`.
- Calls `set_axis_params` only when at least one resolved value is not `None`.
- No domain imports; depends solely on the driver class in the same infrastructure package.
