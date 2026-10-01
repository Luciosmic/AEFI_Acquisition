from domain.calibration.value_objects.hardware_component_name.hardware_component_name import (
    HardwareComponentName,
)


def test_is_a_plain_string_at_runtime():
    name = HardwareComponentName("Final_v4_ASSOCE")
    assert name == "Final_v4_ASSOCE"
    assert isinstance(name, str)
