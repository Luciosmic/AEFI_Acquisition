"""
Post-Processor Composition Root
Orchestrates the full workflow:
1. Scan the configured export directory (see `_export_output_directory`) for
   per-acquisition subfolders (`<timestamp>_<stepScan|flyScan>_<name>/`), each holding
   the device's `*_aefi.csv`.
2. For each subfolder, check if its `.h5` (written alongside the CSV) is
   missing or outdated.
3. Run ProcessingPipeline on missing/outdated items.
4. Launch Visualization App on the export directory.
"""

import json
import logging
import sys
import time
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from PySide6.QtWidgets import QApplication

# Repo root (.aefi_acquisition, etc.) and external_modules (package imports)
_module_dir = Path(__file__).resolve().parent
_external_modules = _module_dir.parent
project_root = _external_modules.parent
for p in (_external_modules, project_root):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

logger = logging.getLogger(__name__)

_LOG_FILE = project_root / ".aefi_acquisition" / "logs" / "post_processor.log"
_EXPORT_CONFIG_PATH = project_root / ".aefi_acquisition" / "configs" / "export_default_config.json"
_DEFAULT_EXPORT_DIR = Path.home() / "Desktop" / "AEFI_Acquisition_Exports"


def _export_output_directory() -> Path:
    """Read `output_directory` from the export config; fall back to the app's own default."""
    try:
        config = json.loads(_EXPORT_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _DEFAULT_EXPORT_DIR

    directory = config.get("output_directory") or ""
    return Path(directory) if directory else _DEFAULT_EXPORT_DIR


_DEVICE_CONFIG_PATH = project_root / "config_templates" / "aefi_device_config.json"


def _ideal_rotation_angles() -> tuple:
    """Ideal sources -> sensor angles (theta_x, theta_y, theta_z) from the device config template."""
    # ponytail: batch reprocessing uses the IDEAL angles, not the sensor calibration active when the
    # scan was acquired (the in-app export uses the active one). Upgrade: read the angles stored with each scan.
    rotation = json.loads(_DEVICE_CONFIG_PATH.read_text(encoding="utf-8"))["sensor"]["calibration"]["sources_to_sensor_rotation"]
    return (float(rotation["theta_x"]), float(rotation["theta_y"]), float(rotation["theta_z"]))

from aefi_post_processor_module.logging_setup import configure_logging
from aefi_post_processor_module.processing.processing_pipeline import ProcessingPipeline
from aefi_post_processor_module.visualisation.model import VisualisationModel
from aefi_post_processor_module.visualisation.view import VisualisationView
from aefi_post_processor_module.visualisation.presenter import VisualisationPresenter

@dataclass
class SyncSummary:
    """Outcome of one batch sync, by acquisition folder name."""
    processed: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)


def sync_scans(raw_dir: Path, force: bool = False) -> SyncSummary:
    """
    Run pipeline on missing/outdated scans.

    Each scan lives in its own acquisition subfolder (`<raw_dir>/<timestamp>_<stepScan|flyScan>_<name>/`);
    the device CSV is found via `<subfolder>/*_aefi.csv` and the processed `.h5`
    is written into that same subfolder.
    """
    summary = SyncSummary()

    if not raw_dir.exists():
        logger.error("sync.aborted reason=raw_dir_not_found raw_dir=%s", raw_dir)
        return summary

    # Step scans (measurements) and fly scans (exploration maps): same files, same pipeline.
    csv_files = sorted(
        path for kind in ("stepScan", "flyScan") for path in raw_dir.glob(f"*_{kind}_*/*_aefi.csv")
    )
    logger.info("sync.started raw_dir=%s scans_found=%d force=%s", raw_dir, len(csv_files), force)

    for csv_path in csv_files:
        scan_name = csv_path.parent.name
        expected_output = csv_path.parent / f"{scan_name}.h5"

        if not expected_output.exists():
            reason = "new"
        elif force:
            reason = "forced"
        elif csv_path.stat().st_mtime >= expected_output.stat().st_mtime:
            reason = "source_newer"
        else:
            logger.debug("scan.up_to_date scan=%s action=none", scan_name)
            summary.skipped.append(scan_name)
            continue

        try:
            rotation_angles = _ideal_rotation_angles()
            logger.info(
                "scan.processing scan=%s reason=%s rotation_angles_deg=%s rotation_origin=ideal_template",
                scan_name, reason, rotation_angles,
            )
            started = time.monotonic()
            with ProcessingPipeline(output_path=expected_output) as pipeline:
                pipeline.run_full_pipeline(
                    csv_path,
                    rotation_angles=rotation_angles,
                    reference_point=(0, 0)
                )
            summary.processed.append(scan_name)
            logger.info("scan.processed scan=%s elapsed_s=%.1f", scan_name, time.monotonic() - started)

        except Exception as e:
            summary.failed.append(scan_name)
            logger.exception("scan.failed scan=%s error_type=%s error=%s", scan_name, type(e).__name__, e)

    outcome_level = logging.WARNING if summary.failed else logging.INFO
    logger.log(
        outcome_level,
        "sync.finished processed=%d skipped=%d failed=%d failed_scans=%s",
        len(summary.processed), len(summary.skipped), len(summary.failed), summary.failed,
    )
    return summary

def main():
    parser = argparse.ArgumentParser(description="AEFI Post-Processor Composition Root")
    parser.add_argument("--force", action="store_true", help="Force re-processing of all scans")
    parser.add_argument(
        "--repo-path",
        type=Path,
        default=None,
        help="Open the visualizer directly on this folder, skipping the sync step "
             "(e.g. an export directory already fully post-processed).",
    )
    args = parser.parse_args()

    feedback = configure_logging(_LOG_FILE)

    if args.repo_path is not None:
        raw_dir = args.repo_path
        logger.info("sync.skipped reason=repo_path_given repo=%s", raw_dir)
    else:
        raw_dir = _export_output_directory()

        # 1. Sync
        sync_scans(raw_dir, force=args.force)

    # 2. Launch Visualization
    logger.info("visualisation.opening repo=%s", raw_dir)
    app = QApplication(sys.argv)
    app.setApplicationName("AEFI Visualisation")

    # Point model to the export directory (recurses into acquisition subfolders)
    model = VisualisationModel(raw_dir)
    view = VisualisationView()
    feedback.attach(view.append_feedback)
    presenter = VisualisationPresenter(view, model)

    view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
