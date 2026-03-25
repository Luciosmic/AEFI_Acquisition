"""
Run Synthetic Campaign
Executes the processing pipeline on the generated synthetic campaign.
Reads manifest.json to get scan parameters.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add project root to path to import modules
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from tools.post_processor_modules.processing.processing_pipeline import ProcessingPipeline

def get_latest_batch_dir(base_dir: Path) -> Path:
    batches = sorted([d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("batch_")])
    if not batches:
        raise FileNotFoundError(f"No batch directories found in {base_dir}")
    return batches[-1]

def run_campaign():
    base_dir = Path(__file__).parent / "synthetic_scans_data_repository"
    batch_dir = get_latest_batch_dir(base_dir)
    print(f"Running campaign on batch: {batch_dir.name}")
    
    manifest_path = batch_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        
    with open(manifest_path, 'r') as f:
        manifest = json.load(f) # type: Dict[str, Any]
        
    results = {}
    
    for scan_name, info in manifest.items():
        print(f"\nProcessing {scan_name}...")
        
        csv_path = Path(info['full_path'])
        rotation_angles = info.get('rotation_angles') # Can be None
        
        # Output HDF5 path (same directory as CSV)
        output_h5 = batch_dir / f"{scan_name}.h5"
        
        # Initialize pipeline
        # Using cubic interpolation and a standard grid size suitable for the synthetic 50x50 input
        # Let's upsample slightly to test interpolation, e.g. 100
        pipeline = ProcessingPipeline(
            output_path=output_h5,
            border_width=1,
            interpolation_method='cubic',
            target_grid_size=100
        )
        
        try:
            summary = pipeline.run_full_pipeline(
                csv_path=csv_path,
                rotation_angles=rotation_angles,
                skip_interpolation=False
            )
            print(f"Success: {scan_name}")
            results[scan_name] = "PASS"
        except Exception as e:
            print(f"FAILED: {scan_name} - {e}")
            results[scan_name] = f"FAIL: {str(e)}"
        finally:
            pipeline.close()

    print("\nCampaign Summary:")
    print(json.dumps(results, indent=2))
    
    # Save results
    with open(batch_dir / "processing_results.json", 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_campaign()
