"""
Example: Using ExcitationAwareAcquisitionPort

This example demonstrates how to integrate the excitation-aware acquisition
mock service into the AEFI_Acquisition system.
"""

"""
Example: Using ExcitationAwareAcquisitionPort

Run from project root with:
    PYTHONPATH=src python src/infrastructure/mocks/example_excitation_aware_usage.py
"""

from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.mocks.adapter_mock_excitation_aware_acquisition import (
    ExcitationAwareAcquisitionPort,
    OffsetVector3D
)
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters
from domain.value_objects.excitation.excitation_mode import ExcitationMode
from domain.value_objects.excitation.excitation_level import ExcitationLevel


def example_basic_usage():
    """Basic usage example: X_DIR excitation with default offset."""
    print("=== Example 1: Basic Usage ===")
    
    # Create base acquisition port (generates random noise)
    base_port = RandomNoiseAcquisitionPort(noise_std=0.1, seed=42)
    
    # Create excitation port
    excitation_port = MockExcitationPort()
    
    # Create excitation-aware acquisition port
    aware_port = ExcitationAwareAcquisitionPort(
        base_acquisition_port=base_port,
        excitation_port=excitation_port,
        real_ratio=0.9,  # 90% real, 10% quadrature
        offset_scale=1.0
    )
    
    # Set X_DIR excitation at 100% level
    params = ExcitationParameters(
        mode=ExcitationMode.X_DIR,
        level=ExcitationLevel(100.0),
        frequency=1000.0
    )
    excitation_port.apply_excitation(params)
    
    # Acquire sample (offset will be applied automatically)
    measurement = aware_port.acquire_sample()
    
    print(f"X In-Phase: {measurement.voltage_x_in_phase:.3f} V")
    print(f"X Quadrature: {measurement.voltage_x_quadrature:.3f} V")
    print(f"Y In-Phase: {measurement.voltage_y_in_phase:.3f} V")
    print(f"Z In-Phase: {measurement.voltage_z_in_phase:.3f} V")
    print()


def example_y_dir_excitation():
    """Example: Y_DIR excitation (maps to Z offset)."""
    print("=== Example 2: Y_DIR Excitation ===")
    
    base_port = RandomNoiseAcquisitionPort(noise_std=0.1, seed=42)
    excitation_port = MockExcitationPort()
    aware_port = ExcitationAwareAcquisitionPort(base_port, excitation_port)
    
    # Set Y_DIR excitation
    params = ExcitationParameters(
        mode=ExcitationMode.Y_DIR,
        level=ExcitationLevel(100.0),
        frequency=1000.0
    )
    excitation_port.apply_excitation(params)
    
    # Acquire sample
    measurement = aware_port.acquire_sample()
    
    print(f"X In-Phase: {measurement.voltage_x_in_phase:.3f} V (should be ~0)")
    print(f"Y In-Phase: {measurement.voltage_y_in_phase:.3f} V (should be ~0)")
    print(f"Z In-Phase: {measurement.voltage_z_in_phase:.3f} V (should have offset)")
    print()


def example_custom_offset():
    """Example: Custom offset vector for excitation mode."""
    print("=== Example 3: Custom Offset Vector ===")
    
    base_port = RandomNoiseAcquisitionPort(noise_std=0.1, seed=42)
    excitation_port = MockExcitationPort()
    aware_port = ExcitationAwareAcquisitionPort(base_port, excitation_port)
    
    # Set custom offset for X_DIR mode
    custom_offset = OffsetVector3D(2.0, 1.0, 0.5)
    aware_port.set_excitation_offset(ExcitationMode.X_DIR, custom_offset)
    
    # Set X_DIR excitation
    params = ExcitationParameters(
        mode=ExcitationMode.X_DIR,
        level=ExcitationLevel(100.0),
        frequency=1000.0
    )
    excitation_port.apply_excitation(params)
    
    # Acquire sample
    measurement = aware_port.acquire_sample()
    
    print(f"X In-Phase: {measurement.voltage_x_in_phase:.3f} V (offset ~2.0)")
    print(f"Y In-Phase: {measurement.voltage_y_in_phase:.3f} V (offset ~1.0)")
    print(f"Z In-Phase: {measurement.voltage_z_in_phase:.3f} V (offset ~0.5)")
    print()


def example_real_ratio():
    """Example: Configuring real/quadrature ratio."""
    print("=== Example 4: Real/Quadrature Ratio ===")
    
    base_port = RandomNoiseAcquisitionPort(noise_std=0.1, seed=42)
    excitation_port = MockExcitationPort()
    aware_port = ExcitationAwareAcquisitionPort(base_port, excitation_port)
    
    # Set 50% real, 50% quadrature
    aware_port.set_real_ratio(0.5)
    
    # Set X_DIR excitation
    params = ExcitationParameters(
        mode=ExcitationMode.X_DIR,
        level=ExcitationLevel(100.0),
        frequency=1000.0
    )
    excitation_port.apply_excitation(params)
    
    # Acquire sample
    measurement = aware_port.acquire_sample()
    
    print(f"X In-Phase: {measurement.voltage_x_in_phase:.3f} V (50% of offset)")
    print(f"X Quadrature: {measurement.voltage_x_quadrature:.3f} V (50% of offset)")
    print()


def example_level_scaling():
    """Example: Excitation level scaling."""
    print("=== Example 5: Level Scaling ===")
    
    base_port = RandomNoiseAcquisitionPort(noise_std=0.1, seed=42)
    excitation_port = MockExcitationPort()
    aware_port = ExcitationAwareAcquisitionPort(base_port, excitation_port)
    
    # Set X_DIR excitation at 50% level
    params = ExcitationParameters(
        mode=ExcitationMode.X_DIR,
        level=ExcitationLevel(50.0),  # 50% level
        frequency=1000.0
    )
    excitation_port.apply_excitation(params)
    
    # Acquire sample
    measurement = aware_port.acquire_sample()
    
    print(f"X In-Phase: {measurement.voltage_x_in_phase:.3f} V (offset ~0.5)")
    print(f"50% level means 50% of the offset magnitude")
    print()


def example_separation_equalization():
    """Example: Using separation and equalization functions."""
    print("=== Example 6: Separation and Equalization ===")
    
    base_port = RandomNoiseAcquisitionPort(noise_std=0.1, seed=42)
    excitation_port = MockExcitationPort()
    aware_port = ExcitationAwareAcquisitionPort(base_port, excitation_port)
    
    # Set separation vector (adds to base offset)
    separation = OffsetVector3D(0.5, 0.5, 0.0)
    aware_port.set_separation_vector(ExcitationMode.X_DIR, separation)
    
    # Set equalization factor (scales offset)
    aware_port.set_equalization_factor(ExcitationMode.X_DIR, 0.5)
    
    # Set X_DIR excitation
    params = ExcitationParameters(
        mode=ExcitationMode.X_DIR,
        level=ExcitationLevel(100.0),
        frequency=1000.0
    )
    excitation_port.apply_excitation(params)
    
    # Acquire sample
    measurement = aware_port.acquire_sample()
    
    print(f"X In-Phase: {measurement.voltage_x_in_phase:.3f} V")
    print(f"Y In-Phase: {measurement.voltage_y_in_phase:.3f} V")
    print(f"Separation and equalization applied")
    print()


def example_integration_with_services():
    """Example: Integration with existing services."""
    print("=== Example 7: Integration with Services ===")
    
    from application.services.excitation_configuration_service.excitation_configuration_service import (
        ExcitationConfigurationService
    )
    
    # Create ports
    base_port = RandomNoiseAcquisitionPort(noise_std=0.1, seed=42)
    excitation_port = MockExcitationPort()
    aware_port = ExcitationAwareAcquisitionPort(base_port, excitation_port)
    
    # Create excitation service
    excitation_service = ExcitationConfigurationService(excitation_port)
    
    # Set excitation via service
    excitation_service.set_excitation(
        mode=ExcitationMode.X_DIR,
        level_percent=100.0,
        frequency=1000.0
    )
    
    # Acquire sample (offset applied automatically)
    measurement = aware_port.acquire_sample()
    
    print(f"Excitation set via service")
    print(f"X In-Phase: {measurement.voltage_x_in_phase:.3f} V")
    print()


if __name__ == "__main__":
    example_basic_usage()
    example_y_dir_excitation()
    example_custom_offset()
    example_real_ratio()
    example_level_scaling()
    example_separation_equalization()
    example_integration_with_services()
    
    print("=== All Examples Complete ===")

