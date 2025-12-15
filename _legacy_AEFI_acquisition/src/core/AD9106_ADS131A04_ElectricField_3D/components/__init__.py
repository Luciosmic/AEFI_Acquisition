"""
Backend Components pour Interface AD9106/ADS131A04

Architecture backend complète pour gestion des 2 modes d'acquisition :
- Mode Temps Réel (EXPLORATION) : Interface réactive avec pause/reprise
- Mode Export (EXPORT) : Interface verrouillée pour mesures scientifiques
"""

__version__ = "1.0.0"
__author__ = "Assistant IA - Banc d'acquisition champ électrique"

# Import des classes principales (avec gestion d'erreur pour développement incrémental)

__all__ = []

try:
    from .AD9106_ADS131A04_DataBuffer_Module import AcquisitionSample, CircularBuffer, ProductionBuffer, AdaptiveDataBuffer
    __all__.extend(['AcquisitionSample', 'CircularBuffer', 'ProductionBuffer', 'AdaptiveDataBuffer'])
except ImportError:
    pass

try:
    from .ADS131A04_Converter_Module import ADCConverter, ADCUnit
    __all__.extend(['ADCConverter', 'ADCUnit'])
except ImportError:
    pass

try:
    from .AD9106_ADS131A04_CSVexporter_Module import CSVExporter
    __all__.extend(['CSVExporter'])
except ImportError:
    pass

try:
    from .AD9106_ADS131A04_acquisition_manager import AcquisitionManager
    __all__.extend(['AcquisitionManager'])
except ImportError:
    pass

