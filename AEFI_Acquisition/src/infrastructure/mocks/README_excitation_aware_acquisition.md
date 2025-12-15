# Excitation-Aware Acquisition Mock Service

## Overview

The `ExcitationAwareAcquisitionPort` is a mock service that seamlessly integrates acquisition and excitation systems by applying excitation-dependent offsets to acquisition measurements. This simulates the physical coupling between excitation and acquisition that occurs in the real system.

## Key Concepts

### Physical Context

- **Frequency Independence**: After synchronous detection, the signal is continuous with added noise. Frequency has no impact on the processed signal characteristics.

- **Excitation-Dependent Signal**: The signal characteristics are directly tied to the excitation mode. Different excitation modes produce different signal patterns in the acquisition channels.

### Technical Implementation

- **3D Offset Vector**: A 3D vector (X, Y, Z) is applied to the real (in-phase) part of the signal based on the excitation mode.

- **Configurable Ratio**: An adjustable ratio (e.g., 0.9 = 90% real, 10% quadrature) controls how the offset is distributed between in-phase and quadrature components.

- **Separation Function**: Allows isolating and equalizing offset vectors, preparing for future enhancements where excitation and offset vectors may differ.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         ExcitationAwareAcquisitionPort                       │
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Base Acquisition│         │  Excitation Port  │         │
│  │      Port        │         │   (Optional)      │         │
│  └──────────────────┘         └──────────────────┘         │
│         │                              │                     │
│         │ acquire_sample()             │ apply_excitation()  │
│         │                              │                     │
│         └──────────────┬───────────────┘                     │
│                        │                                     │
│         ┌──────────────▼──────────────┐                      │
│         │  Offset Application Logic   │                      │
│         │  - Get excitation mode      │                      │
│         │  - Map to offset vector     │                      │
│         │  - Apply separation/eq.    │                      │
│         │  - Scale by level           │                      │
│         │  - Apply to measurement     │                      │
│         └─────────────────────────────┘                      │
│                        │                                     │
│         ┌──────────────▼──────────────┐                      │
│         │  VoltageMeasurement         │                      │
│         │  (with offset applied)       │                      │
│         └─────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

## Usage

### Basic Usage

```python
from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.mocks.adapter_mock_excitation_aware_acquisition import (
    ExcitationAwareAcquisitionPort
)
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters
from domain.value_objects.excitation.excitation_mode import ExcitationMode
from domain.value_objects.excitation.excitation_level import ExcitationLevel

# Create base acquisition port
base_port = RandomNoiseAcquisitionPort(noise_std=0.1)

# Create excitation port
excitation_port = MockExcitationPort()

# Create excitation-aware acquisition port
aware_port = ExcitationAwareAcquisitionPort(
    base_acquisition_port=base_port,
    excitation_port=excitation_port,
    real_ratio=0.9,  # 90% real, 10% quadrature
    offset_scale=1.0
)

# Set excitation
params = ExcitationParameters(
    mode=ExcitationMode.X_DIR,
    level=ExcitationLevel(100.0),
    frequency=1000.0
)
excitation_port.apply_excitation(params)

# Acquire sample (offset will be applied automatically)
measurement = aware_port.acquire_sample()
```

### Manual Excitation Parameters

If you don't have an excitation port, you can manually set excitation parameters:

```python
# Create port without excitation port
aware_port = ExcitationAwareAcquisitionPort(
    base_acquisition_port=base_port,
    excitation_port=None
)

# Manually set excitation
params = ExcitationParameters(
    mode=ExcitationMode.X_DIR,
    level=ExcitationLevel(100.0),
    frequency=1000.0
)
aware_port.set_excitation_parameters(params)

# Acquire sample
measurement = aware_port.acquire_sample()
```

### Configuration

#### Real/Quadrature Ratio

Control how the offset is distributed between in-phase and quadrature components:

```python
# Set 50% real, 50% quadrature
aware_port.set_real_ratio(0.5)

# Set 100% real, 0% quadrature
aware_port.set_real_ratio(1.0)
```

#### Offset Scale

Global scaling factor for offset magnitude:

```python
# Double the offset magnitude
aware_port.set_offset_scale(2.0)

# Half the offset magnitude
aware_port.set_offset_scale(0.5)
```

#### Custom Offset Vectors

Set custom offset vectors for specific excitation modes:

```python
from infrastructure.mocks.adapter_mock_excitation_aware_acquisition import OffsetVector3D

# Set custom offset for X_DIR mode
custom_offset = OffsetVector3D(2.0, 1.0, 0.5)
aware_port.set_excitation_offset(ExcitationMode.X_DIR, custom_offset)
```

#### Separation Vectors

Isolate different components of the offset (for future enhancements):

```python
# Set separation vector for X_DIR mode
separation = OffsetVector3D(0.5, 0.5, 0.0)
aware_port.set_separation_vector(ExcitationMode.X_DIR, separation)
```

#### Equalization Factors

Normalize offset magnitudes across modes:

```python
# Set equalization factor for X_DIR mode
aware_port.set_equalization_factor(ExcitationMode.X_DIR, 0.5)
```

## Default Excitation Mode Mapping

The default mapping from excitation mode to offset vector is:

| Excitation Mode | Offset Vector (X, Y, Z) | Description |
|----------------|-------------------------|-------------|
| `X_DIR` | (1.0, 0.0, 0.0) | X-axis excitation → X offset |
| `Y_DIR` | (0.0, 0.0, 1.0) | Y-axis excitation → Z offset |
| `CIRCULAR_PLUS` | (0.0, 0.0, 0.0) | No offset for circular modes |
| `CIRCULAR_MINUS` | (0.0, 0.0, 0.0) | No offset for circular modes |
| `CUSTOM` | (0.0, 0.0, 0.0) | No offset for custom modes |

**Note**: The Y_DIR mode maps to a Z offset vector. This is intentional based on the physical system configuration. If you need a different mapping, use `set_excitation_offset()`.

## Offset Application Logic

1. **Get Current Excitation**: Retrieve excitation parameters from the excitation port or manual tracking.

2. **Check Active Excitation**: If excitation level is 0%, no offset is applied.

3. **Get Offset Vector**: Look up the offset vector for the current excitation mode.

4. **Scale by Level**: Multiply offset by excitation level (0.0-1.0) and global scale factor.

5. **Apply Separation/Equalization**: Apply separation vectors and equalization factors if configured.

6. **Apply to Measurement**: 
   - Real component: `new_real = base_real + offset * real_ratio`
   - Quadrature component: `new_quad = base_quad + offset * (1 - real_ratio)`

## Integration with Existing Services

### With Acquisition Services

The `ExcitationAwareAcquisitionPort` implements `IAcquisitionPort`, so it can be used as a drop-in replacement:

```python
# Instead of:
acquisition_port = RandomNoiseAcquisitionPort()

# Use:
base_port = RandomNoiseAcquisitionPort()
excitation_port = MockExcitationPort()
acquisition_port = ExcitationAwareAcquisitionPort(base_port, excitation_port)

# All acquisition services work the same
measurement = acquisition_port.acquire_sample()
```

### With Excitation Services

The service observes excitation changes through the `IExcitationPort` interface:

```python
from application.services.excitation_configuration_service.excitation_configuration_service import (
    ExcitationConfigurationService
)

# Create excitation service
excitation_service = ExcitationConfigurationService(excitation_port)

# Set excitation (will be observed by aware_port)
excitation_service.set_excitation(
    mode=ExcitationMode.X_DIR,
    level_percent=100.0,
    frequency=1000.0
)

# Acquire sample (offset applied automatically)
measurement = aware_port.acquire_sample()
```

## Testing

Unit tests are provided in `tests/test_excitation_aware_acquisition.py`. Run with:

```bash
python -m pytest src/infrastructure/mocks/tests/test_excitation_aware_acquisition.py -v
```

### Test Coverage

- Vector operations (scale, add, multiply)
- Offset application for different excitation modes
- Real/quadrature ratio configuration
- Offset scale configuration
- Custom offset vectors
- Separation vectors
- Equalization factors
- Level scaling
- Edge cases (zero level, invalid ratios)

## Future Enhancements

The separation and equalization functions are designed to support future enhancements:

1. **Different Excitation/Offset Vectors**: When excitation and offset vectors differ, separation vectors can isolate components.

2. **Calibration**: Equalization factors can normalize offsets across modes for calibration purposes.

3. **Frequency-Dependent Offsets**: While frequency doesn't affect the current model, the architecture supports future frequency-dependent offset calculations.

4. **Multi-Mode Offsets**: Support for complex excitation patterns that produce multi-component offsets.

## Design Decisions

### Why Y_DIR Maps to Z Offset?

Based on the physical system configuration, Y-axis excitation produces a signal primarily in the Z acquisition channel. This mapping reflects the actual hardware behavior. If your system differs, use `set_excitation_offset()` to customize.

### Why Real Ratio Defaults to 0.9?

After synchronous detection, the signal is primarily in the real (in-phase) component. A 90% real ratio reflects this physical behavior while allowing some quadrature contribution for noise modeling.

### Why Separation and Equalization?

These functions prepare for future enhancements where:
- Excitation and offset vectors may differ
- Calibration may require mode-specific normalization
- Complex excitation patterns may need component isolation

## Troubleshooting

### No Offset Applied

- Check that excitation level is > 0%
- Verify excitation mode has a non-zero offset vector
- Ensure excitation parameters are set (via port or manual)

### Offset Too Large/Small

- Adjust `offset_scale` parameter
- Check excitation level percentage
- Verify equalization factors

### Wrong Offset Direction

- Check excitation mode mapping
- Use `set_excitation_offset()` to customize
- Verify separation vectors aren't interfering

## See Also

- `IAcquisitionPort`: Base acquisition port interface
- `IExcitationPort`: Excitation port interface
- `VoltageMeasurement`: Domain value object for measurements
- `ExcitationParameters`: Domain value object for excitation configuration

