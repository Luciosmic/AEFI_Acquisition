"""
Standalone Arcus Performax 4EX control UI (goes through application layer for config).

Responsibility:
- Let the user:
  - Connect to the Arcus controller
  - Home both axes
  - Adjust high speed (HSX / HSY)
  - Run a simple motion test

Rationale:
- Quickly run the real hardware while still using the application-level
  HardwareConfigurationService and ActionableHardwareParametersSpec.
"""

import sys
from pathlib import Path
from typing import Dict, Any

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
)

# Ensure src is on sys.path when running this file directly
ROOT = Path(__file__).parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from application.hardware_configuration_service.hardware_configuration_service import (
    HardwareConfigurationService,
)
from infrastructure.hardware.arcus_performax_4EX.adapter_arcus_performax4EX import (
    ArcusAdapter,
    ArcusPerformax4EXConfigProvider,
)
from domain.value_objects.geometric.position_2d import Position2D


class ArcusManualControlWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arcus Performax 4EX - Manual Control")
        self.resize(500, 300)

        # --- Application layer wiring ---
        provider = ArcusPerformax4EXConfigProvider()
        self.hw_config_service = HardwareConfigurationService([provider])
        specs = {
            spec.name: spec
            for spec in self.hw_config_service.get_parameter_specs("arcus_performax_4ex")
        }

        # --- Infrastructure adapter (motion) ---
        dll_dir = (
            SRC
            / "infrastructure"
            / "hardware"
            / "arcus_performax_4EX"
            / "DLL64"
        )
        self.adapter = ArcusAdapter(
            dll_path=str(dll_dir)  # uses same DLL folder as legacy test
        )

        # --- UI layout ---
        central = QWidget()
        layout = QVBoxLayout(central)
        self.setCentralWidget(central)

        # Status
        self.status_label = QLabel("Status: disconnected")
        layout.addWidget(self.status_label)

        # Connect button
        btn_connect = QPushButton("Connect to Arcus")
        btn_connect.clicked.connect(self._on_connect_clicked)
        layout.addWidget(btn_connect)

        # HS speed control (uses specs from application layer)
        hs_row = QHBoxLayout()
        hs_label = QLabel("High speed HSX/HSY [Hz]:")
        hs_row.addWidget(hs_label)

        self.hs_spin = QSpinBox()
        hs_spec = specs.get("x_hs")
        if hs_spec and hs_spec.value_range:
            self.hs_spin.setRange(int(hs_spec.value_range[0]), int(hs_spec.value_range[1]))
            self.hs_spin.setValue(int(hs_spec.default))
        else:
            self.hs_spin.setRange(10, 10000)
            self.hs_spin.setValue(1500)
        hs_row.addWidget(self.hs_spin)

        btn_apply_hs = QPushButton("Apply HS to X/Y")
        btn_apply_hs.clicked.connect(self._on_apply_hs_clicked)
        hs_row.addWidget(btn_apply_hs)

        layout.addLayout(hs_row)

        # Homing
        btn_home = QPushButton("Home X and Y")
        btn_home.clicked.connect(self._on_home_clicked)
        layout.addWidget(btn_home)

        # Test motion
        btn_test = QPushButton("Run test motion")
        btn_test.clicked.connect(self._on_test_motion_clicked)
        layout.addWidget(btn_test)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_connect_clicked(self):
        ok = self.adapter.connect()
        if ok:
            self.status_label.setText("Status: connected")
        else:
            self.status_label.setText("Status: connection FAILED (see console)")

    def _on_apply_hs_clicked(self):
        value = int(self.hs_spin.value())
        try:
            # Route through application layer so we exercise the full chain:
            # UI -> HardwareConfigurationService -> ArcusPerformax4EXConfigProvider
            self.hw_config_service.apply_config(
                "arcus_performax_4ex",
                {"hs": value},
            )
            self.status_label.setText(f"Status: HSX/HSY set to {value} Hz")
        except Exception as e:
            print(f"[ArcusManualControl] Failed to apply HS: {e}")
            self.status_label.setText("Status: HS apply FAILED")

    def _on_home_clicked(self):
        try:
            # Use application path for homing as well
            self.hw_config_service.apply_config(
                "arcus_performax_4ex",
                {"home_both_axes": True},
            )
            self.status_label.setText("Status: homing X/Y in progress...")
        except Exception as e:
            print(f"[ArcusManualControl] Homing failed: {e}")
            self.status_label.setText("Status: homing FAILED")

    def _on_test_motion_clicked(self):
        """
        Simple test:
        - Move to (1000, 0)
        - Wait
        - Move to (0, 1000)
        - Wait
        - Return to (0, 0)
        """
        try:
            self.status_label.setText("Status: running test motion...")
            # small displacements; adjust to safe values for your setup
            points = [
                Position2D(x=1000, y=0),
                Position2D(x=0, y=1000),
                Position2D(x=0, y=0),
            ]
            for p in points:
                self.adapter.move_to(p)
                self.adapter.wait_until_stopped(timeout=30.0)

            self.status_label.setText("Status: test motion DONE")
        except Exception as e:
            print(f"[ArcusManualControl] Test motion failed: {e}")
            self.status_label.setText("Status: test motion FAILED")


def main():
    app = QApplication(sys.argv)
    window = ArcusManualControlWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


