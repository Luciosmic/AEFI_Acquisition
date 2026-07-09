"""
Root conftest.py — pytest collection configuration.

Catégorie d'exclusion :
1. TESTS HARDWARE : nécessitent une connexion matérielle physique.
   Exclus de la collection car leurs imports échouent ou ils tentent
   une connexion réelle. À réactiver quand le matériel est branché.
"""

# -- Tests hardware (connexion matérielle physique requise) ----------------------
# Arcus Performax 4EX
_ARCUS_HARDWARE = [
    "src/infrastructure/hardware/arcus_performax_4EX/_tests/adapter_arcus_performax4EX_test.py",
    "src/infrastructure/hardware/arcus_performax_4EX/_tests/arcus_composition_root_sequence_test.py",
    "src/infrastructure/hardware/arcus_performax_4EX/_tests/arcus_hardware_movement_test.py",
    "src/infrastructure/hardware/arcus_performax_4EX/_tests/lifecycle_initialization_test.py",
]
# ADS131A04 ADC
_ADS_HARDWARE = [
    "src/infrastructure/hardware/micro_controller/ads131a04/_tests/adapter_ads131a04_test.py",
    "src/infrastructure/hardware/micro_controller/ads131a04/_tests/acquisition_sequence_test.py",
]

collect_ignore = _ARCUS_HARDWARE + _ADS_HARDWARE
