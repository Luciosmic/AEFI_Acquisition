"""Tests for AcquisitionParameters value object."""
import pytest
from .acquisition_parameters import AcquisitionParameters

def test_acquisition_parameters_creation():
    """Test creating valid acquisition parameters."""
    params = AcquisitionParameters(
        averaging_adc=10,
        adc_gains={1: 0, 2: 1, 3: 2, 4: 3},
        sampling_rate=1000.0
    )
    
    assert params.averaging_adc == 10
    assert params.adc_gains[1] == 0
    assert params.sampling_rate == 1000.0

def test_acquisition_parameters_immutable():
    """Test that parameters are immutable."""
    params = AcquisitionParameters(
        averaging_adc=5,
        adc_gains={1: 0},
        sampling_rate=500.0
    )
    
    with pytest.raises(AttributeError):
        params.averaging_adc = 10

def test_acquisition_parameters_rejects_zero_averaging():
    """Test that averaging_adc must be >= 1."""
    with pytest.raises(ValueError, match="averaging_adc must be >= 1"):
        AcquisitionParameters(
            averaging_adc=0,
            adc_gains={1: 0},
            sampling_rate=1000.0
        )

def test_acquisition_parameters_rejects_negative_averaging():
    """Test that negative averaging is rejected."""
    with pytest.raises(ValueError, match="averaging_adc must be >= 1"):
        AcquisitionParameters(
            averaging_adc=-5,
            adc_gains={1: 0},
            sampling_rate=1000.0
        )

def test_acquisition_parameters_rejects_zero_sampling_rate():
    """Test that sampling_rate must be > 0."""
    with pytest.raises(ValueError, match="sampling_rate must be > 0"):
        AcquisitionParameters(
            averaging_adc=10,
            adc_gains={1: 0},
            sampling_rate=0.0
        )

def test_acquisition_parameters_rejects_negative_sampling_rate():
    """Test that negative sampling rate is rejected."""
    with pytest.raises(ValueError, match="sampling_rate must be > 0"):
        AcquisitionParameters(
            averaging_adc=10,
            adc_gains={1: 0},
            sampling_rate=-100.0
        )

def test_acquisition_parameters_rejects_empty_gains():
    """Test that adc_gains cannot be empty."""
    with pytest.raises(ValueError, match="adc_gains cannot be empty"):
        AcquisitionParameters(
            averaging_adc=10,
            adc_gains={},
            sampling_rate=1000.0
        )

def test_acquisition_parameters_rejects_invalid_channel_id():
    """Test that invalid channel IDs are rejected."""
    with pytest.raises(ValueError, match="Invalid channel ID"):
        AcquisitionParameters(
            averaging_adc=10,
            adc_gains={0: 0},  # Channel 0 is invalid
            sampling_rate=1000.0
        )

def test_acquisition_parameters_rejects_negative_gain():
    """Test that negative gains are rejected."""
    with pytest.raises(ValueError, match="Invalid gain"):
        AcquisitionParameters(
            averaging_adc=10,
            adc_gains={1: -1},
            sampling_rate=1000.0
        )

def test_acquisition_parameters_accepts_all_channels():
    """Test that all 6 channels can be configured."""
    params = AcquisitionParameters(
        averaging_adc=10,
        adc_gains={1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5},
        sampling_rate=1000.0
    )
    
    assert len(params.adc_gains) == 6

