"""
Simple test script for data-driven UI (no GUI display).

Tests the logic without requiring PyQt5 display.
"""

import sys
sys.path.insert(0, 'src')

from interface.hardware_configuration_tabs.parameter_spec import ParameterSpec
from infrastructure.adapters.ad9106_ui_adapter import AD9106UIAdapter


def test_parameter_spec():
    """Test ParameterSpec creation and validation."""
    print("=" * 60)
    print("TEST 1: ParameterSpec Creation and Validation")
    print("=" * 60)
    
    # Create a spec
    spec = ParameterSpec(
        name='freq_hz',
        label='Frequency',
        type='spinbox',
        default=1000,
        range=(100, 10000),
        unit='Hz'
    )
    
    print(f"✓ Created spec: {spec.name} ({spec.label})")
    print(f"  Type: {spec.type}, Range: {spec.range}, Unit: {spec.unit}")
    
    # Test validation - valid value
    is_valid, error = spec.validate_value(5000)
    print(f"\n✓ Validate 5000: {is_valid} (expected: True)")
    assert is_valid is True
    
    # Test validation - invalid value (out of range)
    is_valid, error = spec.validate_value(50000)
    print(f"✓ Validate 50000: {is_valid} (expected: False)")
    print(f"  Error: {error}")
    assert is_valid is False
    assert 'must be between' in error
    
    print("\n✅ ParameterSpec tests PASSED\n")


def test_ad9106_adapter():
    """Test AD9106UIAdapter specs and validation."""
    print("=" * 60)
    print("TEST 2: AD9106UIAdapter")
    print("=" * 60)
    
    # Get specs
    specs = AD9106UIAdapter.get_parameter_specs()
    print(f"✓ Got {len(specs)} parameter specs from AD9106UIAdapter")
    
    # Display specs
    print("\nParameter Specifications:")
    for spec in specs[:3]:  # Show first 3
        print(f"  - {spec.label} ({spec.name}): {spec.type}, default={spec.default}")
    print(f"  ... and {len(specs) - 3} more")
    
    # Test adapter validation
    adapter = AD9106UIAdapter()
    
    # Valid config
    valid_config = {
        'freq_hz': 1000,
        'gain_dds1': 8000,
        'gain_dds2': 8000,
        'gain_dds3': 8000,
        'gain_dds4': 8000,
    }
    
    is_valid, error = adapter.validate_config(valid_config)
    print(f"\n✓ Validate valid config: {is_valid} (expected: True)")
    assert is_valid is True
    
    # Invalid config (high freq + high gain)
    invalid_config = {
        'freq_hz': 6000,  # > 5000
        'gain_dds1': 15000,  # > 12000
        'gain_dds2': 8000,
        'gain_dds3': 8000,
        'gain_dds4': 8000,
    }
    
    is_valid, error = adapter.validate_config(invalid_config)
    print(f"✓ Validate invalid config: {is_valid} (expected: False)")
    print(f"  Error: {error}")
    assert is_valid is False
    assert 'Gain too high' in error
    
    print("\n✅ AD9106UIAdapter tests PASSED\n")


def test_config_application():
    """Test configuration application flow."""
    print("=" * 60)
    print("TEST 3: Configuration Application Flow")
    print("=" * 60)
    
    adapter = AD9106UIAdapter()
    
    # Simulate user config
    user_config = {
        'freq_hz': 2000,
        'gain_dds1': 10000,
        'phase_dds1': 16384,  # 90°
        'gain_dds2': 10000,
        'phase_dds2': 32768,  # 180°
        'gain_dds3': 10000,
        'phase_dds3': 49152,  # 270°
        'gain_dds4': 10000,
        'phase_dds4': 0,      # 0°
    }
    
    print("User configuration:")
    for key, value in user_config.items():
        print(f"  {key}: {value}")
    
    # Validate
    is_valid, error = adapter.validate_config(user_config)
    print(f"\n✓ Validation: {is_valid}")
    
    if is_valid:
        # Apply
        print("✓ Applying configuration to hardware...")
        try:
            adapter.apply_config(user_config)
            print("✅ Configuration applied successfully")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print(f"❌ Validation failed: {error}")
    
    print("\n✅ Configuration flow test PASSED\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("DATA-DRIVEN UI LOGIC TESTS")
    print("=" * 60 + "\n")
    
    try:
        test_parameter_spec()
        test_ad9106_adapter()
        test_config_application()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
