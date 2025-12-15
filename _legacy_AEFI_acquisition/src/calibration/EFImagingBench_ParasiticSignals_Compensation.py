#!/usr/bin/env python3
"""
Compensation des signaux parasites électroniques.

Objectif : Soustraire les offsets caractérisés lors de l'affichage.
"""

import os
import json
import numpy as np
from typing import Dict, Optional, List

class ParasiticSignalsCompensator:
    def __init__(self, calibration_file=None):
        """
        Initialise le compensateur d'offsets
        Args:
            calibration_file: Fichier JSON de caractérisation (auto-détecté si None)
        """
        self.calibration_data = None
        self.frequencies = []
        
        if calibration_file is None:
            # Recherche auto du dernier fichier de calibration
            calibration_dir = os.path.join(os.path.dirname(__file__), 'data')
            json_files = [f for f in os.listdir(calibration_dir) if f.endswith('_parasitic_signals_characterization.json')]
            
            if not json_files:
                raise FileNotFoundError("Aucun fichier de calibration trouvé")
            
            calibration_file = os.path.join(calibration_dir, sorted(json_files)[-1])
        
        # Chargement du fichier
        with open(calibration_file, 'r') as f:
            full_data = json.load(f)
        
        self.calibration_data = full_data['results']
        self.frequencies = [r['frequency_hz'] for r in self.calibration_data]
    
    def _interpolate_offset(self, channel: str, frequency: float) -> float:
        """
        Interpolation linéaire de l'offset à une fréquence donnée
        Args:
            channel: Canal à compenser (ex: 'adc1_ch1')
            frequency: Fréquence courante
        Returns:
            Offset interpolé
        """
        if not self.calibration_data:
            return 0.0
        
        # Filtrer les résultats pour ce canal
        channel_data = [
            (r['frequency_hz'], r['channels'][channel]['mean']) 
            for r in self.calibration_data 
            if channel in r.get('channels', {})
        ]
        
        if not channel_data:
            return 0.0
        
        # Tri par fréquence
        channel_data.sort(key=lambda x: x[0])
        
        # Cas limites
        if frequency <= channel_data[0][0]:
            return channel_data[0][1]
        if frequency >= channel_data[-1][0]:
            return channel_data[-1][1]
        
        # Interpolation
        for i in range(len(channel_data) - 1):
            f1, offset1 = channel_data[i]
            f2, offset2 = channel_data[i+1]
            
            if f1 <= frequency <= f2:
                # Interpolation linéaire
                return offset1 + (offset2 - offset1) * (frequency - f1) / (f2 - f1)
        
        return 0.0
    
    def compensate_sample(self, sample, current_frequency: float):
        """
        Compense un échantillon avec les offsets caractérisés
        Args:
            sample: Échantillon à compenser
            current_frequency: Fréquence courante
        Returns:
            Échantillon compensé
        """
        # Canaux principaux à compenser
        channels_to_compensate = [
            'adc1_ch1', 'adc1_ch2',  # Ex I/Q
            'adc1_ch3', 'adc1_ch4',  # Ey I/Q
            'adc2_ch1', 'adc2_ch2'   # Ez I/Q
        ]
        
        # Copie de l'échantillon
        compensated_sample = sample.copy()
        
        for channel in channels_to_compensate:
            offset = self._interpolate_offset(channel, current_frequency)
            
            # Soustraction de l'offset
            setattr(compensated_sample, channel, 
                    getattr(compensated_sample, channel) - int(round(offset)))
        
        return compensated_sample

def main():
    """Test rapide du module de compensation"""
    try:
        compensator = ParasiticSignalsCompensator()
        print("✅ Compensateur initialisé")
        print(f"📊 Fréquences calibrées : {len(compensator.frequencies)} points")
        print(f"   Plage : {min(compensator.frequencies)} - {max(compensator.frequencies)} Hz")
    except Exception as e:
        print(f"❌ Erreur initialisation : {e}")

if __name__ == "__main__":
    main() 