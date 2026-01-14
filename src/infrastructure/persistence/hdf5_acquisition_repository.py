import h5py
import numpy as np
from typing import List
from pathlib import Path
from datetime import datetime
import logging

from domain.models.aefi_device.repositories.i_acquisition_data_repository import IAcquisitionDataRepository
from domain.models.aefi_device.value_objects.acquisition.acquisition_sample import AcquisitionSample

logger = logging.getLogger(__name__)

class HDF5AcquisitionRepository(IAcquisitionDataRepository):
    """
    HDF5 implementation of the Acquisition Data Repository.
    Persists acquisition samples to an HDF5 file.
    """
    
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    def _get_file_path(self, scan_id: str) -> Path:
        # Sanitize scan_id to be safe for filenames
        safe_id = "".join([c for c in scan_id if c.isalnum() or c in ('-', '_')])
        return self.base_path / f"scan_{safe_id}.h5"

    def save(self, scan_id: str, data: List[AcquisitionSample]) -> None:
        if not data:
            return
            
        file_path = self._get_file_path(scan_id)
        mode = 'a' if file_path.exists() else 'w'
        
        try:
            with h5py.File(file_path, mode) as f:
                # Create or get the group for samples
                if 'acquisition_data' not in f:
                    # Initialize datasets with resizable dimensions
                    # We'll store each component as a separate dataset or a compound dataset
                    # For simplicity/performance, let's use a compound dataset or simple arrays
                    
                    # Let's define a structure. 
                    # We have 6 float components + timestamp
                    # Timestamps in HDF5 are tricky, usually stored as POSIX timestamp (float)
                    
                    dt = np.dtype([
                        ('timestamp', 'f8'),
                        ('x_in_phase', 'f8'), ('x_quadrature', 'f8'),
                        ('y_in_phase', 'f8'), ('y_quadrature', 'f8'),
                        ('z_in_phase', 'f8'), ('z_quadrature', 'f8')
                    ])
                    
                    dset = f.create_dataset(
                        'acquisition_data', 
                        shape=(0,), 
                        maxshape=(None,), 
                        dtype=dt,
                        chunks=True
                    )
                else:
                    dset = f['acquisition_data']
                
                # Prepare data for appending
                new_data = np.zeros(len(data), dtype=dset.dtype)
                for i, sample in enumerate(data):
                    new_data[i] = (
                        sample.timestamp.timestamp(),
                        sample.voltage_x_in_phase, sample.voltage_x_quadrature,
                        sample.voltage_y_in_phase, sample.voltage_y_quadrature,
                        sample.voltage_z_in_phase, sample.voltage_z_quadrature
                    )
                
                # Resize and append
                dset.resize(dset.shape[0] + len(data), axis=0)
                dset[-len(data):] = new_data
                
                logger.debug(f"Saved {len(data)} samples to {file_path}")
                
        except Exception as e:
            logger.error(f"Failed to save data to HDF5: {e}")
            raise

    def find_by_scan(self, scan_id: str) -> List[AcquisitionSample]:
        file_path = self._get_file_path(scan_id)
        if not file_path.exists():
            return []
            
        samples = []
        try:
            with h5py.File(file_path, 'r') as f:
                if 'acquisition_data' in f:
                    dset = f['acquisition_data']
                    for row in dset:
                        ts = datetime.fromtimestamp(row['timestamp'])
                        samples.append(AcquisitionSample(
                            timestamp=ts,
                            voltage_x_in_phase=row['x_in_phase'],
                            voltage_x_quadrature=row['x_quadrature'],
                            voltage_y_in_phase=row['y_in_phase'],
                            voltage_y_quadrature=row['y_quadrature'],
                            voltage_z_in_phase=row['z_in_phase'],
                            voltage_z_quadrature=row['z_quadrature']
                        ))
        except Exception as e:
            logger.error(f"Failed to read data from HDF5: {e}")
            raise
            
        return samples
