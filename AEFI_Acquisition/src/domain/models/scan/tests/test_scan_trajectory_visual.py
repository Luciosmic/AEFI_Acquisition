import unittest
import matplotlib.pyplot as plt
import os

from domain.models.scan.value_objects.step_scan_config import StepScanConfig
from domain.models.scan.value_objects.scan_zone import ScanZone
from domain.models.scan.value_objects.scan_pattern import ScanPattern
from domain.models.scan.value_objects.measurement_uncertainty import MeasurementUncertainty
from domain.models.scan.scan_trajectory_factory import ScanTrajectoryFactory

class TestScanTrajectoryVisual(unittest.TestCase):
    
    def setUp(self):
        self.base_config = StepScanConfig(
            scan_zone=ScanZone(x_min=0.0, x_max=10.0, y_min=0.0, y_max=10.0),
            x_nb_points=5,
            y_nb_points=5,
            scan_pattern=ScanPattern.RASTER,
            stabilization_delay_ms=100,
            averaging_per_position=1,
            measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=1e-6),
        )

    def _plot_trajectory(self, trajectory, title):
        """Helper to plot trajectory with order indication."""
        points = list(trajectory)
        xs = [p.x for p in points]
        ys = [p.y for p in points]
        
        plt.figure(figsize=(8, 8))
        plt.plot(xs, ys, 'o-', alpha=0.5, label='Path')
        
        # Annotate start and end
        plt.plot(xs[0], ys[0], 'go', markersize=10, label='Start')
        plt.plot(xs[-1], ys[-1], 'ro', markersize=10, label='End')
        
        # Annotate order
        for i, (x, y) in enumerate(zip(xs, ys)):
            plt.annotate(str(i), (x, y), xytext=(5, 5), textcoords='offset points')
            
            # Draw arrows for direction
            if i < len(points) - 1:
                dx = points[i+1].x - x
                dy = points[i+1].y - y
                plt.arrow(x, y, dx*0.5, dy*0.5, head_width=0.2, head_length=0.3, fc='k', ec='k')

        plt.title(title)
        plt.xlabel('X Position')
        plt.ylabel('Y Position')
        plt.grid(True)
        plt.legend()
        
        # Save plot
        filename = f"trajectory_{title.lower().replace(' ', '_')}.png"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        plt.savefig(filepath)
        print(f"Plot saved to {filepath}")
        # plt.show() # Uncomment to show interactively

    def test_visual_raster(self):
        """Generate and plot Raster trajectory."""
        config = self.base_config
        trajectory = ScanTrajectoryFactory.create_trajectory(config)
        self._plot_trajectory(trajectory, "Raster Scan")

    def test_visual_serpentine(self):
        """Generate and plot Serpentine trajectory."""
        config = StepScanConfig(
            scan_zone=self.base_config.scan_zone,
            x_nb_points=5,
            y_nb_points=5,
            scan_pattern=ScanPattern.SERPENTINE,
            stabilization_delay_ms=100,
            averaging_per_position=1,
            measurement_uncertainty=self.base_config.measurement_uncertainty,
        )
        trajectory = ScanTrajectoryFactory.create_trajectory(config)
        self._plot_trajectory(trajectory, "Serpentine Scan")

    def test_visual_comb(self):
        """Generate and plot Comb trajectory."""
        config = StepScanConfig(
            scan_zone=self.base_config.scan_zone,
            x_nb_points=5,
            y_nb_points=5,
            scan_pattern=ScanPattern.COMB,
            stabilization_delay_ms=100,
            averaging_per_position=1,
            measurement_uncertainty=self.base_config.measurement_uncertainty,
        )
        trajectory = ScanTrajectoryFactory.create_trajectory(config)
        self._plot_trajectory(trajectory, "Comb Scan")

if __name__ == '__main__':
    unittest.main()
