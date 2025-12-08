"""
Module de configuration d'excitation pour le banc EFImagingBench
- Gère les modes d'excitation (X, Y, circulaires, off)
- Calcule les configurations DDS correspondantes
- API publique via MetaManager
"""

from typing import Dict, Any

class ExcitationConfig:
    """Configuration d'excitation avec mapping modes → paramètres DDS"""
    
    # Mapping des modes vers leurs configurations
    MODE_CONFIGS = {
        "off": {
            'gain_dds1': 0,
            'gain_dds2': 0,
            'gain_dds': 0,
            'phase_dds1': 0,
            'phase_dds2': 0
        },
        "ydir": {
            'gain_dds1': 5000,
            'gain_dds2': 5000,
            'gain_dds': 5000,
            'phase_dds1': 0,
            'phase_dds2': 0
        },
        "xdir": {
            'gain_dds1': 5000,
            'gain_dds2': 5000,
            'gain_dds': 5000,
            'phase_dds1': 0,
            'phase_dds2': 32768
        },
        "circ+": {
            'gain_dds1': 5000,
            'gain_dds2': 5000,
            'gain_dds': 5000,
            'phase_dds1': 0,
            'phase_dds2': 16384
        },
        "circ-": {
            'gain_dds1': 5000,
            'gain_dds2': 5000,
            'gain_dds': 5000,
            'phase_dds1': 0,
            'phase_dds2': 49152
        },
        "custom": {}  # Aucune modification
    }
    
    @classmethod
    def get_config(cls, mode: str) -> Dict[str, Any]:
        """Retourne la configuration complète pour un mode donné"""
        return cls.MODE_CONFIGS.get(mode, {})
    
    @classmethod
    def detect_mode(cls, config: Dict[str, Any]) -> str:
        """Détecte le mode d'excitation à partir d'une configuration"""
        
        # Extraction des paramètres
        gain_dds1 = config.get('gain_dds1', config.get('gain_dds', 0))
        gain_dds2 = config.get('gain_dds2', config.get('gain_dds', 0))
        phase_dds1 = config.get('phase_dds1', 0)
        phase_dds2 = config.get('phase_dds2', 0)
        
        # Mode OFF
        if gain_dds1 == 0 and gain_dds2 == 0:
            return "off"
        
        # Modes actifs
        if gain_dds1 > 0 and gain_dds2 > 0:
            if phase_dds1 == 0 and phase_dds2 == 0:
                return "ydir"
            elif phase_dds1 == 0 and phase_dds2 == 32768:
                return "xdir"
            elif phase_dds1 == 0 and phase_dds2 == 16384:
                return "circ+"
            elif phase_dds1 == 0 and phase_dds2 == 49152:
                return "circ-"
        
        return "custom"
