#!/usr/bin/env python3
"""
Example usage of the data processing pipeline.
Demonstrates how to process scan data from CSV to final HDF5.
"""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from processing import ProcessingPipeline


def main():
    """Example pipeline execution."""
    
    # Paths
    project_root = Path(__file__).parent.parent.parent
    scan_dir = project_root / "data_repository" / "scans"
    output_dir = project_root / "data_repository" / "processed"
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
