import sys
import os

# Ajout dynamique du dossier racine au sys.path si nécessaire
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from getE3D.interface.components import ADS131A04_Converter_Module

# Utilisation des classes du module
ADCConverter = ADS131A04_Converter_Module.ADCConverter
ADCUnit = ADS131A04_Converter_Module.ADCUnit


def test_convert_adc_to_voltage_basic():
    conv = ADCConverter()
    # Code ADC nul doit donner 0V
    assert conv.convert_adc_to_voltage(0, 1) == 0.0
    # Code ADC positif, gain 1
    assert pytest.approx(conv.convert_adc_to_voltage(1000000, 1), rel=1e-6) == 1000000 * conv.CONVERSION_FACTORS[1]
    # Code ADC négatif, gain 2
    conv.set_channel_gains({2: 2})
    assert pytest.approx(conv.convert_adc_to_voltage(-500000, 2), rel=1e-6) == -500000 * conv.CONVERSION_FACTORS[2]


def test_convert_channel_array():
    conv = ADCConverter()
    # 4 codes ADC, canaux 1 à 4
    codes = [0, 100, -100, 8388607]
    voltages = conv.convert_channel_array(codes, start_channel=1)
    assert voltages[0] == 0.0
    assert pytest.approx(voltages[1], rel=1e-6) == 100 * conv.CONVERSION_FACTORS[1]
    assert pytest.approx(voltages[2], rel=1e-6) == -100 * conv.CONVERSION_FACTORS[1]
    # Test valeur max
    assert voltages[3] <= conv.get_voltage_range(1)[1]


def test_convert_to_units():
    conv = ADCConverter()
    v = 1.0  # 1V
    assert conv.convert_to_units(v, ADCUnit.VOLTS) == 1.0
    assert conv.convert_to_units(v, ADCUnit.MILLIVOLTS) == 1000.0
    assert conv.convert_to_units(v, ADCUnit.MICROVOLTS) == 1e6
    assert conv.convert_to_units(v, ADCUnit.VOLTS_PER_METER) == pytest.approx(1.0 * conv.v_to_vm_factor)


def test_convert_full_acquisition():
    conv = ADCConverter()
    adc1 = [0, 1, -1, 100]
    adc2 = [10, 20, 30, 40]
    result = conv.convert_full_acquisition(adc1, adc2, target_units=ADCUnit.VOLTS)
    assert isinstance(result, dict)
    assert len(result['adc1']) == 4
    assert len(result['adc2']) == 4
    # Test conversion d'une valeur
    assert pytest.approx(result['adc1'][1], rel=1e-6) == 1 * conv.CONVERSION_FACTORS[1]


def test_set_channel_gains_and_error():
    conv = ADCConverter()
    # Gain invalide
    conv.set_channel_gains({1: 99})  # Doit ignorer
    assert conv.channel_gains[1] == 1
    # Canal invalide
    conv.set_channel_gains({9: 2})  # Doit ignorer
    assert 9 not in conv.channel_gains
    # Gain valide
    conv.set_channel_gains({3: 4})
    assert conv.channel_gains[3] == 4


def test_convert_adc_to_voltage_channel_error():
    conv = ADCConverter()
    # Canal inconnu
    assert conv.convert_adc_to_voltage(123, 99) is None


if __name__ == "__main__":
    import pytest
    pytest.main([__file__]) 