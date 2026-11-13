"""Le double de configurateur avancé tient le port et expose des paramètres représentatifs du matériel réel."""
from application.shared.hardware_configuration_service.ports.i_hardware_advanced_configurator import (
    IHardwareAdvancedConfigurator,
)
from infrastructure.hardware.micro_controller.mcu_advanced_configurator.fake.fake_mcu_advanced_configurator import (
    MockHardwareAdvancedConfigurator,
)


def test_le_double_tient_le_port_et_expose_les_six_paramettres_representatifs() -> None:
    configurator = MockHardwareAdvancedConfigurator()
    assert isinstance(configurator, IHardwareAdvancedConfigurator)
    keys = {spec.key for spec in configurator.get_parameter_specs()}
    assert keys == {
        "n_avg",
        "high_resolution",
        "negative_charge_pump",
        "reference_voltage",
        "reference_source",
        "oversampling_ratio",
    }


def test_appliquer_une_configuration_la_retient() -> None:
    configurator = MockHardwareAdvancedConfigurator()
    configurator.apply_config({"n_avg": 8})
    assert configurator.last_config == {"n_avg": 8}
    assert configurator.applied_params["n_avg"] == 8


def test_revenir_aux_valeurs_par_defaut_applique_les_valeurs_par_defaut_des_specs() -> None:
    configurator = MockHardwareAdvancedConfigurator()
    configurator.apply_config({"n_avg": 8})
    configurator.reset_to_default()
    assert configurator.last_config["n_avg"] == 1
