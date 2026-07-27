Data Processing Architecture - AEFI Acquisition
This document outlines the decomposed architecture for the AEFI data processing pipeline, breaking down responsibilities into focused, testable modules.

Overview
The data processing pipeline transforms raw CSV scan data into calibrated, interpolated HDF5 datasets ready for analysis. Each processing step is saved in HDF5 for traceability.

Module Responsibilities
1. DataHandler Lifecycle
File: datahandler.py

Responsibilities:

Load raw CSV scan data
Save processed data to HDF5 format
Manage HDF5 file structure and metadata
Track processing history and timestamps
2. Data Pre-Processor
File: data_preprocessor.py

Responsibilities:

Transform CSV data into HDF5 format
Fill incomplete scans (padding with NaN)
Homogenize data structure (ensure consistent grid dimensions)
Create square grids from irregular scan patterns
3. Primary Field Phase Calibrator
File: primary_field_phase_calibrator.py

Responsibilities:

Extract phase values from image border (reference points)
Calculate mean phase angle at borders
Apply rotation to cancel quadrature phase signal for reference points
Align signal to in-phase axis
Algorithm: Takes mean(phase_border) and rotates entire image by -θ to zero out quadrature component at edges.

4. Primary Field Amplitude Subtractor
File: primary_field_amplitude_subtractor.py

Responsibilities:

Extract amplitude values from image border (excluding NaN)
Calculate mean amplitude at borders
Subtract mean border value from entire image
Remove DC offset/background field
Algorithm: Computes mean(amplitude_border) and subtracts from all pixels.

5. Sensor to EF Sources Frame Rotator
File: sensor_to_ef_sources_frame_rotator.py

Responsibilities:

Apply 3D rotation to project sensor frame → probe frame
Use quaternion-based rotation for numerical stability
Handle rotation angles (θx, θy, θz)
Transform vector fields (Ux, Uy, Uz)
Algorithm: Uses quaternion rotation q * v * q^(-1) for stability over Euler angles.

6. Data Interpolator
File: data_interpolator.py

Responsibilities:

Interpolate data onto finer grid
Support multiple interpolation methods (linear, cubic, etc.)
Handle NaN values appropriately
Preserve data quality metrics
Sequence Diagram
The following diagram shows the complete data processing workflow from CSV input to final HDF5 output:

@startuml
!theme plain
skinparam sequenceMessageAlign center
skinparam responseMessageBelowArrow true
actor User
participant "DataHandler" as DH
participant "DataPreProcessor" as DPP
participant "PhaseCalibrator" as PC
participant "AmplitudeSubtractor" as AS
participant "FrameRotator" as FR
participant "DataInterpolator" as DI
database "HDF5 File" as HDF5
User -> DH: load_csv("scan_data.csv")
activate DH
DH -> DH: read_csv_file()
DH --> User: raw_dataframe
deactivate DH
User -> DPP: preprocess(raw_dataframe)
activate DPP
DPP -> DPP: transform_to_hdf5_structure()
DPP -> DPP: fill_incomplete_scans()
note right: Pad with NaN for missing points
DPP -> DPP: homogenize_grid()
note right: Create square grid
DPP -> DH: save_step("preprocessed", data)
activate DH
DH -> HDF5: write_dataset("/preprocessed", data)
DH -> HDF5: write_metadata(timestamp, params)
deactivate DH
DPP --> User: preprocessed_data
deactivate DPP
User -> PC: calibrate_phase(preprocessed_data)
activate PC
PC -> PC: extract_border_pixels()
note right: Get reference points from edges
PC -> PC: calculate_mean_phase()
note right: θ = mean(atan2(Q, I))
PC -> PC: apply_phase_rotation(-θ)
note right: Rotate to cancel quadrature
PC -> DH: save_step("phase_calibrated", data)
activate DH
DH -> HDF5: write_dataset("/phase_calibrated", data)
DH -> HDF5: write_metadata(phase_angle, timestamp)
deactivate DH
PC --> User: phase_calibrated_data
deactivate PC
User -> AS: subtract_primary_field(phase_calibrated_data)
activate AS
AS -> AS: extract_border_pixels()
AS -> AS: calculate_mean_amplitude()
note right: A_mean = mean(border_values, ignore_nan)
AS -> AS: subtract_from_all(A_mean)
AS -> DH: save_step("amplitude_subtracted", data)
activate DH
DH -> HDF5: write_dataset("/amplitude_subtracted", data)
DH -> HDF5: write_metadata(mean_amplitude, timestamp)
deactivate DH
AS --> User: amplitude_subtracted_data
deactivate AS
User -> FR: rotate_to_probe_frame(data, angles)
activate FR
FR -> FR: create_quaternion(θx, θy, θz)
note right: Stable rotation representation
FR -> FR: apply_rotation_to_vectors()
note right: q * v * q^(-1) for each (Ux, Uy, Uz)
FR -> DH: save_step("rotated_frame", data)
activate DH
DH -> HDF5: write_dataset("/rotated_frame", data)
DH -> HDF5: write_metadata(rotation_angles, quaternion)
deactivate DH
FR --> User: rotated_data
deactivate FR
User -> DI: interpolate(rotated_data, target_grid)
activate DI
DI -> DI: create_finer_grid()
DI -> DI: interpolate_values(method="cubic")
note right: Handle NaN appropriately
DI -> DI: validate_quality()
DI -> DH: save_step("interpolated", data)
activate DH
DH -> HDF5: write_dataset("/interpolated", data)
DH -> HDF5: write_metadata(grid_params, method)
deactivate DH
DI --> User: final_interpolated_data
deactivate DI
User -> DH: close_hdf5()
activate DH
DH -> HDF5: flush_and_close()
deactivate DH
@enduml
Class Diagram
The following diagram shows the class structure and relationships:

@startuml
!theme plain
package "Data Processing Pipeline" {
    
    class DataHandler {
        - hdf5_file: h5py.File
        - file_path: Path
        - processing_history: List[str]
        + __init__(file_path: Path)
        + load_csv(csv_path: Path): DataFrame
        + save_step(step_name: str, data: ndarray, metadata: dict)
        + load_step(step_name: str): Tuple[ndarray, dict]
        + get_processing_history(): List[str]
        + close()
    }
    
    class DataPreProcessor {
        - grid_size: Optional[int]
        + transform_to_hdf5(df: DataFrame): ndarray
        + fill_incomplete_scans(data: ndarray, coords: dict): ndarray
        + homogenize_grid(data: ndarray): ndarray
        + create_square_grid(df: DataFrame, value_col: str): Tuple[ndarray, dict]
    }
    
    class PrimaryFieldPhaseCalibrator {
        - border_width: int
        + extract_border_pixels(data: ndarray): ndarray
        + calculate_mean_phase(border_data: ndarray): float
        + apply_phase_rotation(data: ndarray, theta: float): ndarray
        + calibrate(data: ndarray): Tuple[ndarray, float]
    }
    
    class PrimaryFieldAmplitudeSubtractor {
        - border_width: int
        + extract_border_pixels(data: ndarray): ndarray
        + calculate_mean_amplitude(border_data: ndarray, ignore_nan: bool): float
        + subtract_from_all(data: ndarray, mean_value: float): ndarray
        + subtract_primary_field(data: ndarray): Tuple[ndarray, float]
    }
    
    class SensorToEFSourcesFrameRotator {
        - rotation_angles: Tuple[float, float, float]
        - quaternion: Quaternion
        + set_rotation_angles(theta_x: float, theta_y: float, theta_z: float)
        + create_quaternion(angles: Tuple): Quaternion
        + apply_rotation_to_vector(vector: ndarray): ndarray
        + rotate_vector_field(data: ndarray): ndarray
        + get_rotation_matrix(): ndarray
    }
    
    class DataInterpolator {
        - target_grid_size: int
        - interpolation_method: str
        + create_finer_grid(original_extent: dict, factor: int): ndarray
        + interpolate_values(data: ndarray, method: str): ndarray
        + validate_quality(original: ndarray, interpolated: ndarray): dict
        + interpolate(data: ndarray, target_grid: ndarray): ndarray
    }
    
    class ProcessingPipeline {
        - data_handler: DataHandler
        - preprocessor: DataPreProcessor
        - phase_calibrator: PrimaryFieldPhaseCalibrator
        - amplitude_subtractor: PrimaryFieldAmplitudeSubtractor
        - frame_rotator: SensorToEFSourcesFrameRotator
        - interpolator: DataInterpolator
        + __init__(output_path: Path)
        + run_full_pipeline(csv_path: Path, rotation_angles: Tuple)
        + run_partial_pipeline(start_step: str, end_step: str)
    }
    
    class Quaternion {
        - w: float
        - x: float
        - y: float
        - z: float
        + from_euler_angles(theta_x, theta_y, theta_z): Quaternion
        + rotate_vector(v: ndarray): ndarray
        + to_rotation_matrix(): ndarray
        + conjugate(): Quaternion
        + multiply(other: Quaternion): Quaternion
    }
}
ProcessingPipeline *-- DataHandler
ProcessingPipeline *-- DataPreProcessor
ProcessingPipeline *-- PrimaryFieldPhaseCalibrator
ProcessingPipeline *-- PrimaryFieldAmplitudeSubtractor
ProcessingPipeline *-- SensorToEFSourcesFrameRotator
ProcessingPipeline *-- DataInterpolator
SensorToEFSourcesFrameRotator *-- Quaternion
note right of DataHandler
  Manages HDF5 lifecycle
  Tracks all processing steps
  Ensures traceability
end note
note right of PrimaryFieldPhaseCalibrator
  Uses border pixels as reference
  Cancels quadrature phase signal
  θ = mean(atan2(Q_border, I_border))
end note
note right of SensorToEFSourcesFrameRotator
  Uses quaternions for stability
  Avoids gimbal lock
  Rotation: q * v * q^(-1)
end note
@enduml
Test Design Diagram
The following diagram describes the test architecture using analytic functions for predictable, verifiable results:

@startuml
!theme plain
package "Test Architecture" {
    
    abstract class AnalyticTestCase {
        # analytic_function: Callable
        # expected_result: Any
        + generate_test_data(): ndarray
        + compute_expected_output(): Any
        + verify_result(actual: Any, expected: Any): bool
        + run_test()
    }
    
    class PhaseCalibrationTest {
        + generate_test_data(): ndarray
        + compute_expected_output(): float
        + verify_result(actual, expected): bool
    }
    
    class AmplitudeSubtractionTest {
        + generate_test_data(): ndarray
        + compute_expected_output(): ndarray
        + verify_result(actual, expected): bool
    }
    
    class FrameRotationTest {
        + generate_test_data(): ndarray
        + compute_expected_output(): ndarray
        + verify_result(actual, expected): bool
    }
    
    class InterpolationTest {
        + generate_test_data(): ndarray
        + compute_expected_output(): ndarray
        + verify_result(actual, expected): bool
    }
    
    class GridHomogenizationTest {
        + generate_test_data(): DataFrame
        + compute_expected_output(): ndarray
        + verify_result(actual, expected): bool
    }
    
    class EndToEndPipelineTest {
        - all_modules: List[Module]
        + generate_synthetic_scan(): DataFrame
        + run_pipeline(): ndarray
        + verify_final_output(): bool
    }
}
AnalyticTestCase <|-- PhaseCalibrationTest
AnalyticTestCase <|-- AmplitudeSubtractionTest
AnalyticTestCase <|-- FrameRotationTest
AnalyticTestCase <|-- InterpolationTest
AnalyticTestCase <|-- GridHomogenizationTest
AnalyticTestCase <|-- EndToEndPipelineTest
note right of PhaseCalibrationTest
  **Analytic Function**: 
  f(x,y) = A·cos(ωx + φ) + i·A·sin(ωx + φ)
  
  **Test Strategy**:
  1. Generate signal with known phase φ
  2. Add constant phase to border
  3. Verify calibration recovers -φ
  4. Check border quadrature → 0
  
  **Expected**: θ_calibrated = -φ
  **Tolerance**: |θ_actual - θ_expected| < 1e-6
end note
note right of AmplitudeSubtractionTest
  **Analytic Function**:
  f(x,y) = A₀ + A₁·sin(kx)·sin(ky)
  
  **Test Strategy**:
  1. Generate field with DC offset A₀
  2. Border values = A₀ (sine zeros)
  3. Verify subtraction removes A₀
  4. Check border → 0
  
  **Expected**: border_mean = A₀
  **After subtraction**: mean(border) ≈ 0
  **Tolerance**: < 1e-10
end note
note right of FrameRotationTest
  **Analytic Function**:
  v(x,y) = [sin(kx), cos(ky), 0]
  
  **Test Strategy**:
  1. Create known vector field
  2. Apply rotation R(θx, θy, θz)
  3. Verify: v_rotated = R·v_original
  4. Check quaternion vs matrix equivalence
  5. Verify inverse: R^(-1)·R·v = v
  
  **Expected**: ||v_rotated - R·v|| < 1e-12
  **Quaternion stability**: No gimbal lock
end note
note right of InterpolationTest
  **Analytic Function**:
  f(x,y) = x² + y² (smooth polynomial)
  
  **Test Strategy**:
  1. Sample on coarse grid
  2. Interpolate to fine grid
  3. Compare with analytic values
  4. Check interpolation order accuracy
  
  **Expected**: 
  - Linear: O(h²) error
  - Cubic: O(h⁴) error
  **Tolerance**: Verify convergence rate
end note
note right of GridHomogenizationTest
  **Analytic Function**:
  Incomplete grid with known pattern
  
  **Test Strategy**:
  1. Create partial scan (missing corners)
  2. Verify NaN padding in correct locations
  3. Check grid becomes square
  4. Verify extent preservation
  
  **Expected**: 
  - Grid shape: (N, N) where N = max(nx, ny)
  - Missing data → NaN
  - Extent: [x_min, x_max, y_min, y_max]
end note
note right of EndToEndPipelineTest
  **Synthetic Scan**:
  Combination of all analytic functions
  
  **Test Strategy**:
  1. Generate complete synthetic scan:
     - Known phase offset
     - Known DC background
     - Known rotation
     - Coarse grid
  2. Run full pipeline
  3. Verify each step's output
  4. Check final result matches expected
  
  **Verification Points**:
  - After phase cal: Q_border ≈ 0
  - After amplitude sub: border ≈ 0
  - After rotation: v' = R·v
  - After interpolation: smooth field
  
  **Traceability**: Load each HDF5 step
  and verify intermediate results
end note
@enduml
Reusable Logic from Existing Code
From 
transformation_service.py
The 
TransformationService
 provides excellent quaternion-based rotation logic that can be adapted:

# Reusable components:
1. Quaternion rotation using scipy.spatial.transform.Rotation
2. Euler angle → Rotation object conversion
3. Direct and inverse transformations
4. Enable/disable mechanism for transformations
Adaptations needed:

Extend to handle full vector field arrays (not just single vectors)
Add batch processing for efficiency
Integrate with HDF5 saving mechanism
From 
signal_processor.py
The 
SignalPostProcessor
 provides the phase rotation and amplitude subtraction logic:

# Reusable components:
1. Phase angle calculation: θ = atan2(Q, I)
2. Phase rotation matrix application
3. Offset subtraction (noise, primary field)
4. Processing state management
Adaptations needed:

Extend from single-sample to full image processing
Add border extraction logic
Modify to work with numpy arrays instead of dictionaries
Add mean calculation over border pixels
From 
plot_scan.py
The plotting script provides grid creation and homogenization:

# Reusable components:
1. create_square_grid() - padding with NaN
2. CSV loading and coordinate extraction
3. Extent calculation for visualization
4. Grid size determination
Adaptations needed:

Separate visualization from data processing
Move grid creation to DataPreProcessor
Add HDF5 saving instead of pickle
Enhance metadata tracking
Implementation Priority
DataHandler - Foundation for all other modules
DataPreProcessor - Transform CSV → HDF5 structure
PrimaryFieldPhaseCalibrator - Reuse signal_processor logic
PrimaryFieldAmplitudeSubtractor - Reuse signal_processor logic
SensorToEFSourcesFrameRotator - Adapt transformation_service
DataInterpolator - New implementation
ProcessingPipeline - Orchestrator
Test Suite - Implement all analytic tests
HDF5 Structure for Traceability
scan_data.h5
├── /raw_data
│   ├── data: [N×M×6] array (x, y, z × I, Q)
│   ├── coordinates: [N×M×2] (x, y positions)
│   └── metadata: {timestamp, source_file, ...}
├── /preprocessed
│   ├── data: [N×N×6] homogenized grid
│   ├── extent: [x_min, x_max, y_min, y_max]
│   └── metadata: {grid_size, padding_info, timestamp}
├── /phase_calibrated
│   ├── data: [N×N×6] phase-corrected
│   └── metadata: {phase_angles: [θx, θy, θz], timestamp}
├── /amplitude_subtracted
│   ├── data: [N×N×6] background removed
│   └── metadata: {mean_amplitudes: [Ax, Ay, Az], timestamp}
├── /rotated_frame
│   ├── data: [N×N×6] sensor → probe frame
│   └── metadata: {rotation_angles, quaternion, timestamp}
└── /interpolated
    ├── data: [M×M×6] fine grid
    └── metadata: {interpolation_method, grid_factor, timestamp}
Each step preserves the complete processing chain for reproducibility and debugging.