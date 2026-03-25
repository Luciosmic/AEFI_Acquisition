"""
Post-Processor Composition Root
Orchestrates the full workflow:
1. Scan '.aefi_acquisition/scans/raw_data' for raw CSVs.
2. Compare with '.aefi_acquisition/scans/processed_data' to identify missing/outdated items.
3. Run ProcessingPipeline on missing items.
4. Launch Visualization App on the processed directory.
"""

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

from post_processor_module.processing.processing_pipeline import ProcessingPipeline
from post_processor_module.visualisation.model import VisualisationModel
from post_processor_module.visualisation.view import VisualisationView
from post_processor_module.visualisation.presenter import VisualisationPresenter

def sync_scans(raw_dir: Path, processed_dir: Path, force: bool = False):
    """
    Compare raw and processed directories. Run pipeline on missing/outdated files.
    """
    print(f"Syncing scans from {raw_dir} to {processed_dir}...")
    
    if not raw_dir.exists():
        print(f"Error: Raw directory not found: {raw_dir}")
        return

    processed_dir.mkdir(parents=True, exist_ok=True)
    
    csv_files = sorted(raw_dir.glob("*.csv"))
    
    files_processed_count = 0
    
    for csv_path in csv_files:
        scan_name = csv_path.stem
        expected_output = processed_dir / f"{scan_name}.h5"
        
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
    args = parser.parse_args()

    raw_dir = project_root / ".aefi_acquisition" / "scans" / "raw_data"
    processed_dir = project_root / ".aefi_acquisition" / "scans" / "processed_data"
    
    # 1. Sync
    sync_scans(raw_dir, processed_dir, force=args.force)
    
    # 2. Launch Visualization
    print("Launching Visualization App...")
    app = QApplication(sys.argv)
    app.setApplicationName("AEFI Visualisation")
    
    # Point model to the processed directory
    model = VisualisationModel(processed_dir)
    view = VisualisationView()
    presenter = VisualisationPresenter(view, model)
    
    view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
