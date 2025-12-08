# Domain Refactoring: Measurement Precision

## Summary

Refactored the domain model to use **quantization noise** as the business concept instead of hardware-specific parameters (ADC gains, OSR, sampling rate).

## Changes Made

### 1. PlantUML Diagram Updated
**File:** `docs/diagrams/domain/services/automatic_step_scan_service.puml`

**Changes:**
- Replaced `AcquisitionParameters` with `MeasurementPrecision`
- Updated `StepScanConfig` to use `measurement_precision` instead of `acquisition_params`
- Updated `IAcquisitionPort` interface: `configure_for_precision()` instead of `configure()`
- Added `quantization_noise_estimate_volts` to `VoltageMeasurement`
- Enhanced documentation notes explaining domain/infrastructure separation

### 2. Domain Value Objects Created

#### `MeasurementPrecision` (NEW)
**File:** `src/domain/value_objects/measurement_precision.py`

**Concept:** Business-level precision expressed as quantization noise

**Attributes:**
- `max_quantization_noise_volts: float` - Maximum acceptable quantization noise
- `target_resolution_bits: Optional[int]` - Optional target ENOB

**Methods:**
- `validate()` - Domain-level validation
- `effective_number_of_bits(signal_range_volts)` - Calculate ENOB
- `required_samples_for_snr(target_snr_db, base_snr_db)` - Calculate averaging needed

**Example:**
```python
precision = MeasurementPrecision(max_quantization_noise_volts=10e-6)  # 10 µV
enob = precision.effective_number_of_bits(signal_range_volts=2.5)  # 17.93 bits
```

#### `VoltageMeasurement` (UPDATED)
**File:** `src/domain/value_objects/acquisition/voltage_measurement.py`

**Added:**
- `quantization_noise_estimate_volts: Optional[float]` - Quality metric

### 3. Infrastructure Adapter Created

#### `ADS131A04Adapter` (NEW)
**File:** `src/infrastructure/adapters/ads131a04_adapter.py`

**Responsibility:** Translate domain concepts to hardware configuration

**Key Method:**
```python
def configure_for_precision(self, precision: MeasurementPrecision) -> None:
    """
    Translates MeasurementPrecision → ADCHardwareConfig
    Formula: Q_noise = Vref / (2^N · Gain · √OSR)
    """
```

**Translation Logic:**
1. Calculate required ENOB from target quantization noise
2. Select optimal PGA gain
3. Calculate required OSR (oversampling ratio)
4. Configure ADC hardware

**Example:**
```python
# Domain (business concept)
precision = MeasurementPrecision(max_quantization_noise_volts=10e-6)

# Infrastructure translates to hardware
adapter.configure_for_precision(precision)
# → Calculates: gain=8, OSR=512, sampling_rate=250Hz
```

## Architecture Benefits

### Before (Hardware in Domain)
```python
# ❌ Domain knew about hardware details
params = AcquisitionParameters(
    averaging_adc=256,  # Hardware OSR
    adc_gains={1:8, 2:8, 3:8, 4:8, 5:8, 6:8},  # Hardware gains
    sampling_rate=10000.0  # Hardware rate
)
```

### After (Business Concept in Domain)
```python
# ✅ Domain uses business language
precision = MeasurementPrecision(
    max_quantization_noise_volts=10e-6  # Business: "10 µV precision"
)

# Infrastructure handles hardware translation
adapter.configure_for_precision(precision)
```

### Separation of Concerns

| Layer | Knows About | Doesn't Know About |
|-------|-------------|-------------------|
| **Domain** | Quantization noise, ENOB, precision requirements | ADC model, gains, OSR, hardware registers |
| **Infrastructure** | ADC specifications, hardware configuration | Business rules, scan logic, domain validation |

## Key Principles Applied

### 1. Ubiquitous Language
- Physicists talk about "precision" and "noise", not "ADC gains"
- Domain model uses the language of domain experts

### 2. Hexagonal Architecture
- Domain defines **WHAT** (precision needed)
- Infrastructure defines **HOW** (hardware configuration)
- Port (`IAcquisitionPort`) separates the two

### 3. Hardware Independence
- Changing from ADS131A04 to another ADC:
  - ✅ Domain code: **unchanged**
  - ✅ Only adapter needs updating

### 4. Testability
- Domain logic testable without hardware
- Mock adapter can return predictable `VoltageMeasurement`

## Formula Reference

### Quantization Noise Calculation
```
Q_noise = Vref / (2^N · Gain · √OSR)

Where:
- Q_noise: Quantization noise (volts)
- Vref: Reference voltage (e.g., 2.5V)
- N: ADC resolution (e.g., 24 bits)
- Gain: PGA gain (1, 2, 4, 8, 16, 32, 64, 128)
- OSR: Oversampling ratio (128, 256, 512, ..., 16384)
```

### Effective Number of Bits (ENOB)
```
ENOB = log2(signal_range / quantization_noise)
```

### Example Calculation
```
Target: 10 µV quantization noise
Hardware: ADS131A04 (24-bit, Vref=2.5V)

Required ENOB = log2(2.5 / 10e-6) = 17.93 bits

With Gain=8:
Required OSR = (2.5 / (10e-6 · 2^24 · 8))^2 ≈ 512

Result: Gain=8, OSR=512 → Q_noise ≈ 9.3 µV ✓
```

## Migration Path

### For Existing Code Using `AcquisitionParameters`

1. **Replace parameter creation:**
```python
# Old
params = AcquisitionParameters(averaging_adc=256, adc_gains={...}, sampling_rate=10000)

# New
precision = MeasurementPrecision(max_quantization_noise_volts=10e-6)
```

2. **Update adapter calls:**
```python
# Old
adapter.configure(params)

# New
adapter.configure_for_precision(precision)
```

3. **Update `StepScanConfig`:**
```python
# Old
config = StepScanConfig(..., acquisition_params=params)

# New
config = StepScanConfig(..., measurement_precision=precision)
```

## Next Steps

1. **Update Application Layer** - Modify `DeviceAcquisitionConfigService` to use `MeasurementPrecision`
2. **Create Port Interface** - Define `IAcquisitionPort` protocol/ABC
3. **Update GUI** - Replace gain/OSR controls with precision slider (µV)
4. **Add Tests** - Unit tests for `MeasurementPrecision` and adapter translation logic
5. **Documentation** - Update user documentation to explain precision concept

## Files Modified/Created

### Created
- `src/domain/value_objects/measurement_precision.py`
- `src/infrastructure/adapters/ads131a04_adapter.py`
- `docs/DOMAIN_REFACTORING_MEASUREMENT_PRECISION.md` (this file)

### Modified
- `docs/diagrams/domain/services/automatic_step_scan_service.puml`
- `src/domain/value_objects/acquisition/voltage_measurement.py`

## References

- **DDD Concept:** Ubiquitous Language (Evans, 2003)
- **Architecture:** Hexagonal Architecture / Ports & Adapters (Cockburn, 2005)
- **Hardware:** ADS131A04 Datasheet (Texas Instruments)
