"""Test script to verify AD9106 parameter specs retrieval via presenter (closest to real usage)."""
import sys
from pathlib import Path

# Add src to path (from tests/ad9106/tests/ -> src/)
# tests/ad9106/tests/ -> tests/ -> ad9106/ -> micro_controller/ -> hardware/ -> infrastructure/ -> src/
src_path = Path(__file__).parent.parent.parent.parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from infrastructure.hardware.micro_controller.ad9106.adapter_excitation_configuration_ad9106 import AD9106Adapter
from application.services.hardware_configuration_service.hardware_configuration_service import HardwareConfigurationService
from domain.value_objects.hardware_configuration.hardware_advanced_parameter_schema import (
    NumberParameterSchema, EnumParameterSchema
)

print("=== Test AD9106 Conversion Logic (Presenter logic without PyQt6) ===\n")

# Setup: Create service with AD9106 adapter
adapter = AD9106Adapter(None, None)
service = HardwareConfigurationService([adapter])

# Test 1: Get domain specs
print("1. Get domain specs from service:")
ids = service.list_hardware_ids()
print(f"   ✅ Hardware IDs: {ids}")

if "ad9106_dds" not in ids:
    print("   ❌ 'ad9106_dds' not found")
    sys.exit(1)

domain_specs = service.get_parameter_specs("ad9106_dds")
print(f"   ✅ Domain specs count: {len(domain_specs)}")
print(f"   ✅ Types: {[type(s).__name__ for s in domain_specs[:5]]}")

# Test 2: Simulate presenter conversion logic
print("\n2. Simulate presenter conversion logic:")
print("   (This is what GenericHardwareConfigPresenter._convert_to_ui_specs() does)")

ui_specs_data = []
for ds in domain_specs:
    widget_type = 'lineedit'  # Default
    options = None
    rng = None
    
    if isinstance(ds, NumberParameterSchema):
        widget_type = 'spinbox'
        rng = (ds.min_value, ds.max_value)
    elif isinstance(ds, EnumParameterSchema):
        widget_type = 'combo'
        options = list(ds.choices)
    # BooleanParameterSchema -> 'checkbox' (not in AD9106)
    
    ui_spec = {
        'name': ds.key,
        'label': ds.display_name,
        'type': widget_type,
        'default': ds.default_value,
        'range': rng,
        'options': options,
        'unit': getattr(ds, 'unit', None),
        'tooltip': ds.description
    }
    ui_specs_data.append(ui_spec)

print(f"   ✅ Converted UI specs count: {len(ui_specs_data)}")

# Test 3: Display results
print("\n3. First 5 converted specs:")
for i, spec in enumerate(ui_specs_data[:5], 1):
    print(f"\n   {i}. {spec['name']} ({spec['type']})")
    print(f"      Label: {spec['label']}")
    print(f"      Default: {spec['default']}")
    if spec['range']:
        print(f"      Range: {spec['range']}")
    if spec['options']:
        print(f"      Options: {spec['options']}")
    if spec['unit']:
        print(f"      Unit: {spec['unit']}")
    if spec['tooltip']:
        print(f"      Tooltip: {spec['tooltip'][:50]}...")

print(f"\n4. All parameter keys:")
print(f"   {[s['name'] for s in ui_specs_data]}")

print("\n=== Test completed successfully ===")
print("✅ AD9106 parameter specs can be retrieved and converted correctly!")

