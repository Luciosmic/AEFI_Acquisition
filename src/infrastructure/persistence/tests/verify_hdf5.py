"""
Demonstration script to verify HDF5 file creation.
This script uses the HDF5AcquisitionRepository to save a sample file.
"""
from pathlib import Path
from datetime import datetime
import shutil
import sys
import os

from infrastructure.persistence.hdf5_acquisition_repository import HDF5AcquisitionRepository
from domain.models.aefi_device.value_objects.acquisition.acquisition_sample import AcquisitionSample

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def demo_hdf5_creation():
    # Setup
    # Create demo_data in the same directory as this script
    demo_dir = Path(__file__).parent / "demo_data"
    if demo_dir.exists():
        shutil.rmtree(demo_dir)
    
    print(f"Creating repository in {demo_dir}...")
    repo = HDF5AcquisitionRepository(base_path=str(demo_dir))
    
    # Create data
    scan_id = "demo_scan_001"
    samples = [
        AcquisitionSample(
            timestamp=datetime.now(),
            voltage_x_in_phase=1.0 * i, voltage_x_quadrature=0.1 * i,
            voltage_y_in_phase=2.0 * i, voltage_y_quadrature=0.2 * i,
            voltage_z_in_phase=3.0 * i, voltage_z_quadrature=0.3 * i
        )
        for i in range(5)
    ]
    
    # Save
    print(f"Saving {len(samples)} samples for scan {scan_id}...")
    repo.save(scan_id, samples)
    
    # Verify file existence
    expected_file = demo_dir / f"scan_{scan_id}.h5"
    if expected_file.exists():
        print(f"SUCCESS: File created at {expected_file}")
        print(f"File size: {expected_file.stat().st_size} bytes")
        
        # Verify content
        retrieved = repo.find_by_scan(scan_id)
        print(f"Verified content: Retrieved {len(retrieved)} samples.")
    else:
        print(f"FAILURE: File not found at {expected_file}")

if __name__ == "__main__":
    demo_hdf5_creation()
