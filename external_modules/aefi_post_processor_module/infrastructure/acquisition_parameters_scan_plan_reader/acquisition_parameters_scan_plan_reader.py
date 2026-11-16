"""
AcquisitionParametersScanPlanReader - The planned grid of a scan, from the acquisition parameters file
the acquisition writes next to it (see acquisition_parameters_scan_plan_reader_intention.md).
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from ...application.post_processing_service.ports.i_scan_plan_reader import IScanPlanReader
from ...domain.processing.planned_scan_grid.planned_scan_grid import PlannedAxis, PlannedScanGrid

logger = logging.getLogger(__name__)

# Export names of the acquisition: <acquisition>_aefi.csv and <acquisition>_acquisition-parameters.json, side by side.
CSV_SUFFIX = '_aefi.csv'
PARAMETERS_SUFFIX = '_acquisition-parameters.json'
# Unit of the scan coordinates in the CSV.
COORDINATE_UNIT = 'mm'


def parameters_path_of(csv_path: str) -> Optional[Path]:
    """The acquisition parameters file next to an exported scan CSV, or None for a CSV the acquisition did not name."""
    path = Path(csv_path)
    if not path.name.endswith(CSV_SUFFIX):
        return None
    return path.with_name(path.name[: -len(CSV_SUFFIX)] + PARAMETERS_SUFFIX)


def _axis(zone: Dict[str, Any], grid: Dict[str, Any], axis: str) -> PlannedAxis:
    minimum, maximum = zone[f'{axis}_min'], zone[f'{axis}_max']
    for bound in (minimum, maximum):
        if bound.get('unit') != COORDINATE_UNIT:
            raise ValueError(f"{axis} bound in {bound.get('unit')!r}, expected {COORDINATE_UNIT!r}")
    return PlannedAxis(
        minimum=float(minimum['value']), maximum=float(maximum['value']), points=int(grid[f'{axis}_nb_points'])
    )


class AcquisitionParametersScanPlanReader(IScanPlanReader):
    def planned_grid(self, csv_path: str) -> Optional[PlannedScanGrid]:
        parameters_path = parameters_path_of(csv_path)
        if parameters_path is None:
            logger.info("scan_plan.unknown csv=%s reason=not an acquisition export name (*%s)", csv_path, CSV_SUFFIX)
            return None
        if not parameters_path.is_file():
            logger.info("scan_plan.unknown csv=%s reason=no acquisition parameters file parameters=%s", csv_path, parameters_path)
            return None
        try:
            description = json.loads(parameters_path.read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
            logger.warning("scan_plan.unreadable parameters=%s error_type=%s error=%s", parameters_path, type(e).__name__, e)
            return None
        try:
            step_scan = description['procedure']['step_scan']
            zone, grid = step_scan['zone'], step_scan['grid']
            plan = PlannedScanGrid(x=_axis(zone, grid, 'x'), y=_axis(zone, grid, 'y'))
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            schema = description.get('schema') if isinstance(description, dict) else None
            logger.warning(
                "scan_plan.incomplete parameters=%s schema=%s error_type=%s error=%s",
                parameters_path, schema, type(e).__name__, e,
            )
            return None
        logger.info(
            "scan_plan.read parameters=%s x=[%s, %s] x_points=%s y=[%s, %s] y_points=%s",
            parameters_path, plan.x.minimum, plan.x.maximum, plan.x.points, plan.y.minimum, plan.y.maximum, plan.y.points,
        )
        return plan
