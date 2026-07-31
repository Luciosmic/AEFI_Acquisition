"""
Dev launcher — same composition root as main.py, all hardware mocked.

Use this instead of editing main.py's default hardware_config: main.py ships
on `main` as the real-hardware launcher and should never need to "think
about" mocks.
"""
from main import main

if __name__ == "__main__":
    main(hardware_config={
        "motion": "mock",
        "aefi_device": "mock",
        "electric_field_probe": "mock",
    })
