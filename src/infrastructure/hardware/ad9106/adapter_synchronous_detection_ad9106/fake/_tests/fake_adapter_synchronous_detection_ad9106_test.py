"""Le double de détection synchrone tient le port et rejoue la persistance manuelle du registre de phase."""
from application.test_bench_calibration.synchronous_detection_service.ports.i_synchronous_detection_hardware_port import (
    ISynchronousDetectionHardwarePort,
)
from infrastructure.hardware.ad9106.adapter_synchronous_detection_ad9106.fake.fake_adapter_synchronous_detection_ad9106 import (
    MockSynchronousDetectionHardwarePort,
)


def test_le_double_tient_le_port_et_expose_ses_registres():
    port = MockSynchronousDetectionHardwarePort()
    assert isinstance(port, ISynchronousDetectionHardwarePort)
    assert port.get_all_channel_phase_registers() == {1: 0, 2: 32768, 3: 16384, 4: 0}


def test_un_registre_persiste_devient_la_base_de_la_restauration_manuelle():
    port = MockSynchronousDetectionHardwarePort()
    port.set_ch3_phase_register(1234, persist=True)
    port.set_ch3_phase_register(99)
    port.restore_manual_configuration()
    assert port.get_all_channel_phase_registers()[3] == 1234
    assert port.restore_manual_configuration_calls == 1


def test_la_restauration_sans_base_enregistree_ne_change_rien():
    port = MockSynchronousDetectionHardwarePort()
    port.restore_manual_configuration()
    assert port.get_all_channel_phase_registers()[3] == 16384
