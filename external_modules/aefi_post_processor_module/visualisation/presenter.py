"""
Visualization Presenter
Orchestrates the module logic with Loading Cache and Embedded Plotting.
"""

from typing import Optional, Dict, Tuple
import logging
import time
import numpy as np

from .model import VisualisationModel
from .view import VisualisationView
from .plot_service import FigureFactory

logger = logging.getLogger(__name__)

class VisualisationPresenter:
    """
    Connects Model and View.
    Handles user actions, data caching, and figure generation.
    """
    
    def __init__(self, view: VisualisationView, model: VisualisationModel):
        self.view = view
        self.model = model
        self.figure_factory = FigureFactory()
        
        # Cache: Key=(scan_path, step_name), Value=(grids, extent, metadata)
        self._data_cache = {} 
        self._step_mapping = {} # Maps display string back to actual step name
        
        # State
        self.current_scan_path: Optional[str] = None
        self.current_step_name: Optional[str] = None
        
        # Connect signals
        self.view.scan_selected_signal.connect(self.on_scan_selected)
        self.view.step_selected_signal.connect(self.on_step_selected)
        
        # Initialize
        self.refresh_scan_list()

    def refresh_scan_list(self):
        scans = self.model.list_scans()
        if scans:
            logger.info("scans.listed repo=%s count=%d", self.model.repo_path, len(scans))
        else:
            logger.warning("scans.none_found repo=%s pattern=**/*.h5", self.model.repo_path)
        
        # Convert paths to relative strings for display
        scan_strs = []
        for p in scans:
            try:
                # Try to make relative to repo root
                rel = p.relative_to(self.model.repo_path)
                scan_strs.append(str(rel))
            except ValueError:
                scan_strs.append(p.name)
                
        self.view.set_scan_list(scan_strs)

    # Define the logical order of processing steps
    PIPELINE_ORDER = [
        'preprocessed',
        'phase_calibrated',
        'amplitude_subtracted',
        'rotated_frame',
        'interpolated'
    ]

    def _format_and_sort_steps(self, steps: list) -> list:
        """Sort steps logically and format them with numbers."""
        ordered_steps = []
        for step in self.PIPELINE_ORDER:
            if step in steps:
                ordered_steps.append(step)
        
        # Add any steps not in the predefined order at the end
        for step in sorted(steps):
            if step not in self.PIPELINE_ORDER:
                ordered_steps.append(step)
                
        formatted_steps = []
        self._step_mapping = {} # Maps display name to actual step name
        for i, step in enumerate(ordered_steps, 1):
            display_name = f"{i} - {step}"
            formatted_steps.append(display_name)
            self._step_mapping[display_name] = step
            
        return formatted_steps

    def on_scan_selected(self, scan_name: str):
        # Don't reload if same scan
        if self.current_scan_path == scan_name:
            return
            
        self.current_scan_path = scan_name
        
        # Reconstruct full path
        full_path = self.model.repo_path / scan_name
        
        logger.info("scan.selected scan=%s", scan_name)
        steps = self.model.load_scan_steps(full_path)
        
        # Sort and format steps
        formatted_steps = self._format_and_sort_steps(steps)
        self.view.set_step_list(formatted_steps)
        if steps:
            logger.info("scan.steps_loaded scan=%s steps=%s", scan_name, list(self._step_mapping.values()))
        else:
            logger.warning("scan.no_steps scan=%s", scan_name)

    def on_step_selected(self, display_name: str):
        if not display_name:
            return
            
        actual_step_name = self._step_mapping.get(display_name, display_name)
        self.current_step_name = actual_step_name
        
        self.update_plot()

    def update_plot(self):
        """Fetch data (cache/load) and update view."""
        if not self.current_scan_path or not self.current_step_name:
            return
            
        start_time = time.time()
        key = (self.current_scan_path, self.current_step_name)
        
        # 1. Fetch Data
        if key in self._data_cache:
            grids, extent, metadata = self._data_cache[key]
            load_source = "Cache"
        else:
            full_path = self.model.repo_path / self.current_scan_path
            try:
                grids, extent, metadata = self.model.get_step_data(full_path, self.current_step_name)
                # Store in cache
                self._data_cache[key] = (grids, extent, metadata)
                load_source = "Disk"
            except Exception as e:
                logger.exception(
                    "step.load_failed scan=%s step=%s error_type=%s error=%s",
                    self.current_scan_path, self.current_step_name, type(e).__name__, e,
                )
                return

        # Update Frame Info
        rot = metadata.get('rotation_angles', 'N/A')
        if isinstance(rot, (list, tuple, np.ndarray)):
            rot_str = f"[{rot[0]:.2f}, {rot[1]:.2f}, {rot[2]:.2f}]"
        else:
            rot_str = str(rot)
            
        ref = metadata.get('reference_point', 'N/A')
        
        self.view.set_frame_info(rot_str, str(ref))

        # 2. Generate Figure
        context = f"{self.current_scan_path} : {self.current_step_name}"
        fig = self.figure_factory.create_figure(grids, extent, metadata, context)
        
        # 3. Update View
        self.view.update_plot(fig)
        
        elapsed = (time.time() - start_time) * 1000
        logger.info(
            "plot.drawn scan=%s step=%s source=%s rotation_angles_deg=%s elapsed_ms=%.1f",
            self.current_scan_path, self.current_step_name, load_source, rot_str, elapsed,
        )
