"""
Field map service — the stored steps of an acquisition, as maps (see field_map_service_intention.md).
"""

import json
import logging
from typing import Any, Dict, List, Tuple

from ...domain.processing.grid_builder.grid_builder import VOLTAGE_CHANNELS
from ...domain.processing.processing_steps.processing_steps import STEP_NAMES
from .dtos.field_map_dto import FieldMapDTO
from .dtos.load_step_dto import LoadStepDTO
from .dtos.steps_request_dto import StepsRequestDTO
from .i_api_field_map_service import IApiFieldMapService
from .ports.i_step_reader import IStepReader

logger = logging.getLogger(__name__)

_DEFAULT_EXTENT = [0, 1, 0, 1]


def _processing_order(names: List[str]) -> Tuple[str, ...]:
    known = [name for name in STEP_NAMES if name in names]
    others = sorted(name for name in names if name not in STEP_NAMES)
    return tuple(known + others)


def _decoded(value: Any) -> Any:
    """A list stored as a JSON string comes back as a list; anything else is left as it is."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


class FieldMapService(IApiFieldMapService):
    def __init__(self, step_reader: IStepReader):
        self._step_reader = step_reader

    def list_steps(self, request: StepsRequestDTO) -> Tuple[str, ...]:
        return _processing_order(self._step_reader.list_steps(request.acquisition_file))

    def load_step(self, request: LoadStepDTO) -> FieldMapDTO:
        stored = self._step_reader.read_step(request.acquisition_file, request.step_name)
        data, metadata = stored.data, stored.metadata
        channels = _decoded(metadata.get('channel_names'))
        if not channels or not isinstance(channels, list) or len(channels) != data.shape[2]:
            channels = list(VOLTAGE_CHANNELS[:data.shape[2]])
            logger.warning(
                "step.channel_names_defaulted path=%s step=%s channels=%s",
                request.acquisition_file, request.step_name, channels,
            )
        grids: Dict[str, Any] = {name: data[:, :, i] for i, name in enumerate(channels) if i < data.shape[2]}

        extent = _decoded(metadata.get('extent', _DEFAULT_EXTENT))
        if isinstance(extent, str):
            logger.warning(
                "step.extent_unreadable path=%s step=%s extent=%r", request.acquisition_file, request.step_name, extent
            )
            extent = _DEFAULT_EXTENT
        left, right, bottom, top = (float(v) for v in extent)
        return FieldMapDTO(step_name=request.step_name, grids=grids, extent=(left, right, bottom, top), metadata=dict(metadata))
