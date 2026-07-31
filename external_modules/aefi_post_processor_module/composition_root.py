"""
Post-Processor Composition Root
Orchestrates the full workflow:
1. Scan the configured export directory (see `_export_output_directory`) for
   per-acquisition subfolders (`<timestamp>_stepScan_<name>/`), each holding
   the device's `*_aefi.csv`.
2. For each subfolder, check if its `.h5` (written alongside the CSV) is
   missing or outdated.
3. Run ProcessingPipeline on missing/outdated items.
4. Launch Visualization App on the export directory.
"""

import json
import sys
import argparse
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

from aefi_post_processor_module.processing.processing_pipeline import ProcessingPipeline
from aefi_post_processor_module.visualisation.model import VisualisationModel
from aefi_post_processor_module.visualisation.view import VisualisationView
from aefi_post_processor_module.visualisation.presenter import VisualisationPresenter

def sync_scans(raw_dir: Path, force: bool = False):
    """
    Run pipeline on missing/outdated scans.

    Each scan lives in its own acquisition subfolder (`<raw_dir>/<timestamp>_stepScan_<name>/`);
    the device CSV is found via `<subfolder>/*_aefi.csv` and the processed `.h5`
    is written into that same subfolder.
    """
    print(f"Syncing scans in {raw_dir}...")

    if not raw_dir.exists():
        print(f"Error: Raw directory not found: {raw_dir}")
        return

    csv_files = sorted(raw_dir.glob("*_stepScan_*/*_aefi.csv"))

    files_processed_count = 0

    for csv_path in csv_files:
        scan_name = csv_path.parent.name
        expected_output = csv_path.parent / f"{scan_name}.h5"
        
        # Check if up to date
        if expected_output.exists() and not force:
            if csv_path.stat().st_mtime < expected_output.stat().st_mtime:
                continue
            else:
                print(f"Updating {scan_name} (Source newer)...")
        else:
             print(f"Processing new scan: {scan_name}...")

        print(f"Running pipeline for {scan_name}...")
        try:
            # Instantiate pipeline for this specific file
            with ProcessingPipeline(output_path=expected_output) as pipeline:
                pipeline.run_full_pipeline(
                    csv_path, 
                    # specific angles requested by user
                    rotation_angles=(35.26, -45.00, -7.20),
                    reference_point=(0, 0)
                )
            
            files_processed_count += 1
            print(f"Successfully processed {scan_name}")
            
        except Exception as e:
            print(f"Failed to process {scan_name}: {e}")

    print(f"Sync complete. Processed {files_processed_count} new scans.")

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

    if args.repo_path is not None:
        raw_dir = args.repo_path
    else:
        raw_dir = _export_output_directory()

        # 1. Sync
        sync_scans(raw_dir, force=args.force)

    # 2. Launch Visualization
    print("Launching Visualization App...")
    app = QApplication(sys.argv)
    app.setApplicationName("AEFI Visualisation")

    # Point model to the export directory (recurses into acquisition subfolders)
    model = VisualisationModel(raw_dir)
    view = VisualisationView()
    presenter = VisualisationPresenter(view, model)
    
    view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
