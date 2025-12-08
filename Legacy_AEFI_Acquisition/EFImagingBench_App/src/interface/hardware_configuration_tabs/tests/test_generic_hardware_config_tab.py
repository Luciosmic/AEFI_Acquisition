"""
Unit tests for data-driven UI generation.

Tests ParameterSpec, GenericHardwareConfigTab, and validation.
"""

import pytest
import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication

# Add src to path (we're in src/interface/hardware_configuration_tabs/tests/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from interface.hardware_configuration_tabs.parameter_spec import ParameterSpec
from interface.hardware_configuration_tabs.generic_hardware_config_tab import GenericHardwareConfigTab


@pytest.fixture(scope='session')
def qapp():
    """Create QApplication for tests."""
    return QApplication([])


class TestParameterSpec:
    """Test ParameterSpec dataclass."""
    
    def test_create_spinbox_spec(self):
        """Test creating spinbox parameter spec."""
        spec = ParameterSpec(
            name='freq_hz',
            label='Frequency',
            type='spinbox',
            default=1000,
            range=(100, 10000),
            unit='Hz'
        )
        
        assert spec.name == 'freq_hz'
        assert spec.label == 'Frequency'
        assert spec.type == 'spinbox'
        assert spec.default == 1000
        assert spec.range == (100, 10000)
        assert spec.unit == 'Hz'
    
    def test_validate_value_in_range(self):
        """Test validation of value in range."""
        spec = ParameterSpec(
            name='gain',
            label='Gain',
            type='spinbox',
            default=100,
            range=(0, 1000)
        )
        
        is_valid, error = spec.validate_value(500)
        assert is_valid is True
        assert error is None
    
    def test_validate_value_out_of_range(self):
        """Test validation of value out of range."""
        spec = ParameterSpec(
            name='gain',
            label='Gain',
            type='spinbox',
            default=100,
            range=(0, 1000)
        )
        
        is_valid, error = spec.validate_value(1500)
        assert is_valid is False
        assert 'must be between' in error
    
    def test_validate_combo_value(self):
        """Test validation of combo value."""
        spec = ParameterSpec(
            name='mode',
            label='Mode',
            type='combo',
            default='AC',
            options=['AC', 'DC', 'GND']
        )
        
        is_valid, error = spec.validate_value('AC')
        assert is_valid is True
        
        is_valid, error = spec.validate_value('INVALID')
        assert is_valid is False


class TestGenericHardwareConfigTab:
    """Test GenericHardwareConfigTab widget."""
    
    @pytest.fixture
    def simple_specs(self):
        """Create simple parameter specs for testing."""
        return [
            ParameterSpec(
                name='freq_hz',
                label='Frequency',
                type='spinbox',
                default=1000,
                range=(100, 10000),
                unit='Hz'
            ),
            ParameterSpec(
                name='gain',
                label='Gain',
                type='combo',
                default='1',
                options=['1', '2', '4', '8']
            ),
            ParameterSpec(
                name='enabled',
                label='Enabled',
                type='checkbox',
                default=True
            )
        ]
    
    @pytest.fixture
    def tab(self, qapp, simple_specs):
        """Create GenericHardwareConfigTab for testing."""
        return GenericHardwareConfigTab(
            title="Test Config",
            param_specs=simple_specs
        )
    
    def test_widget_creation(self, tab):
        """Test that widget is created correctly."""
        assert tab.title == "Test Config"
        assert len(tab._widgets) == 3
        assert 'freq_hz' in tab._widgets
        assert 'gain' in tab._widgets
        assert 'enabled' in tab._widgets
    
    def test_get_config(self, tab):
        """Test getting configuration."""
        config = tab.get_config()
        
        assert 'freq_hz' in config
        assert 'gain' in config
        assert 'enabled' in config
        assert config['freq_hz'] == 1000  # default
        assert config['gain'] == '1'  # default
        assert config['enabled'] is True  # default
    
    def test_set_config(self, tab):
        """Test setting configuration programmatically."""
        new_config = {
            'freq_hz': 5000,
            'gain': '4',
            'enabled': False
        }
        
        tab.set_config(new_config)
        config = tab.get_config()
        
        assert config['freq_hz'] == 5000
        assert config['gain'] == '4'
        assert config['enabled'] is False
    
    def test_validate_valid_config(self, tab):
        """Test validation of valid configuration."""
        tab.set_config({'freq_hz': 5000, 'gain': '2', 'enabled': True})
        
        is_valid, error = tab.validate()
        assert is_valid is True
        assert error is None
    
    def test_validate_invalid_config(self, tab):
        """Test validation of invalid configuration."""
        # Set freq_hz out of range
        tab.set_config({'freq_hz': 50000})  # > 10000
        
        is_valid, error = tab.validate()
        assert is_valid is False
        assert error is not None
    
    def test_config_changed_signal(self, tab, qtbot):
        """Test that config_changed signal is emitted."""
        with qtbot.waitSignal(tab.config_changed, timeout=1000) as blocker:
            # Change a value
            tab._widgets['freq_hz'].setValue(2000)
        
        # Check emitted config
        emitted_config = blocker.args[0]
        assert emitted_config['freq_hz'] == 2000
    
    def test_set_enabled(self, tab):
        """Test enabling/disabling all widgets."""
        tab.set_enabled(False)
        
        for widget in tab._widgets.values():
            assert widget.isEnabled() is False
        
        tab.set_enabled(True)
        
        for widget in tab._widgets.values():
            assert widget.isEnabled() is True
