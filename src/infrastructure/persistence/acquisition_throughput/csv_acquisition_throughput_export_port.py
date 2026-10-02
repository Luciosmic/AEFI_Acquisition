"""
CSV Acquisition Throughput Export Port

See csv_acquisition_throughput_export_port_intention.md.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Sequence, Tuple

from application.shared.acquisition_parameters.acquisition_conditions_dtos import (
    ExportedFileDTO,
)
from application.services.acquisition_throughput_characterization_service.dtos.acquisition_parameters_dtos import (
    AcquisitionParametersDTO,
)
from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    VALUE_CHANNELS,
    AcquisitionThroughputCharacterizationDTO,
    AcquisitionThroughputSampleDTO,
)
from application.services.acquisition_throughput_characterization_service.ports.i_acquisition_throughput_export_port import (
    IAcquisitionThroughputExportPort,
)
from domain.shared_kernel.operation_result import OperationResult
from infrastructure.persistence.acquisition_parameters.acquisition_parameters_file import describe_file, write_document
from infrastructure.persistence.acquisition_throughput.acquisition_parameters_v1_serializer import (
    ACQUISITION_PARAMETERS_FILE_NAME,
    serialize_acquisition_parameters_v1,
)

logger = logging.getLogger(__name__)

SUMMARY_FILE_NAME = "summary.csv"
SAMPLES_FILE_NAME = "samples.csv"
SUMMARY_COLUMNS = (
    ["n_avg", "sample_period_s", "sample_rate_per_s", "adc_conversions_per_s", "noise_rms_v", "noise_in_one_second_v"]
    + [f"noise_v_rms_{c}" for c in VALUE_CHANNELS]
)
SAMPLES_COLUMNS = ["n_avg", "sample_index", "timestamp"] + [f"{c}_v" for c in VALUE_CHANNELS]


class CsvAcquisitionThroughputExportPort(IAcquisitionThroughputExportPort):
    def __init__(self, base_output_dir: Optional[Path] = None, clock: Callable[[], datetime] = datetime.now) -> None:
        self._base = base_output_dir or Path.home() / "Desktop" / "AEFI_Acquisition_Exports"
        self._clock = clock

    def open_export(self, oversampling_ratio: int, excitation_label: str) -> OperationResult[str, str]:
        stamp = self._clock().strftime("%Y-%m-%d_%H%M%S")
        folder = self._base / f"{stamp}_mcuThroughput_osr{oversampling_ratio}_excitation-{excitation_label}"
        try:
            folder.mkdir(parents=True)
        except OSError as error:
            logger.warning("CsvAcquisitionThroughputExportPort: cannot create %s: %s", folder, error)
            return OperationResult.fail(f"export impossible ({folder}) : {error}")
        logger.info("CsvAcquisitionThroughputExportPort: export folder %s created", folder)
        return OperationResult.ok(str(folder))

    def export(
        self,
        location: str,
        result: AcquisitionThroughputCharacterizationDTO,
        samples: Sequence[AcquisitionThroughputSampleDTO],
    ) -> OperationResult[Tuple[ExportedFileDTO, ...], str]:
        folder = Path(location)
        try:
            self._write_summary(folder / SUMMARY_FILE_NAME, result)
            self._write_samples(folder / SAMPLES_FILE_NAME, samples)
            files = tuple(describe_file(folder / name, "CSV") for name in (SUMMARY_FILE_NAME, SAMPLES_FILE_NAME))
        except OSError as error:
            logger.warning("CsvAcquisitionThroughputExportPort: export to %s failed: %s", folder, error)
            return OperationResult.fail(f"export impossible ({folder}) : {error}")
        logger.info("CsvAcquisitionThroughputExportPort: exported %d samples to %s", len(samples), folder)
        return OperationResult.ok(files)

    def write_acquisition_parameters(
        self, location: str, parameters: AcquisitionParametersDTO
    ) -> OperationResult[None, str]:
        path = Path(location) / ACQUISITION_PARAMETERS_FILE_NAME
        document = serialize_acquisition_parameters_v1(parameters, generated_at=self._clock())
        try:
            write_document(path, document)
        except (OSError, TypeError, ValueError) as error:
            logger.warning("CsvAcquisitionThroughputExportPort: cannot write %s: %s", path, error)
            return OperationResult.fail(f"paramètres d'acquisition non écrits ({path}) : {error}")
        logger.info(
            "CsvAcquisitionThroughputExportPort: %s written activity_id=%s status=%s warnings=%d",
            path, parameters.activity.activity_id, parameters.activity.status, len(document["warnings"]),
        )
        return OperationResult.ok(None)

    @staticmethod
    def _write_summary(path: Path, result: AcquisitionThroughputCharacterizationDTO) -> None:
        with open(path, "w", newline="", encoding="utf-8") as f:
            for key, value in (
                ("oversampling_ratio", result.oversampling_ratio),
                ("excitation", result.excitation),
                ("overhead_s", result.overhead_s),
                ("adc_output_rate_hz", result.adc_output_rate_hz),
                ("fit_max_relative_residual", result.fit_max_relative_residual),
                ("recommended_n_avg", result.recommended_n_avg),
                ("noise_relative_uncertainty", result.noise_relative_uncertainty),
            ):
                f.write(f"# {key},{value}\n")
            writer = csv.writer(f)
            writer.writerow(SUMMARY_COLUMNS)
            for p in result.points:
                writer.writerow(
                    [p.n_avg, p.sample_period_s, p.sample_rate_per_s, p.adc_conversions_per_s, p.noise_rms_v,
                     p.noise_in_one_second_v]
                    + list(p.noise_v_rms)
                )

    @staticmethod
    def _write_samples(path: Path, samples: Sequence[AcquisitionThroughputSampleDTO]) -> None:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(SAMPLES_COLUMNS)
            for s in samples:
                # ISO 8601 with offset (naive host timestamps are local time).
                writer.writerow([s.n_avg, s.sample_index, s.timestamp.astimezone().isoformat()] + list(s.values_v))

