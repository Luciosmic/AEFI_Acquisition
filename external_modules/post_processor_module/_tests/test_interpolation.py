import unittest
import numpy as np
import sys
from pathlib import Path

# Add post_processor_modules to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tests.analytic_test_case import AnalyticTestCase
except ImportError:
    from analytic_test_case import AnalyticTestCase
from processing.data_interpolator import DataInterpolator

class TestInterpolation(AnalyticTestCase):
    
    def test_interpolation_recovery(self):
        """
        Verify that interpolation recovers a known smooth function.
        """
        # 1. Generate smooth analytic function
        # f(x, y) = x^2 + y^2
        # Use smaller grid for input
        coarse_grid_size = 10
        x = np.linspace(-1, 1, coarse_grid_size)
        y = np.linspace(-1, 1, coarse_grid_size)
        X, Y = np.meshgrid(x, y)
        
        # Create Data (N, N, 6) - put function in Ch 0
        data_coarse = np.zeros((coarse_grid_size, coarse_grid_size, 6))
        Z_coarse = X**2 + Y**2
        data_coarse[:, :, 0] = Z_coarse
        
        # 2. Interpolate to finer grid
        interpolator = DataInterpolator(interpolation_method='cubic')
        extent = [-1, 1, -1, 1] 
        
        # Upsample by factor of 5 (50 points)
        # Note: DataInterpolator.create_finer_grid estimates points based on target size
        # Let's set target size explicitly
        interpolator.target_grid_size = 50
        
        interpolated_data, metadata = interpolator.interpolate(data_coarse, extent)
        
        # 3. Verify against analytic truth on fine grid
        Z_interp = interpolated_data[:, :, 0]
        
        # Generate analytic truth for fine grid
        x_fine = np.linspace(-1, 1, 50)
        y_fine = np.linspace(-1, 1, 50)
        X_fine, Y_fine = np.meshgrid(x_fine, y_fine)
        Z_truth = X_fine**2 + Y_fine**2
        
        # Calculate error
        error = np.abs(Z_interp - Z_truth)
        max_error = np.max(error)
        mean_error = np.mean(error)
        
        print("\nInterpolation Test Results (cubic):")
        print(f"  Max Error: {max_error}")
        print(f"  Mean Error: {mean_error}")
        
        # For cubic interpolation of a quadratic function, error should be very small/numerical
        self.assertLess(mean_error, 0.005, "Mean interpolation error too high")

if __name__ == '__main__':
    unittest.main()
