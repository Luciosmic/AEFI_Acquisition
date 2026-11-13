---
type: atome::solidai-atome
tldr: "Decouples configuration representation (flat dict from UI or file) from the low-level driver API."
code: ["[[src/infrastructure/hardware/arcus_performax_4ex/adapter_arcus_speed_config.py]]", "[[src/infrastructure/hardware/arcus_performax_4ex/adapter_lifecycle_arcus_performax4ex/adapter_lifecycle_arcus_performax4ex.py]]", "[[src/infrastructure/hardware/arcus_performax_4ex/adapter_motion_port_arcus_performax4ex/adapter_motion_port_arcus_performax4ex.py]]", "[[src/infrastructure/hardware/arcus_performax_4ex/arcus_advanced_configuration/arcus_advanced_configuration.py]]", "[[src/infrastructure/hardware/arcus_performax_4ex/composition_root_arcus.py]]", "[[src/infrastructure/hardware/arcus_performax_4ex/driver_arcus_performax4ex.py]]"]
cause_de_changement: outil
---
# Responsibility
Translate a flat speed-config dictionary into per-axis `set_axis_params` calls on `ArcusPerformax4EXController`. Handles axis-specific keys (`x_hs`, `y_dec`, …) and global keys (`hs`, `dec`, …) with axis-specific keys taking priority. Skips an axis entirely when no parameter applies to it.

# Rationale
Decouples configuration representation (flat dict from UI or file) from the low-level driver API. Keeps the driver free of dispatch logic and makes the mapping rule testable in isolation without hardware.

# Design
- Iterates over a fixed axis list `("x", "y")` and param list `("ls", "hs", "acc", "dec")`.
- For each (axis, param) pair: prefers the axis-scoped key, falls back to the global key, defaults to `None`.
- Calls `set_axis_params` only when at least one resolved value is not `None`.
- No domain imports; depends solely on the driver class in the same infrastructure package.
