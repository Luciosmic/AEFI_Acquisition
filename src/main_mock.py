"""
Dev launcher — same composition root as interface/main.py, all hardware mocked.

Use this instead of editing interface/main.py's default hardware_config: it ships
on `main` as the real-hardware launcher and should never need to "think
about" mocks.
"""
from interface.main import main

if __name__ == "__main__":
    main(hardware_config={
        "motion": "mock",
        "aefi_device": "mock",
        "electric_field_probe": "mock",
        "inertial_probe": "mock",
        "oscilloscope": "mock",
    })
