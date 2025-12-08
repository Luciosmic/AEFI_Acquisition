#!/usr/bin/env python3
"""
ADC Converter - Conversion codes ADC vers tensions avec facteur V to V/m
Adapté pour ADS131A04
Adapté pour le banc d'imagerie électrique en champ proche

Gère la conversion des codes ADC bruts vers différentes unités :
- Codes ADC bruts
- Tensions (V, mV, µV)  
- Champ électrique (V/m) avec facteur configurable
"""

import logging
from typing import Dict, List, Optional, Union
from enum import Enum
from dataclasses import dataclass


class ADCUnit(Enum):
    """Unités de conversion supportées"""
    CODES_ADC = "codes_adc"
    VOLTS = "V"
    MILLIVOLTS = "mV"
    MICROVOLTS = "µV"
    VOLTS_PER_METER = "V/m"


@dataclass
class ConvertedSample:
    """Échantillon converti avec unités"""
    adc1_ch1: float
    adc1_ch2: float
    adc1_ch3: float
    adc1_ch4: float
    adc2_ch1: float
    adc2_ch2: float
    adc2_ch3: float
    adc2_ch4: float
    unit: ADCUnit


class ADCConverter:
    """
    Convertisseur ADC avec facteurs de gain et unités multiples
    Responsabilités :
    - Conversion codes ADC → tensions selon gain
    - Application facteur V to V/m configurable
    - Support unités multiples
    - Cache pour performance
    """

    # --- Propriétés internes ---
    CONVERSION_FACTORS = {
        1: 4.76837E-7,   # ±4.0V
        2: 2.38419E-7,   # ±2.0V
        4: 1.19209E-7,   # ±1.0V
        8: 5.96046E-8,   # ±0.5V
        16: 2.98023E-8   # ±0.25V
    }

    def __init__(self, v_to_vm_factor: float = 63600.0):
        """
        Initialisation du convertisseur
        Args:
            v_to_vm_factor: Facteur de conversion V vers V/m
        """
        self.logger = logging.getLogger(__name__)
        self.v_to_vm_factor = v_to_vm_factor
        self._conversion_cache = {}
        self._channel_gains = {
            1: 1, 2: 1, 3: 1, 4: 1,  # ADC1 canaux 1-4
            5: 1, 6: 1, 7: 1, 8: 1   # ADC2 canaux 1-4 (numérotés 5-8)
        }
        self.logger.info("ADCConverter initialisé")

    # --- API Publique ---
    def set_channel_gains(self, gains: Dict[int, int]):
        """
        Configure les gains des canaux ADC
        Args:
            gains: Dict {channel: gain} avec channel 1-8 et gain 1,2,4,8,16
        """
        for channel, gain in gains.items():
            if channel not in range(1, 9):
                self.logger.warning(f"Canal invalide: {channel}")
                continue
            if gain not in self.CONVERSION_FACTORS:
                self.logger.warning(f"Gain invalide pour canal {channel}: {gain}")
                continue
            self._channel_gains[channel] = gain
        self._conversion_cache.clear()
        self.logger.debug(f"Gains mis à jour: {self._channel_gains}")

    def set_v_to_vm_factor(self, factor: float):
        """Change le facteur V to V/m"""
        if factor <= 0:
            self.logger.warning(f"Facteur V to V/m invalide: {factor}")
            return
        self.v_to_vm_factor = factor
        self._conversion_cache.clear()
        self.logger.info(f"Facteur V to V/m mis à jour: {factor}")

    def convert_sample(self, sample, gains: Dict[str, int], target_unit: ADCUnit) -> ConvertedSample:
        """
        Convertit un échantillon selon les gains et unité cible
        Args:
            sample: AcquisitionSample à convertir
            gains: Dictionnaire des gains par canal
            target_unit: Unité cible
        Returns:
            ConvertedSample avec valeurs converties
        """
        # Stub minimal - conversion basique
        if target_unit == ADCUnit.CODES_ADC:
            return ConvertedSample(
                adc1_ch1=float(sample.adc1_ch1),
                adc1_ch2=float(sample.adc1_ch2),
                adc1_ch3=float(sample.adc1_ch3),
                adc1_ch4=float(sample.adc1_ch4),
                adc2_ch1=float(sample.adc2_ch1),
                adc2_ch2=float(sample.adc2_ch2),
                adc2_ch3=float(sample.adc2_ch3),
                adc2_ch4=float(sample.adc2_ch4),
                unit=target_unit
            )
        factor = self.CONVERSION_FACTORS.get(gains.get('adc1_gain', 1), self.CONVERSION_FACTORS[1])
        v1 = sample.adc1_ch1 * factor
        v2 = sample.adc1_ch2 * factor
        v3 = sample.adc1_ch3 * factor
        v4 = sample.adc1_ch4 * factor
        v5 = sample.adc2_ch1 * factor
        v6 = sample.adc2_ch2 * factor
        v7 = sample.adc2_ch3 * factor
        v8 = sample.adc2_ch4 * factor
        if target_unit == ADCUnit.VOLTS:
            multiplier = 1.0
        elif target_unit == ADCUnit.MILLIVOLTS:
            multiplier = 1000.0
        elif target_unit == ADCUnit.MICROVOLTS:
            multiplier = 1000000.0
        elif target_unit == ADCUnit.VOLTS_PER_METER:
            multiplier = self.v_to_vm_factor
        else:
            multiplier = 1.0
        return ConvertedSample(
            adc1_ch1=v1 * multiplier,
            adc1_ch2=v2 * multiplier,
            adc1_ch3=v3 * multiplier,
            adc1_ch4=v4 * multiplier,
            adc2_ch1=v5 * multiplier,
            adc2_ch2=v6 * multiplier,
            adc2_ch3=v7 * multiplier,
            adc2_ch4=v8 * multiplier,
            unit=target_unit
        )

    def convert_adc_to_voltage(self, adc_code: int, channel: int) -> Optional[float]:
        """
        Convertit un code ADC en tension (section 4.2 de la todo)
        Args:
            adc_code: Code ADC brut
            channel: Numéro de canal (1-8)
        Returns:
            Tension en volts ou None si erreur
        """
        if channel not in self._channel_gains:
            self.logger.error(f"Canal inconnu: {channel}")
            return None
        gain = self._channel_gains[channel]
        cache_key = (adc_code, gain)
        if cache_key in self._conversion_cache:
            return self._conversion_cache[cache_key]
        try:
            conversion_factor = self.CONVERSION_FACTORS[gain]
            voltage = adc_code * conversion_factor
            min_v, max_v = self.get_voltage_range(gain)
            if not (min_v <= voltage <= max_v):
                self.logger.warning(f"Tension hors range pour canal {channel}: {voltage}V (range: {min_v} à {max_v}V)")
            self._conversion_cache[cache_key] = voltage
            return voltage
        except Exception as e:
            self.logger.error(f"Erreur conversion ADC canal {channel}: {e}")
            return None

    def convert_channel_array(self, adc_codes: List[int], start_channel: int = 1) -> List[Optional[float]]:
        """
        Convertit un array de codes ADC en tensions
        Args:
            adc_codes: Liste des codes ADC
            start_channel: Premier numéro de canal (1 pour ADC1, 5 pour ADC2)
        Returns:
            Liste des tensions en volts
        """
        voltages = []
        for i, code in enumerate(adc_codes):
            channel = start_channel + i
            voltage = self.convert_adc_to_voltage(code, channel)
            voltages.append(voltage)
        return voltages

    def convert_to_units(self, voltage: float, target_units: ADCUnit) -> Optional[float]:
        """
        Convertit une tension vers les unités demandées
        Args:
            voltage: Tension en volts
            target_units: Unités de sortie
        Returns:
            Valeur convertie ou None si erreur
        """
        if voltage is None:
            return None
        try:
            if target_units == ADCUnit.VOLTS:
                return voltage
            elif target_units == ADCUnit.MILLIVOLTS:
                return voltage * 1000.0
            elif target_units == ADCUnit.MICROVOLTS:
                return voltage * 1000000.0
            elif target_units == ADCUnit.VOLTS_PER_METER:
                return voltage * self.v_to_vm_factor
            elif target_units == ADCUnit.CODES_ADC:
                gain = self._channel_gains[1]
                factor = self.CONVERSION_FACTORS[gain]
                return int(voltage / factor)
            else:
                self.logger.error(f"Unités non supportées: {target_units}")
                return None
        except Exception as e:
            self.logger.error(f"Erreur conversion unités: {e}")
            return None

    def convert_full_acquisition(self, adc1_data: List[int], adc2_data: List[int], 
                               target_units: ADCUnit = ADCUnit.VOLTS) -> Dict[str, List[Optional[float]]]:
        """
        Convertit une acquisition complète (8 canaux)
        Args:
            adc1_data: 4 codes ADC1 (canaux 1-4)
            adc2_data: 4 codes ADC2 (canaux 5-8)
            target_units: Unités de sortie
        Returns:
            Dict avec "adc1" et "adc2" contenant les valeurs converties
        """
        adc1_voltages = self.convert_channel_array(adc1_data, start_channel=1)
        adc2_voltages = self.convert_channel_array(adc2_data, start_channel=5)
        if target_units != ADCUnit.VOLTS:
            adc1_converted = [self.convert_to_units(v, target_units) for v in adc1_voltages]
            adc2_converted = [self.convert_to_units(v, target_units) for v in adc2_voltages]
        else:
            adc1_converted = adc1_voltages
            adc2_converted = adc2_voltages
        return {
            "adc1": adc1_converted,
            "adc2": adc2_converted
        }

    def get_voltage_range(self, gain: int) -> tuple:
        """Retourne la plage de tension pour un gain donné"""
        if gain == 1:
            return (-4.0, 4.0)
        elif gain == 2:
            return (-2.0, 2.0)
        elif gain == 4:
            return (-1.0, 1.0)
        elif gain == 8:
            return (-0.5, 0.5)
        elif gain == 16:
            return (-0.25, 0.25)
        else:
            return (-4.0, 4.0)  # Par défaut

    def get_channel_info(self, channel: int) -> Dict[str, Union[int, float, tuple]]:
        """
        Retourne les informations d'un canal
        Args:
            channel: Numéro de canal (1-8)
        Returns:
            Dict avec gain, facteur conversion, range tension
        """
        if channel not in self._channel_gains:
            return {}
        gain = self._channel_gains[channel]
        return {
            "channel": channel,
            "gain": gain,
            "conversion_factor": self.CONVERSION_FACTORS[gain],
            "voltage_range": self.get_voltage_range(gain),
            "adc_type": "ADC1" if channel <= 4 else "ADC2"
        }

    def get_all_channels_info(self) -> Dict[int, Dict]:
        """Retourne les informations de tous les canaux"""
        return {ch: self.get_channel_info(ch) for ch in range(1, 9)}

    @property
    def channel_gains(self) -> Dict[int, int]:
        """Gains actuels par canal"""
        return self._channel_gains.copy()

    def clear_cache(self):
        """Vide le cache de conversion"""
        self._conversion_cache.clear()
        self.logger.debug("Cache de conversion vidé") 

    # --- Méthodes internes ---
    # (aucune méthode interne supplémentaire à déplacer ici pour l'instant)

    # --- Propriétés internes ---
    # self._conversion_cache, self._channel_gains, self.logger, self.v_to_vm_factor
    # (déjà initialisées dans __init__) 