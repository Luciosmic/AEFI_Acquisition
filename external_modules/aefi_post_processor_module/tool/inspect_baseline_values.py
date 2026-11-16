
import sys
from pathlib import Path

# tool/ est dans le module : external_modules/ doit être sur sys.path pour importer aefi_post_processor_module.
MODULE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_DIR.parent))

import h5py
import numpy as np

def inspect_baseline():
    repo_dir = MODULE_DIR / "_tests" / "synthetic_scans_data_repository"
    # Find latest batch
    batches = sorted([d for d in repo_dir.iterdir() if d.is_dir() and d.name.startswith("batch_")])
    if not batches:
        print("No batch found.")
        return
    
    batch_dir = batches[-1]
    h5_path = batch_dir / "scan_001_baseline.h5"
    
    print(f"Inspecting: {h5_path}")
    
    with h5py.File(h5_path, 'r') as f:
        # Check phase_calibrated data
        if 'phase_calibrated' not in f:
            print("No phase_calibrated group found.")
            return
            
        data = f['phase_calibrated']['data'][:] # (H, W, 6)
        
        # indices: 0=Ux_I, 1=Ux_Q, 2=Uy_I, 3=Uy_Q, 4=Uz_I, 5=Uz_Q
        
        names = ['X Quad (ch1)', 'Y Quad (ch3)', 'Z Quad (ch5)']
        indices = [1, 3, 5]
        
        for name, idx in zip(names, indices):
            channel_data = data[:, :, idx]
            print(f"\n--- {name} ---")
            print(f"Min: {np.min(channel_data)}")
            print(f"Max: {np.max(channel_data)}")
            print(f"Mean: {np.mean(channel_data)}")
            print(f"Std: {np.std(channel_data)}")
            
            non_zeros = np.count_nonzero(channel_data)
            print(f"Non-zero count: {non_zeros} / {channel_data.size}")

if __name__ == "__main__":
    inspect_baseline()
