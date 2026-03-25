"""
ProcessingPipeline - Orchestrates the complete data processing workflow.
Manages the execution of all processing steps with proper error handling.
"""

from pathlib import Path
from typing import Tuple, Optional, Dict
import numpy as np

from .datahandler import DataHandler
from .data_preprocessor import DataPreProcessor
from .primary_field_phase_calibrator import PrimaryFieldPhaseCalibrator
from .primary_field_amplitude_subtractor import PrimaryFieldAmplitudeSubtractor
from .sensor_to_ef_sources_frame_rotator import SensorToEFSourcesFrameRotator
from .data_interpolator import DataInterpolator


class ProcessingPipeline:
    """
    Orchestrates the complete data processing pipeline.
    Manages execution of all steps: preprocessing → phase calibration → 
    amplitude subtraction → frame rotation → interpolation.
    """
    
    def __init__(
        self,
        output_path: Path,
        border_width: int = 1,
        interpolation_method: str = 'cubic',
        target_grid_size: Optional[int] = None
    ):
        """
        Initialize processing pipeline.
        
        Args:
            output_path: Path to output HDF5 file
            border_width: Width of border for calibration
            interpolation_method: Method for interpolation
            target_grid_size: Target grid size for interpolation
        """
        self.output_path = Path(output_path)
        
        # Initialize all processing modules
        self.data_handler = DataHandler(output_path, mode='a')
        self.preprocessor = DataPreProcessor()
        self.phase_calibrator = PrimaryFieldPhaseCalibrator(border_width=border_width)
        self.amplitude_subtractor = PrimaryFieldAmplitudeSubtractor(border_width=border_width)
        self.frame_rotator = SensorToEFSourcesFrameRotator()
        self.interpolator = DataInterpolator(
            target_grid_size=target_grid_size,
            interpolation_method=interpolation_method
        )
        
        self.current_data = None
        self.current_metadata = {}
    
    def run_full_pipeline(
        self,
        csv_path: Path,
        rotation_angles: Optional[Tuple[float, float, float]] = None,
        reference_point: Tuple[int, int] = (0, 0),
        skip_interpolation: bool = False
    ) -> Dict:
        """
        Run the complete processing pipeline from CSV to final output.
        
        Args:
            csv_path: Path to input CSV file
            rotation_angles: Optional (theta_x, theta_y, theta_z) in degrees
            skip_interpolation: If True, skip interpolation step
            
        Returns:
            Dictionary with processing summary
        """
        summary = {
            'steps_completed': [],
            'errors': []
        }
        
        try:
            # Step 1: Load CSV
            print("Loading CSV data...")
            df = self.data_handler.load_csv(csv_path)
            summary['steps_completed'].append('load_csv')
            
            # Step 2: Preprocess
            print("Preprocessing data...")
            preprocessed, metadata = self.preprocessor.preprocess(df)
            self.data_handler.save_step('preprocessed', preprocessed, metadata)
            self.current_data = preprocessed
            self.current_metadata = metadata
            summary['steps_completed'].append('preprocess')
            
            # Step 3: Phase calibration
            print(f"Calibrating phase (Ref: {reference_point})...")
            phase_calibrated, phase_angles = self.phase_calibrator.calibrate(
                preprocessed, 
                reference_idx=reference_point
            )
            phase_metadata = {'phase_angles': phase_angles, 'reference_point': reference_point}
            self.data_handler.save_step('phase_calibrated', phase_calibrated, phase_metadata)
            self.current_data = phase_calibrated
            summary['steps_completed'].append('phase_calibration')
            
            # Step 4: Amplitude subtraction
            print(f"Subtracting primary field amplitude (Ref: {reference_point})...")
            amplitude_subtracted, mean_amplitudes = self.amplitude_subtractor.subtract_primary_field(
                phase_calibrated,
                reference_idx=reference_point
            )
            amp_metadata = {'mean_amplitudes': mean_amplitudes.tolist()}
            self.data_handler.save_step('amplitude_subtracted', amplitude_subtracted, amp_metadata)
            self.current_data = amplitude_subtracted
            summary['steps_completed'].append('amplitude_subtraction')
            
            # Step 5: Frame rotation (if angles provided)
            if rotation_angles is not None:
                print(f"Rotating to probe frame: {rotation_angles}...")
                rotated, rot_metadata = self.frame_rotator.rotate(
                    amplitude_subtracted,
                    rotation_angles
                )
                self.data_handler.save_step('rotated_frame', rotated, rot_metadata)
                self.current_data = rotated
                summary['steps_completed'].append('frame_rotation')
            else:
                print("Skipping frame rotation (no angles provided)")
                rotated = amplitude_subtracted
            
            # Step 6: Interpolation (if not skipped)
            if not skip_interpolation:
                print("Interpolating to finer grid...")
                extent = metadata['extent']
                interpolated, interp_metadata = self.interpolator.interpolate(
                    rotated,
                    extent
                )
                # Propagate rotation info if available
                if rotation_angles is not None:
                    interp_metadata['rotation_angles'] = rotation_angles
                
                self.data_handler.save_step('interpolated', interpolated, interp_metadata)
                self.current_data = interpolated
                summary['steps_completed'].append('interpolation')
            else:
                print("Skipping interpolation")
            
            # Finalize
            print("Pipeline complete!")
            summary['success'] = True
            summary['output_file'] = str(self.output_path)
            summary['processing_history'] = self.data_handler.get_processing_history()
            
        except Exception as e:
            print(f"Error in pipeline: {e}")
            summary['success'] = False
            summary['errors'].append(str(e))
            raise
        
        return summary
    
    def run_partial_pipeline(
        self,
        start_step: str,
        end_step: str,
        rotation_angles: Optional[Tuple[float, float, float]] = None
    ) -> Dict:
        """
        Run a partial pipeline from start_step to end_step.
        
        Args:
            start_step: Starting step name (must exist in HDF5)
            end_step: Ending step name
            rotation_angles: Optional rotation angles for frame rotation
            
        Returns:
            Dictionary with processing summary
        """
        summary = {
            'steps_completed': [],
            'errors': []
        }
        
        # Define step order
        step_order = [
            'preprocessed',
            'phase_calibrated',
            'amplitude_subtracted',
            'rotated_frame',
            'interpolated'
        ]
        
        if start_step not in step_order or end_step not in step_order:
            raise ValueError(f"Invalid step names. Must be one of: {step_order}")
        
        start_idx = step_order.index(start_step)
        end_idx = step_order.index(end_step)
        
        if start_idx >= end_idx:
            raise ValueError("start_step must come before end_step")
        
        try:
            # Load starting data
            print(f"Loading data from step: {start_step}")
            data, metadata = self.data_handler.load_step(start_step)
            self.current_data = data
            self.current_metadata = metadata
            
            # Execute steps in order
            for step_name in step_order[start_idx + 1:end_idx + 1]:
                if step_name == 'phase_calibrated':
                    print("Calibrating phase...")
                    data, phase_angles = self.phase_calibrator.calibrate(data)
                    self.data_handler.save_step(step_name, data, {'phase_angles': phase_angles})
                    
                elif step_name == 'amplitude_subtracted':
                    print("Subtracting amplitude...")
                    data, mean_amps = self.amplitude_subtractor.subtract_primary_field(data)
                    self.data_handler.save_step(step_name, data, {'mean_amplitudes': mean_amps.tolist()})
                    
                elif step_name == 'rotated_frame':
                    if rotation_angles is None:
                        raise ValueError("rotation_angles required for frame rotation step")
                    print("Rotating frame...")
                    data, rot_meta = self.frame_rotator.rotate(data, rotation_angles)
                    self.data_handler.save_step(step_name, data, rot_meta)
                    
                elif step_name == 'interpolated':
                    print("Interpolating...")
                    extent = metadata.get('extent', [0, 1, 0, 1])
                    data, interp_meta = self.interpolator.interpolate(data, extent)
                    self.data_handler.save_step(step_name, data, interp_meta)
                
                self.current_data = data
                summary['steps_completed'].append(step_name)
            
            summary['success'] = True
            
        except Exception as e:
            print(f"Error in partial pipeline: {e}")
            summary['success'] = False
            summary['errors'].append(str(e))
            raise
        
        return summary
    
    def get_current_data(self) -> Tuple[np.ndarray, Dict]:
        """
        Get the current processed data and metadata.
        
        Returns:
            Tuple of (data, metadata)
        """
        return self.current_data, self.current_metadata
    
    def close(self):
        """Close the data handler and cleanup."""
        self.data_handler.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
