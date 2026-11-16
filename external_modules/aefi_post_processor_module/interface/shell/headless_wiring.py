"""
headless_wiring - Builds the post-processing service with its real adapters, without Qt (see headless_wiring_intention.md).
"""

from typing import Tuple

from ...application.post_processing_service.i_api_post_processing_service import IApiPostProcessingService
from ...application.post_processing_service.post_processing_service import PostProcessingService
from ...application.post_processing_service.ports.i_step_writer import IStepWriter
from ...infrastructure.csv_scan_reader.csv_scan_reader import CsvScanReader
from ...infrastructure.hdf5_step_writer.hdf5_step_writer import Hdf5StepWriter


def build_post_processing_service(acquisition_file: str) -> Tuple[IApiPostProcessingService, IStepWriter]:
    """The service wired to the real reader and to a writer bound to the steps file of the acquisition, and that writer."""
    step_writer = Hdf5StepWriter(acquisition_file)
    return PostProcessingService(CsvScanReader(), step_writer), step_writer
