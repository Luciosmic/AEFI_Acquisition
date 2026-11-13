"""Le double d'initialisation matérielle tient le port IHardwareInitializationPort sans toucher de matériel."""
from application.shared.system_lifecycle_service.ports.i_hardware_initialization_port import (
    IHardwareInitializationPort,
)
from infrastructure.hardware.micro_controller.adapter_lifecycle_mcu.fake.fake_adapter_lifecycle_mcu import (
    MockHardwareInitializationPort,
)


def test_initialiser_puis_fermer_bascule_les_drapeaux_et_rend_les_doubles_de_mouvement_et_d_acquisition() -> None:
    port = MockHardwareInitializationPort()
    assert isinstance(port, IHardwareInitializationPort)
    hardware = port.initialize_all()
    assert port.initialized and not port.closed
    assert set(hardware) == {"mock_motion", "mock_acquisition"}
    port.close_all()
    assert port.closed and not port.initialized


def test_la_verification_passe_toujours() -> None:
    assert MockHardwareInitializationPort().verify_all() is True
