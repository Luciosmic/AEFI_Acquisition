import time
from typing import Optional
from ...domain.ports.scan_port import ScanPort, ScanObserver
from ...domain.entities.spatial_scan import Scan
from ...domain.value_objects import ScanResults
from ...domain.value_objects.scan.scan_point_result import ScanPointResult

# Try to import the Rust module. 
# In a real environment, this would be installed via pip.
# For now, we might need to mock it if it's not built.
try:
    import aefi_scan_engine
except ImportError:
    aefi_scan_engine = None

class RustScanAdapter(ScanPort):
    """Adapter for the Rust-based Scan Engine.
    
    Implements the ScanPort interface to allow the Domain to execute scans
    using the high-performance Rust engine.
    """
    
    def __init__(self, port_name: str = "/dev/ttyUSB0", baud_rate: int = 115200):
        self.port_name = port_name
        self.baud_rate = baud_rate
        self._engine = None
        
    def _get_engine(self):
        """Lazy initialization of the Rust engine."""
        if self._engine is None:
            if aefi_scan_engine is None:
                raise RuntimeError("Rust scan engine module 'aefi_scan_engine' not found.")
            self._engine = aefi_scan_engine.RustScanExecutor(self.port_name, self.baud_rate)
            self._engine.connect()
        return self._engine

    def execute_scan(self, scan: Scan, observer: ScanObserver) -> ScanResults:
        """Execute the scan using the Rust engine.
        
        Parameters
        ----------
        scan : Scan
            The scan entity defining the trajectory.
        observer : ScanObserver
            Observer for real-time updates.
            
        Returns
        -------
        ScanResults
            The complete results.
        """
        observer.on_scan_started(scan.id)
        
        try:
            engine = self._get_engine()
            
            # 1. Configure Engine based on Scan type
            # For prototype, we assume 1D X-axis scan
            if scan.dimension() != 1:
                raise NotImplementedError("Only 1D scans are supported in this prototype.")
            
            # Extract parameters (simplified for prototype)
            # In a full implementation, we'd iterate over the scan's range
            # or pass the range parameters directly to Rust.
            # Assuming SpatialScan1D for now.
            x_min = int(scan.position_range.min_value * 1000) # Convert to microns/steps
            x_max = int(scan.position_range.max_value * 1000)
            step = int(scan.position_range.step * 1000)
            
            # 2. Execute Scan (Blocking call to Rust)
            # The Rust engine returns a list of (x, y) tuples
            # In a real Flyscan, Rust would handle the timing.
            raw_data = engine.start_scan(x_min, x_max, step)
            
            # 3. Process Results
            point_results = []
            for i, (pos_x, measured_val) in enumerate(raw_data):
                # Convert back to Domain types
                # Note: 'measured_val' here is just position for the prototype
                # In real app, it would be the sensor data.
                
                # Create a dummy result for now
                result = ScanPointResult(
                    scan_id=scan.id,
                    point_index=i,
                    position=(float(pos_x)/1000.0, 0.0, 0.0),
                    data={"signal": float(measured_val)} 
                )
                point_results.append(result)
                
                # Notify observer (in a real app, this might happen via a callback from Rust)
                observer.on_scan_point_acquired(scan.id, i, result)
                
                # Update progress
                progress = (i + 1) / len(raw_data)
                observer.on_scan_progress(scan.id, progress)

            observer.on_scan_completed(scan.id)
            
            return ScanResults(
                scan_id=scan.id,
                point_results=point_results
            )
            
        except Exception as e:
            observer.on_scan_failed(scan.id, str(e))
            raise e
