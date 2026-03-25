"""
Generate Synthetic Campaign
Generates a batch of synthetic scans (CSV format) to cover processing pipeline test cases.
Produces a manifest.json describing the parameters for each scan.
"""

from pathlib import Path
import json
from datetime import datetime
import numpy as np
import pandas as pd
from synthetic_scan_generator import SyntheticScanGenerator

def generate_campaign():
    # Setup paths
    base_dir = Path(__file__).parent / "synthetic_scans_data_repository"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = base_dir / f"batch_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating synthetic campaign in: {output_dir}")
    
    # Initialize generator
    # Using 50x50 grid, 10mm range
    generator = SyntheticScanGenerator(grid_size=50, scan_range=10.0)
    
    manifest = {}
    
    # helper to save
    def save_scan(name, data, description, params=None):
        filename = f"{name}.csv"
        filepath = output_dir / filename
        df = generator.to_dataframe(data)
        df.to_csv(filepath, index=False)
        
        manifest_entry = {
            "filename": filename,
            "description": description,
            "full_path": str(filepath)
        }
        if params:
            manifest_entry.update(params)
        
        manifest[name] = manifest_entry
        print(f"Generated {filename}: {description}")

    # Case 1: Baseline
    # Perfect signal, no offsets, no rotation
    data_base = generator.generate_base_signal()
    save_scan("scan_001_baseline", data_base, "Baseline signal (clean)")
    
    # Case 2: Phase Offset
    # Apply phase offset (30, -45, 90 deg)
    # Pipeline should calibrate this to near zero
    phase_angles = (np.deg2rad(30), np.deg2rad(-45), np.deg2rad(90))
    data_phase = generator.add_phase_offset(data_base, phase_angles)
    save_scan("scan_002_phase_offset", data_phase, "Phase offsets: (30, -45, 90)")
    
    # Case 3: Primary Field Amplitude Subtraction
    # Apply DC offsets
    dc_offsets = np.array([1.0, 0.5, -1.0, 0.0, 2.0, -0.5])
    data_amp = generator.add_dc_offset(data_base, dc_offsets)
    save_scan("scan_003_dc_offset", data_amp, "DC offsets added")
    
    # Case 4: Frame Rotation
    # Apply 45 deg rotation around Z
    # We supply rotation angles in manifest for pipeline to use
    rot_angles = (0.0, 0.0, 45.0)
    data_rot = generator.rotate_frame(data_base, rot_angles)
    save_scan(
        "scan_004_rotation_z45", 
        data_rot, 
        "Rotated 45 deg Z", 
        params={"rotation_angles": rot_angles}
    )
    
    # Case 5: Combined
    # Phase + Amp + Rotation
    data_combined = generator.add_phase_offset(data_base, phase_angles)
    data_combined = generator.add_dc_offset(data_combined, dc_offsets)
    # Note: If we rotate AFTER adding phase/amp, the physics is slightly different depending on 
    # where the errors are introduced.
    # Usually phase offset is instrumental (rx), DC is instrumental (rx), rotation is physical sensor.
    # So we rotate the FIELD first, then add instrumental errors?
    # Or start with rotated field.
    # Simple approach: Start with base, rotate it (representing physical field), then add errors.
    
    data_comb_rot = generator.rotate_frame(data_base, rot_angles)
    data_comb_phase = generator.add_phase_offset(data_comb_rot, phase_angles)
    data_comb_final = generator.add_dc_offset(data_comb_phase, dc_offsets)
    
    save_scan(
        "scan_005_combined_rotated", 
        data_comb_final, 
        "Combined: Rot->Phase->Amp",
        params={"rotation_angles": rot_angles}
    )

    # Case 6: Combined (No Rotation)
    # Phase + Amp only
    data_comb_norot_phase = generator.add_phase_offset(data_base, phase_angles)
    data_comb_norot_final = generator.add_dc_offset(data_comb_norot_phase, dc_offsets)
    
    save_scan(
        "scan_006_combined",
        data_comb_norot_final,
        "Combined: Phase->Amp (No Rotation)"
    )

    # Case 7: Negative Reference (Testing Sign Preservation)
    # We create a signal where the reference point (0,0) has negative In-Phase components.
    # The calibrator should preserve this negative sign.
    data_neg = generator.generate_base_signal() * -1.0 # Invert everything
    # Add some phase offset to force rotation
    data_neg_phase = generator.add_phase_offset(data_neg, (np.deg2rad(10), np.deg2rad(10), np.deg2rad(10)))
    
    save_scan(
        "scan_007_negative_ref",
        data_neg_phase,
        "Negative Base Signal (Sign Preservation Test)"
    )

    # Save manifest
    with open(output_dir / "manifest.json", 'w') as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Campaign generation complete using batch {timestamp}")
    print(f"Manifest saved to {output_dir / 'manifest.json'}")

if __name__ == "__main__":
    generate_campaign()
