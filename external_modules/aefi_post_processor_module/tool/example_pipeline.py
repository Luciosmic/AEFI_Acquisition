#!/usr/bin/env python3
"""
Example usage of the data processing pipeline.
Demonstrates how to process scan data from CSV to final HDF5.
"""

import sys
from pathlib import Path

# tool/ est dans le module : external_modules/ doit être sur sys.path pour importer aefi_post_processor_module.
MODULE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_DIR.parent))

from aefi_post_processor_module.processing import ProcessingPipeline


def main():
    """Example pipeline execution."""
    
    # Paths
    project_root = MODULE_DIR.parent.parent
    scan_dir = project_root / ".aefi_acquisition" / "scans" / "raw_data"
    output_dir = project_root / ".aefi_acquisition" / "scans" / "processed_data"
    output_dir.mkdir(exist_ok=True)
    
    # Find latest CSV file
    csv_files = sorted(scan_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not csv_files:
        print("No CSV files found in scan directory")
        return
    
    csv_file = csv_files[0]
    print(f"Processing: {csv_file.name}")
    
    # Output HDF5 file
    output_file = output_dir / f"{csv_file.stem}_processed.h5"
    
    # Create pipeline
    with ProcessingPipeline(output_file) as pipeline:
        # Run full pipeline
        # Rotation angles: example values (adjust as needed)
        rotation_angles = (0.0, 0.0, 0.0)  # (theta_x, theta_y, theta_z) in degrees
        
        summary = pipeline.run_full_pipeline(
            csv_file,
            rotation_angles=rotation_angles,
            skip_interpolation=False
        )
        
        print("\n" + "="*50)
        print("PIPELINE SUMMARY")
        print("="*50)
        print(f"Success: {summary['success']}")
        print(f"Steps completed: {', '.join(summary['steps_completed'])}")
        print(f"Output file: {summary['output_file']}")
        print("\nProcessing history:")
        for step in summary['processing_history']:
            print(f"  - {step}")
        
        if summary['errors']:
            print("\nErrors:")
            for error in summary['errors']:
                print(f"  - {error}")


if __name__ == "__main__":
    main()
