"""
Tests package pour le backend AD9106/ADS131A04
"""

# Version des tests
__version__ = "1.0.0"

# Importation des modules de test
try:
    from . import test_1_imports
    from . import test_2_unit_mode_controller
    from . import test_2_unit_data_buffer
    from . import test_2_unit_adc_converter
    from . import test_2_unit_csv_exporter
except ImportError:
    # Les modules de test ne sont pas encore créés
    pass 