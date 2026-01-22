# AEFI Data Processing Pipeline

Modular, traceable data processing pipeline for AEFI scan data.

## Overview

This package provides a complete pipeline for processing AEFI scan data from raw CSV to calibrated, interpolated HDF5 datasets. Each processing step is saved with metadata for complete traceability.

## Architecture

The pipeline consists of six processing modules:

1. **DataHandler** - HDF5 lifecycle and CSV loading
2. **DataPreProcessor** - Grid creation and homogenization
3. **PrimaryFieldPhaseCalibrator** - Phase calibration using border references
4. **PrimaryFieldAmplitudeSubtractor** - Amplitude subtraction using border references
5. **SensorToEFSourcesFrameRotator** - Quaternion-based frame rotation
6. **DataInterpolator** - Interpolation onto finer grids

Plus an orchestrator:

7. **ProcessingPipeline** - Manages complete workflow

## Quick Start

### Basic Usage

```python
from processing import ProcessingPipeline

# Create pipeline
with ProcessingPipeline("output.h5") as pipeline:
    # Run full pipeline
    summary = pipeline.run_full_pipeline(
        csv_path="scan_data.csv",
        rotation_angles=(0.0, 0.0, 0.0),  # (θx, θy, θz) in degrees
        skip_interpolation=False
    )
    
    print(f"Steps completed: {summary['steps_completed']}")
```

### Individual Module Usage

```python
from processing import (
    DataHandler,
    DataPreProcessor,
    PrimaryFieldPhaseCalibrator,
    PrimaryFieldAmplitudeSubtractor,
    SensorToEFSourcesFrameRotator,
    DataInterpolator
)

# Load data
handler = DataHandler("output.h5")
df = handler.load_csv("scan.csv")

# Preprocess
preprocessor = DataPreProcessor()
grid, metadata = preprocessor.preprocess(df)
handler.save_step("preprocessed", grid, metadata)

# Phase calibration
calibrator = PrimaryFieldPhaseCalibrator(border_width=1)
calibrated, phase_angles = calibrator.calibrate(grid)
handler.save_step("phase_calibrated", calibrated, {"phase_angles": phase_angles})

# Amplitude subtraction
subtractor = PrimaryFieldAmplitudeSubtractor(border_width=1)
subtracted, mean_amps = subtractor.subtract_primary_field(calibrated)
handler.save_step("amplitude_subtracted", subtracted, {"mean_amplitudes": mean_amps.tolist()})

# Frame rotation
rotator = SensorToEFSourcesFrameRotator()
rotated, rot_meta = rotator.rotate(subtracted, angles=(0, 0, 0))
handler.save_step("rotated_frame", rotated, rot_meta)

# Interpolation
interpolator = DataInterpolator(interpolation_method='cubic')
interpolated, interp_meta = interpolator.interpolate(rotated, metadata['extent'])
handler.save_step("interpolated", interpolated, interp_meta)

handler.close()
```

### Partial Pipeline

Resume processing from any step:

```python
with ProcessingPipeline("output.h5") as pipeline:
    # Resume from phase_calibrated, run until interpolated
    summary = pipeline.run_partial_pipeline(
        start_step="phase_calibrated",
        end_step="interpolated",
        rotation_angles=(5.0, 10.0, 0.0)
    )
```

## HDF5 Structure

Each processing step is saved with complete metadata:

```
output.h5
├── /preprocessed
│   ├── data: [N×N×6] array
│   └── attrs: {extent, grid_size, channel_names, timestamp, ...}
├── /phase_calibrated
│   ├── data: [N×N×6] array
│   └── attrs: {phase_angles, timestamp, ...}
├── /amplitude_subtracted
│   ├── data: [N×N×6] array
│   └── attrs: {mean_amplitudes, timestamp, ...}
├── /rotated_frame
│   ├── data: [N×N×6] array
│   └── attrs: {rotation_angles, quaternion, rotation_matrix, timestamp, ...}
└── /interpolated
    ├── data: [M×M×6] array
    └── attrs: {interpolation_method, quality_metrics, timestamp, ...}
```

## Module Details

### DataHandler

Manages HDF5 file lifecycle and CSV loading.

**Key Methods**:
- `load_csv(csv_path)` - Load CSV data
- `save_step(step_name, data, metadata)` - Save processing step
- `load_step(step_name)` - Load processing step
- `get_processing_history()` - Get complete history

### DataPreProcessor

Transforms CSV to homogenized grids.

**Key Methods**:
- `preprocess(dataframe)` - Complete preprocessing
- `create_square_grid(df, value_columns)` - Create square grid with NaN padding

**Features**:
- Handles incomplete scans
- Creates square grids
- Calculates extent and coordinates

### PrimaryFieldPhaseCalibrator

Calibrates phase using border reference points.

**Key Methods**:
- `calibrate(data)` - Complete phase calibration
- `extract_border_pixels(data)` - Extract border region
- `calculate_mean_phase(border_data)` - Calculate mean phase angles
- `apply_phase_rotation(data, phase_angles)` - Apply rotation

**Algorithm**: θ = mean(atan2(Q_border, I_border)), then rotate by -θ

### PrimaryFieldAmplitudeSubtractor

Subtracts primary field using border reference.

**Key Methods**:
- `subtract_primary_field(data)` - Complete subtraction
- `extract_border_pixels(data)` - Extract border region
- `calculate_mean_amplitude(border_data)` - Calculate mean (NaN-aware)
- `subtract_from_all(data, mean_values)` - Subtract from entire image

**Algorithm**: A_mean = mean(border_values, ignore_nan=True), then subtract from all

### SensorToEFSourcesFrameRotator

Rotates sensor frame to probe frame using quaternions.

**Key Methods**:
- `rotate(data, angles)` - Complete rotation
- `set_rotation_angles(θx, θy, θz)` - Set rotation (degrees)
- `rotate_vector_field(data)` - Apply to vector field
- `get_rotation_matrix()` - Get 3×3 matrix
- `get_quaternion()` - Get quaternion [x, y, z, w]

**Features**:
- Quaternion-based (no gimbal lock)
- Batch processing
- Separate I/Q component rotation

### DataInterpolator

Interpolates data onto finer grids.

**Key Methods**:
- `interpolate(data, extent)` - Complete interpolation
- `interpolate_values(data, extent, method)` - Interpolate all channels
- `validate_quality(original, interpolated)` - Quality metrics

**Supported Methods**: 'linear', 'cubic', 'nearest'

**Features**:
- NaN-aware interpolation
- Quality validation
- Configurable upsampling

## Configuration

### Border Width

For phase calibration and amplitude subtraction:

```python
calibrator = PrimaryFieldPhaseCalibrator(border_width=2)  # 2 pixels
subtractor = PrimaryFieldAmplitudeSubtractor(border_width=2)
```

### Interpolation Method

```python
interpolator = DataInterpolator(
    interpolation_method='cubic',  # or 'linear', 'nearest'
    target_grid_size=200  # optional fixed size
)
```

### Pipeline Options

```python
pipeline = ProcessingPipeline(
    output_path="output.h5",
    border_width=1,
    interpolation_method='cubic',
    target_grid_size=None  # auto-determine
)
```

## Example Script

See `example_pipeline.py` for a complete working example that:
- Finds the latest CSV in the scan directory
- Processes it through the full pipeline
- Prints a summary of results

Run with:
```bash
python example_pipeline.py
```

## Dependencies

- numpy
- pandas
- scipy
- h5py

## Design Principles

1. **Single Responsibility** - Each module has one clear purpose
2. **Traceability** - Every step saved with metadata and timestamps
3. **Testability** - Clear inputs/outputs, ready for analytic testing
4. **Flexibility** - Partial pipeline execution, configurable parameters
5. **Reusability** - Logic adapted from existing codebase (transformation_service, signal_processor, plot_scan)

## Next Steps

- Write unit tests with analytic functions
- Write integration tests
- Add performance benchmarks
- Create detailed API documentation
