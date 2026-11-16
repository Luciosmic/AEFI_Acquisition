"""
ProcessingPipeline - Raccord vers le service de traitement.

# ponytail: raccord temporaire. L'adaptateur de l'acquisition (src/infrastructure/aefi_post_processor_port) importe encore
# ce nom, et son test le patche. Le raccord garde la signature d'origine et délègue à PostProcessingService, câblé sans Qt.
# Retrait : tranche 6, quand l'adaptateur appelle le service directement.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple

from aefi_post_processor_module.application.post_processing_service.dtos.process_scan_dto import ProcessScanDTO
from aefi_post_processor_module.domain.processing.processing_steps.processing_steps import ProcessingParameters
from aefi_post_processor_module.interface.shell.headless_wiring import build_post_processing_service


class ProcessingPipeline:
    """Same entry point as before the layers: ProcessingPipeline(output_path).run_full_pipeline(csv_path, ...)."""

    def __init__(
        self,
        output_path: Path,
        border_width: int = 1,
        interpolation_method: str = 'cubic',
        target_grid_size: Optional[int] = None,
    ):
        self.output_path = Path(output_path)
        self._border_width = border_width
        self._interpolation_method = interpolation_method
        self._target_grid_size = target_grid_size
        self._service, self.data_handler = build_post_processing_service(str(output_path))

    def run_full_pipeline(
        self,
        csv_path: Path,
        rotation_angles: Optional[Tuple[float, float, float]] = None,
        reference_point: Tuple[int, int] = (0, 0),
        skip_interpolation: bool = False,
    ) -> Dict:
        """Process one scan. Rotation angles are degrees (theta_x, theta_y, theta_z) of the mounting rotation P."""
        request = ProcessScanDTO(
            csv_path=str(csv_path),
            acquisition_file=str(self.output_path),
            parameters=ProcessingParameters(
                border_width=self._border_width,
                interpolation_method=self._interpolation_method,
                target_grid_size=self._target_grid_size,
                reference_point=reference_point,
                rotation_angles=rotation_angles,
            ),
            skip_interpolation=skip_interpolation,
        )
        summary = self._service.process_scan(request)
        return {
            'steps_completed': list(summary.steps_completed),
            'errors': list(summary.errors),
            'success': summary.success,
            'output_file': summary.output_file,
            'processing_history': list(summary.processing_history),
        }

    def close(self):
        self.data_handler.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
