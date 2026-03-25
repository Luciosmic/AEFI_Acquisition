
import numpy as np
from tools.post_processor_modules.tests.synthetic_scan_generator import SyntheticScanGenerator
from tools.post_processor_modules.processing.primary_field_phase_calibrator import PrimaryFieldPhaseCalibrator

def verify_hypothesis():
    # 1. Generate Base Signal
    generator = SyntheticScanGenerator(grid_size=50, scan_range=10.0)
    data = generator.generate_base_signal()
    
    # 2. Extract Reference (0,0)
    ref_vec = data[0, 0, :]
    print("Reference Vector (0,0):")
    # I, Q for X (0,1), Y (2,3), Z (4,5)
    print(f"X: I={ref_vec[0]}, Q={ref_vec[1]}")
    print(f"Y: I={ref_vec[2]}, Q={ref_vec[3]}")
    print(f"Z: I={ref_vec[4]}, Q={ref_vec[5]}")
    
    # 3. Calculate Theta using Calibrator logic
    calibrator = PrimaryFieldPhaseCalibrator()
    corrections = calibrator.calculate_phase_correction(ref_vec)
    
    print("\nCalculated Corrections:")
    for axis in ['x', 'y', 'z']:
        c = corrections[axis]
        theta_rad = c['theta']
        theta_deg = np.rad2deg(theta_rad)
        sin_t = np.sin(theta_rad)
        print(f"{axis.upper()}: Theta={theta_rad} rad ({theta_deg} deg), sin(theta)={sin_t}")
        
    print("\nExplanation:")
    print("If sin(theta) is not exactly 0, rotation 'leaks' I into Q: Q_new = -I*sin(theta) + ...")

if __name__ == "__main__":
    verify_hypothesis()
