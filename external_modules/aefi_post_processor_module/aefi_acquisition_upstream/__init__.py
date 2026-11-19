"""
aefi_acquisition_upstream - The only place where this module borrows code from the acquisition application (see upstream_objects_intention.md).

Importing this package makes `import interface` and `import domain` resolve to `src/interface`, never to this module's own `interface/`:
launched as a script, the module's folder heads `sys.path` and its `domain`, `application`, `infrastructure` and
`interface` folders would shadow those of `src/`.
"""

import sys
from pathlib import Path

_MODULE_DIR = Path(__file__).resolve().parents[1]
_SRC_DIR = _MODULE_DIR.parents[1] / "src"


def _resolved(entry: str) -> Path:
    return Path(entry or ".").resolve()


def settle_sys_path() -> None:
    """Make `import interface` and `import domain` resolve to `src/`. Idempotent."""
    sys.path[:] = [entry for entry in sys.path if _resolved(entry) != _MODULE_DIR]
    if not any(_resolved(entry) == _SRC_DIR for entry in sys.path):
        sys.path.append(str(_SRC_DIR))


settle_sys_path()
