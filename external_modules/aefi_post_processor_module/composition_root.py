"""
Post-Processor Composition Root
Thin entry point: reads the arguments, settles the paths and the journal, builds the window of panels
(`interface/shell/shell_wiring.py`) on the export directory and runs it.

The launch computes nothing: the window opens on the list of acquisitions with the state of each, and the journal
says it. Processing starts from the "Traiter" button of the Acquisitions panel, or at launch with `--force`.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

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
_LAYOUT_FILE = Path.home() / ".aefi_post_processor_layout.dat"  # its own file: never the acquisition's layout
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
    """Ideal sources -> sensor angles (theta_x, theta_y, theta_z) from the device config template: the fallback angles."""
    # ponytail: these IDEAL angles are only the fallback, for an acquisition whose parameters file gives no usable
    # rotation (old export, convention refused): when it does, the angles the acquisition applied take precedence
    # (post_processing_service). Upgrade: none planned; the fallback is the documented behaviour without a description.
    rotation = json.loads(_DEVICE_CONFIG_PATH.read_text(encoding="utf-8"))["sensor"]["calibration"]["sources_to_sensor_rotation"]
    return (float(rotation["theta_x"]), float(rotation["theta_y"]), float(rotation["theta_z"]))

from aefi_post_processor_module.domain.processing.processing_steps.processing_steps import ProcessingParameters
from aefi_post_processor_module.infrastructure.logging.logging_setup import configure_logging
from aefi_post_processor_module.interface.shell.shell_wiring import build_shell


def _processing_parameters() -> ProcessingParameters:
    """Parameters of one processing: the default ones, with the ideal rotation angles of the device template."""
    return ProcessingParameters(rotation_angles=_ideal_rotation_angles(), reference_point=(0, 0))


def main():
    parser = argparse.ArgumentParser(description="AEFI Post-Processor Composition Root")
    parser.add_argument(
        "--force", action="store_true", help="Process every acquisition at launch, before the window shows."
    )
    parser.add_argument(
        "--repo-path",
        type=Path,
        default=None,
        help="Open the window on this export folder instead of the one of the export configuration.",
    )
    parser.add_argument("--log-file", type=Path, default=_LOG_FILE, help="Where this run writes its journal.")
    parser.add_argument(
        "--layout-file", type=Path, default=_LAYOUT_FILE, help="Where the layout of the panels is kept between runs."
    )
    args = parser.parse_args()

    feedback = configure_logging(args.log_file)
    raw_dir = args.repo_path if args.repo_path is not None else _export_output_directory()

    app = QApplication(sys.argv)
    app.setApplicationName("AEFI Post-Processor")
    shell = build_shell(
        feedback, str(args.log_file), str(args.layout_file), str(raw_dir), _processing_parameters, "ideal_template"
    )

    if args.force:
        shell.acquisitions_presenter.process_pending(force=True)
    else:
        shell.acquisitions_presenter.refresh()

    logger.info("window.opening repo=%s", raw_dir)
    shell.window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
