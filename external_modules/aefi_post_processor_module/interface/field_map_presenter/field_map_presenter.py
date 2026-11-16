"""
FieldMapPresenter - What the Map panel shows and does (see field_map_presenter_intention.md).
"""

import logging
import time
from typing import Dict, Optional, Tuple

import numpy as np

from ...application.field_map_service.dtos.load_step_dto import LoadStepDTO
from ...application.field_map_service.dtos.steps_request_dto import StepsRequestDTO

logger = logging.getLogger(__name__)


class FieldMapPresenter:
    def __init__(self, view, field_map_service, figure_factory):
        self._view = view
        self._service = field_map_service
        self._figure_factory = figure_factory
        self._cache: Dict[Tuple[str, str], object] = {}  # (acquisition file, step) -> FieldMapDTO
        self._step_mapping: Dict[str, str] = {}  # what the list shows -> the step name
        self._acquisition_name: Optional[str] = None
        self._acquisition_file: Optional[str] = None
        self._step_name: Optional[str] = None
        view.step_selected.connect(self.on_step_selected)
        view.cursor_moved.connect(self.on_cursor_moved)

    def show_acquisition(self, name: str, acquisition_file: str) -> None:
        """An acquisition was chosen: list its stored steps, draw none until one is chosen."""
        if name == self._acquisition_name and acquisition_file == self._acquisition_file:
            return
        self._acquisition_name, self._acquisition_file, self._step_name = name, acquisition_file, None
        logger.info("scan.selected scan=%s", name)
        self._list_steps()

    def refresh(self) -> None:
        """The steps of the shown acquisition may have changed (it was processed): forget what was read and list them again."""
        if self._acquisition_file is None:
            return
        self._cache = {key: value for key, value in self._cache.items() if key[0] != self._acquisition_file}
        chosen = self._step_name
        self._list_steps()
        for display_name, step in self._step_mapping.items():
            if step == chosen:
                self._step_name = chosen
                self._view.select_step(display_name)  # without emitting: the draw below is the only one
                self._draw()

    def on_step_selected(self, display_name: str) -> None:
        if not display_name:
            return
        self._step_name = self._step_mapping.get(display_name, display_name)
        self._draw()

    def on_cursor_moved(self, event) -> None:
        """Text for the value under the mouse, from a matplotlib motion event."""
        if not event.inaxes:
            self._view.set_cursor_text("Cursor: Out of axes")
            return
        x, y = event.xdata, event.ydata
        images = event.inaxes.images
        if not images:
            self._view.set_cursor_text(f"Cursor: x={x:.1f}, y={y:.1f}")
            return
        try:
            value = images[0].get_cursor_data(event)
            if value is not None and str(value) != 'nan':
                if isinstance(value, (int, float, np.number)):
                    self._view.set_cursor_text(f"Cursor: x={x:.1f}, y={y:.1f} | z={value:.4g}")
                else:
                    self._view.set_cursor_text(f"Cursor: x={x:.1f}, y={y:.1f} | z={value}")
            else:
                self._view.set_cursor_text(f"Cursor: x={x:.1f}, y={y:.1f} | z=NaN")
        except Exception:
            self._view.set_cursor_text(f"Cursor: x={x:.1f}, y={y:.1f}")

    def _list_steps(self) -> None:
        steps = self._service.list_steps(StepsRequestDTO(self._acquisition_file))
        self._step_mapping = {f"{i} - {step}": step for i, step in enumerate(steps, 1)}
        self._view.set_steps(list(self._step_mapping))
        self._view.clear_map()
        if steps:
            logger.info("scan.steps_loaded scan=%s steps=%s", self._acquisition_name, list(steps))
        else:
            logger.warning("scan.no_steps scan=%s", self._acquisition_name)

    def _draw(self) -> None:
        if self._acquisition_file is None or self._step_name is None:
            return
        start = time.time()
        key = (self._acquisition_file, self._step_name)
        if key in self._cache:
            field_map, source = self._cache[key], "Cache"
        else:
            try:
                field_map = self._service.load_step(LoadStepDTO(self._acquisition_file, self._step_name))
            except Exception as error:
                logger.exception(
                    "step.load_failed scan=%s step=%s error_type=%s error=%s",
                    self._acquisition_name, self._step_name, type(error).__name__, error,
                )
                return
            self._cache[key], source = field_map, "Disk"

        rotation = field_map.metadata.get('rotation_angles', 'N/A')
        if isinstance(rotation, (list, tuple, np.ndarray)):
            rotation_text = f"[{rotation[0]:.2f}, {rotation[1]:.2f}, {rotation[2]:.2f}]"
        else:
            rotation_text = str(rotation)
        self._view.set_frame_info(rotation_text, str(field_map.metadata.get('reference_point', 'N/A')))

        figure = self._figure_factory.create_figure(
            field_map.grids, list(field_map.extent), field_map.metadata, f"{self._acquisition_name} : {self._step_name}"
        )
        self._view.show_figure(figure)
        logger.info(
            "plot.drawn scan=%s step=%s source=%s rotation_angles_deg=%s elapsed_ms=%.1f",
            self._acquisition_name, self._step_name, source, rotation_text, (time.time() - start) * 1000,
        )
