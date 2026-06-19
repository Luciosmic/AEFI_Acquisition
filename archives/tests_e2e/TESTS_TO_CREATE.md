# Tests E2E à Créer

## ✅ ScanApplicationService (FAIT - 8 tests)
- ✅ test_scan_nominal_flow
- ✅ test_scan_with_atomic_motions
- ✅ test_scan_cancellation
- ✅ test_scan_pause_resume
- ✅ test_scan_failure_handling
- ✅ test_scan_trajectory_patterns (3 patterns)

## 📋 MotionControlService (À CRÉER)
**Use cases principaux :**
- `move_relative(dx, dy)` - Déplacement relatif
- `move_absolute(x, y)` - Déplacement absolu
- `home(axis)` - Homing
- `stop()` - Arrêt normal
- `emergency_stop()` - Arrêt d'urgence
- `set_speed(speed)` - Configuration vitesse
- `set_reference(axis, position)` - Définition référence

**Tests à créer :**
1. `test_motion_relative_move.py` - Déplacement relatif nominal
2. `test_motion_absolute_move.py` - Déplacement absolu nominal
3. `test_motion_homing.py` - Homing X, Y, both
4. `test_motion_stop.py` - Arrêt normal et d'urgence
5. `test_motion_speed_configuration.py` - Configuration vitesse
6. `test_motion_reference_setting.py` - Définition référence

## 📋 ContinuousAcquisitionService (À CRÉER)
**Use cases principaux :**
- `start_acquisition(config)` - Démarrer acquisition continue
- `stop_acquisition()` - Arrêter acquisition
- `update_acquisition_parameters(config)` - Mise à jour paramètres à la volée

**Tests à créer :**
1. `test_continuous_acquisition_start_stop.py` - Démarrage/arrêt nominal
2. `test_continuous_acquisition_parameter_update.py` - Mise à jour paramètres
3. `test_continuous_acquisition_error_handling.py` - Gestion d'erreurs

## 📋 HardwareConfigurationService (À CRÉER)
**Use cases principaux :**
- Découverte des configurateurs hardware
- Application de configuration
- Récupération des spécifications de paramètres

**Tests à créer :**
1. `test_hardware_config_discovery.py` - Découverte configurateurs
2. `test_hardware_config_application.py` - Application configuration

## 📋 Integration Tests (À CRÉER)
**Scénarios multi-services :**
1. `test_scan_with_continuous_acquisition.py` - Scan + acquisition continue
2. `test_motion_during_scan.py` - Contrôle motion pendant scan
3. `test_full_system_startup.py` - Démarrage système complet



