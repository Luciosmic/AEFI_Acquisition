"""Les doubles d'acquisition tiennent le port IAcquisitionPort et se comportent comme leur intention le dit."""
import pytest

from application.shared.ports.i_acquisition_port import IAcquisitionPort
from infrastructure.hardware.ads131a04.adapter_i_acquistion_port_ads131a04.fake.fake_adapter_i_acquistion_port_ads131a04 import (
    MockAcquisitionPort,
    RandomNoiseAcquisitionPort,
)


def test_le_double_synthetique_tient_le_port_et_numerote_ses_echantillons() -> None:
    port = MockAcquisitionPort()
    first = port.acquire_sample()
    second = port.acquire_sample()
    assert isinstance(port, IAcquisitionPort)
    assert port.acquire_count == 2
    assert second.voltage_x_in_phase == pytest.approx(2 * first.voltage_x_in_phase)
    assert port.is_ready()


def test_le_double_bruite_rejoue_la_meme_suite_avec_la_meme_graine() -> None:
    a = RandomNoiseAcquisitionPort(noise_std=0.5, seed=7)
    b = RandomNoiseAcquisitionPort(noise_std=0.5, seed=7)
    assert isinstance(a, IAcquisitionPort)
    assert a.acquire_sample().voltage_x_in_phase == b.acquire_sample().voltage_x_in_phase
    assert a.get_quantification_noise() == 0.5
