from __future__ import annotations
from typing import Optional

from infrastructure.hardware.arcus_performax_4EX.driver_arcus_performax4EX import ArcusPerformax4EXController


class ArcusSpeedConfigAdapter:
    """Translates a flat speed-config dict into per-axis set_axis_params calls."""

    _AXES = ("x", "y")
    _PARAMS = ("ls", "hs", "acc", "dec")

    def __init__(self, controller: ArcusPerformax4EXController) -> None:
        self._controller = controller

    def apply_config(self, config: dict) -> None:
        for axis in self._AXES:
            kwargs: dict[str, Optional[int]] = {}
            for param in self._PARAMS:
                axis_key = f"{axis}_{param}"
                if axis_key in config:
                    kwargs[param] = config[axis_key]
                elif param in config:
                    kwargs[param] = config[param]
                else:
                    kwargs[param] = None

            if any(v is not None for v in kwargs.values()):
                self._controller.set_axis_params(axis, **kwargs)
