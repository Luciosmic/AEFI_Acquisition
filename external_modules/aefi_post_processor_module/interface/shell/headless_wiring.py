"""
headless_wiring - Builds the post-processing service with its real adapters, without Qt (see headless_wiring_intention.md).
"""

from typing import Tuple

from ...application.acquisition_catalog_service.acquisition_catalog_service import AcquisitionCatalogService
from ...application.acquisition_catalog_service.i_api_acquisition_catalog_service import IApiAcquisitionCatalogService
from ...application.field_map_service.field_map_service import FieldMapService
from ...application.field_map_service.i_api_field_map_service import IApiFieldMapService
from ...application.post_processing_service.i_api_post_processing_service import IApiPostProcessingService
from ...application.post_processing_service.post_processing_service import PostProcessingService
from ...application.post_processing_service.ports.i_step_writer import IStepWriter
from ...infrastructure.acquisition_parameters_scan_plan_reader.acquisition_parameters_scan_plan_reader import (
    AcquisitionParametersScanPlanReader,
)
from ...infrastructure.csv_scan_reader.csv_scan_reader import CsvScanReader
from ...infrastructure.export_folder_repository.export_folder_repository import ExportFolderRepository
from ...infrastructure.hdf5_step_reader.hdf5_step_reader import Hdf5StepReader
from ...infrastructure.hdf5_step_writer.hdf5_step_writer import Hdf5StepWriter


def build_post_processing_service(acquisition_file: str) -> Tuple[IApiPostProcessingService, IStepWriter]:
    """The service wired to the real readers (scan points, planned grid) and to a writer bound to the steps file of the acquisition, and that writer."""
    step_writer = Hdf5StepWriter(acquisition_file)
    return PostProcessingService(CsvScanReader(), step_writer, AcquisitionParametersScanPlanReader()), step_writer


def build_acquisition_catalog_service() -> IApiAcquisitionCatalogService:
    """The catalog wired to the export folder repository. One instance per session: it remembers the failures."""
    return AcquisitionCatalogService(ExportFolderRepository())


def build_field_map_service() -> IApiFieldMapService:
    """The field map service wired to the HDF5 step reader."""
    return FieldMapService(Hdf5StepReader())
