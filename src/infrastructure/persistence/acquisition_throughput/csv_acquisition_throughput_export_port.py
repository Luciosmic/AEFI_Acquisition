"""
CSV Acquisition Throughput Export Port

See csv_acquisition_throughput_export_port_intention.md.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    AcquisitionThroughputCharacterizationDTO,
    AcquisitionThroughputSampleDTO,
)
from application.services.acquisition_throughput_characterization_service.ports.i_acquisition_throughput_export_port import (
    IAcquisitionThroughputExportPort,
)
from domain.shared_kernel.operation_result import OperationResult

logger = logging.getLogger(__name__)

_CHANNELS = ("x_in_phase", "y_in_phase", "z_in_phase", "x_quadrature", "y_quadrature", "z_quadrature")


class CsvAcquisitionThroughputExportPort(IAcquisitionThroughputExportPort):
    def __init__(self, base_output_dir: Optional[Path] = None) -> None:
        self._base = base_output_dir or Path.home() / "Desktop" / "AEFI_Acquisition_Exports"

    def export(
        self,
        result: AcquisitionThroughputCharacterizationDTO,
        samples: Sequence[AcquisitionThroughputSampleDTO],
    ) -> OperationResult[str, str]:
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        folder = self._base / f"{stamp}_mcuThroughput_osr{result.oversampling_ratio}_excitation-{result.excitation}"
        try:
            folder.mkdir(parents=True)
            self._write_summary(folder / "summary.csv", result)
            self._write_samples(folder / "samples.csv", samples)
        except OSError as error:
            logger.warning("CsvAcquisitionThroughputExportPort: export to %s failed: %s", folder, error)
            return OperationResult.fail(f"export impossible ({folder}) : {error}")
        logger.info("CsvAcquisitionThroughputExportPort: exported %d samples to %s", len(samples), folder)
        return OperationResult.ok(str(folder))

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
            writer.writerow(
                ["n_avg", "sample_period_s", "sample_rate_per_s", "adc_conversions_per_s", "noise_rms_v",
                 "noise_in_one_second_v"]
                + [f"noise_v_rms_{c}" for c in _CHANNELS]
            )
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
            writer.writerow(["n_avg", "sample_index", "timestamp"] + [f"{c}_v" for c in _CHANNELS])
            for s in samples:
                writer.writerow([s.n_avg, s.sample_index, s.timestamp.isoformat()] + list(s.values_v))
