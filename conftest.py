"""
Root conftest.py — pytest collection configuration.

Deux catégories d'exclusion :
1. TESTS HARDWARE : nécessitent une connexion matérielle physique.
   Exclus de la collection car leurs imports échouent ou ils tentent
   une connexion réelle. À réactiver quand le matériel est branché.
2. TESTS API OBSOLÈTE : référencent des méthodes/classes supprimées lors
   du refactoring DDD (connect/disconnect → enable/disable, _stage → _controller,
   port= kwarg, classes removed). À mettre à jour quand le temps le permet.
3. TESTS CODE MORT : référencent des classes supprimées sans plan de réimplémenter.
   À supprimer lors du prochain nettoyage si la fonctionnalité reste absente.
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

# -- Tests API obsolète (rename connect→enable, _stage→_controller, etc.) --------
# Ces tests testent des comportements valides mais utilisent l'ancienne API interne.
# Ils ne nécessitent pas de matériel mais demandent une mise à jour du code de test.
_OBSOLETE_API = [
    "src/infrastructure/hardware/arcus_performax_4EX/_tests/arcus_async_architecture_test.py",
    "src/infrastructure/hardware/arcus_performax_4EX/_tests/arcus_composition_root_test.py",
    "src/infrastructure/hardware/arcus_performax_4EX/_tests/arcus_speed_setting_test.py",
    "src/infrastructure/hardware/arcus_performax_4EX/_tests/arcus_unit_conversion_test.py",
]

# -- Tests code mort (classes supprimées lors du refactoring DDD) ---------------
_DEAD_CODE = [
    # GenericHardwareConfigPresenter (interface.ui_hardware_advanced_configuration supprimé)
    "src/_tests/e2e_advanced_config_test.py",
    "src/_tests/e2e_advanced_config_diagram_test.py",
    # ActionableHardwareParametersSpec + ArcusPerformax4EXConfigProvider (supprimés)
    "src/application/services/hardware_configuration_service/_tests/hardware_configuration_service_test.py",
    # ArcusSpeedConfigAdapter (non implémenté)
    "src/infrastructure/hardware/arcus_performax_4EX/_tests/arcus_deceleration_config_test.py",
    # CoordinateTransformer (interface.logic supprimé)
    "src/interface/_tests/coordinate_transformer_test.py",
]

collect_ignore = _ARCUS_HARDWARE + _ADS_HARDWARE + _OBSOLETE_API + _DEAD_CODE
