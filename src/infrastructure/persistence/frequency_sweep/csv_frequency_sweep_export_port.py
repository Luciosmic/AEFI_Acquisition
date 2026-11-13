"""
CSV Frequency Sweep Export Port

See csv_frequency_sweep_export_port_intention.md.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Sequence, Tuple

from application.services.frequency_sweep_service.dtos.acquisition_parameters_dtos import (
    FrequencySweepAcquisitionParametersDTO,
)
from application.services.frequency_sweep_service.dtos.frequency_sweep_dtos import (
    VALUE_CHANNELS,
    FrequencySweepResultDTO,
    FrequencySweepSampleDTO,
)
from application.services.frequency_sweep_service.ports.i_frequency_sweep_export_port import IFrequencySweepExportPort
from application.shared.acquisition_parameters.acquisition_conditions_dtos import ExportedFileDTO
from domain.shared_kernel.operation_result import OperationResult
from infrastructure.persistence.acquisition_parameters.acquisition_parameters_file import describe_file, write_document
from infrastructure.persistence.frequency_sweep.acquisition_parameters_v1_serializer import (
    ACQUISITION_PARAMETERS_FILE_NAME,
    serialize_acquisition_parameters_v1,
)

logger = logging.getLogger(__name__)

RESPONSE_FILE_NAME = "frequency_response.csv"
SAMPLES_FILE_NAME = "samples.csv"
RESPONSE_COLUMNS = (
    ["frequency_index", "frequency_hz", "samples_count", "reference_phase_offset_deg"]
    + [f"{c}_v" for c in VALUE_CHANNELS]
    + [f"std_{c}_v" for c in VALUE_CHANNELS]
)
SAMPLES_COLUMNS = ["frequency_hz", "sample_index", "timestamp"] + [f"{c}_v" for c in VALUE_CHANNELS]


class CsvFrequencySweepExportPort(IFrequencySweepExportPort):
    def __init__(self, base_output_dir: Optional[Path] = None, clock: Callable[[], datetime] = datetime.now) -> None:
        self._base = base_output_dir or Path.home() / "Desktop" / "AEFI_Acquisition_Exports"
        self._clock = clock

    def open_export(self, role: str, table_height_mm: float) -> OperationResult[str, str]:
        stamp = self._clock().strftime("%Y-%m-%d_%H%M%S")
        folder = self._base / f"{stamp}_frequencySweep_{role}_table{table_height_mm:g}mm"
        try:
            folder.mkdir(parents=True)
        except OSError as error:
            logger.warning("CsvFrequencySweepExportPort: cannot create %s: %s", folder, error)
            return OperationResult.fail(f"export impossible ({folder}) : {error}")
        logger.info("CsvFrequencySweepExportPort: export folder %s created", folder)
        return OperationResult.ok(str(folder))

    def export(
        self, location: str, result: FrequencySweepResultDTO, samples: Sequence[FrequencySweepSampleDTO]
    ) -> OperationResult[Tuple[ExportedFileDTO, ...], str]:
        folder = Path(location)
        try:
            self._write_response(folder / RESPONSE_FILE_NAME, result)
            self._write_samples(folder / SAMPLES_FILE_NAME, samples)
            files = tuple(describe_file(folder / name, "CSV") for name in (RESPONSE_FILE_NAME, SAMPLES_FILE_NAME))
        except OSError as error:
            logger.warning("CsvFrequencySweepExportPort: export to %s failed: %s", folder, error)
            return OperationResult.fail(f"export impossible ({folder}) : {error}")
        logger.info(
            "CsvFrequencySweepExportPort: sweep_id=%s exported %d frequencies, %d samples to %s",
            result.sweep_id, len(result.points), len(samples), folder,
        )
        return OperationResult.ok(files)

    def write_acquisition_parameters(
        self, location: str, parameters: FrequencySweepAcquisitionParametersDTO
    ) -> OperationResult[None, str]:
        path = Path(location) / ACQUISITION_PARAMETERS_FILE_NAME
        document = serialize_acquisition_parameters_v1(parameters, generated_at=self._clock().astimezone())
        try:
            write_document(path, document)
        except (OSError, TypeError, ValueError) as error:
            logger.warning("CsvFrequencySweepExportPort: cannot write %s: %s", path, error)
            return OperationResult.fail(f"paramètres d'acquisition non écrits ({path}) : {error}")
        logger.info(
            "CsvFrequencySweepExportPort: %s written activity_id=%s status=%s warnings=%d",
            path, parameters.activity.activity_id, parameters.activity.status, len(document["warnings"]),
        )
        return OperationResult.ok(None)

    @staticmethod
    def _write_response(path: Path, result: FrequencySweepResultDTO) -> None:
        with open(path, "w", newline="", encoding="utf-8") as f:
            for key, value in (
                ("sweep_id", result.sweep_id),
                ("role", result.role),
                ("table_height_mm", result.table_height_mm),
                ("status", result.status),
            ):
                f.write(f"# {key},{value}\n")
            writer = csv.writer(f)
            writer.writerow(RESPONSE_COLUMNS)
            for p in result.points:
                phase = "" if p.reference_phase_offset_deg is None else p.reference_phase_offset_deg
                writer.writerow([p.frequency_index, p.frequency_hz, p.samples_count, phase] + list(p.mean_v) + list(p.std_v))

    @staticmethod
    def _write_samples(path: Path, samples: Sequence[FrequencySweepSampleDTO]) -> None:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(SAMPLES_COLUMNS)
            for s in samples:
                # ISO 8601 with offset (naive host timestamps are local time).
                writer.writerow([s.frequency_hz, s.sample_index, s.timestamp.astimezone().isoformat()] + list(s.values_v))
