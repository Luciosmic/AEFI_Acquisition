"""Le double d'excitation tient le port IExcitationPort et garde en mémoire la dernière excitation appliquée."""
from application.shared.excitation_configuration_service.ports.i_excitation_port import IExcitationPort
from domain.shared_kernel.excitation.value_objects.excitation_level import ExcitationLevel
from domain.shared_kernel.excitation.value_objects.excitation_parameters import ExcitationParameters
from infrastructure.hardware.ad9106.adapter_excitation_configuration_ad9106.fake.fake_adapter_excitation_configuration_ad9106 import (
    MockExcitationPort,
)


def test_le_double_tient_le_port_et_retient_la_derniere_excitation():
    port = MockExcitationPort()
    params = ExcitationParameters.off()
    port.apply_excitation(params)
    assert isinstance(port, IExcitationPort)
    assert port.last_parameters == params


def test_le_gain_sans_excitation_appliquee_ne_change_rien_puis_remplace_les_niveaux():
    port = MockExcitationPort()
    port.set_gain(10.0, 20.0)
    assert port.last_parameters is None
    port.apply_excitation(ExcitationParameters.off())
    port.set_gain(10.0, 20.0)
    assert port.last_parameters.level_s1_s2 == ExcitationLevel(10.0)
    assert port.last_parameters.level_s3_s4 == ExcitationLevel(20.0)


def test_le_lien_des_deux_generateurs_se_retient():
    port = MockExcitationPort()
    port.set_link_dds1_dds2(False)
    assert port.linked is False
