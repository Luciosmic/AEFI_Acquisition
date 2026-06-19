# Structure Recommandée pour Tests E2E

## Principe : Tester par Services Application (Use Cases)

**Rationale** :
- Les services application représentent les use cases métier
- Tests alignés avec l'utilisation réelle du système
- Plus facile à maintenir et comprendre
- Correspond à la structure existante (`application/services/*/tests/`)

---

## Structure Proposée

```
tests_e2e/
├── base/
│   ├── test_base_agent.py              # Classe de base diagram-friendly (existant)
│   ├── e2e_test_environment.py         # Environnement complet (existant)
│   └── test_fixtures.py                # Fixtures réutilisables (à créer)
│
├── scan_application_service/           # Tests E2E pour ScanApplicationService
│   ├── test_scan_nominal_flow.py       # Flux nominal complet
│   ├── test_scan_with_atomic_motions.py # Scan avec AtomicMotion
│   ├── test_scan_cancellation.py        # Annulation
│   ├── test_scan_pause_resume.py       # Pause/Resume
│   ├── test_scan_failure_handling.py   # Gestion d'erreurs
│   └── test_scan_trajectory_patterns.py # Patterns (serpentine, raster, comb)
│
├── motion_control_service/             # Tests E2E pour MotionControlService
│   ├── test_motion_control_basic.py     # Contrôles de base (jog, move_to, home)
│   ├── test_motion_profiles.py         # Profils de mouvement
│   └── test_motion_emergency_stop.py    # Arrêt d'urgence
│
├── continuous_acquisition_service/     # Tests E2E pour ContinuousAcquisitionService
│   ├── test_continuous_acquisition.py  # Acquisition continue
│   └── test_acquisition_sequence.py     # Séquence d'acquisition
│
├── hardware_configuration_service/     # Tests E2E pour HardwareConfigurationService
│   └── test_hardware_configuration.py  # Configuration matérielle
│
└── integration/                        # Tests multi-services
    ├── test_scan_with_acquisition.py   # Scan + Acquisition
    └── test_full_workflow.py           # Workflow complet utilisateur
```

**Note** : Les tests backend/infrastructure (comme `test_scan_executor_backend_mock_refinement.py`) restent dans `tests_e2e/` à la racine car ils testent l'infrastructure directement.

---

## Comparaison : Domain vs Services

### ❌ Par Domain (Bounded Contexts)
```
tests_e2e/
├── scan/
├── aefi_device/
├── test_bench/
```
**Problèmes** :
- Les use cases utilisent souvent plusieurs bounded contexts
- Moins aligné avec l'utilisation réelle
- Difficile de tester les interactions entre contexts

### ✅ Par Services Application (Recommandé)
```
tests_e2e/
├── scan_application_service/
├── motion_control_service/
├── continuous_acquisition_service/
```
**Avantages** :
- Aligné avec les use cases métier
- Tests plus proches de l'utilisation réelle
- Facile de tester les interactions (services utilisent plusieurs contexts)
- Cohérent avec structure existante (`application/services/*/tests/`)

---

## Organisation des Tests par Service

### ScanApplicationService
**Responsabilité** : Orchestrer les opérations de scan
**Tests** :
- Flux nominal (config → trajectoire → execution → résultats)
- AtomicMotion (génération, sélection profil, exécution)
- Gestion d'erreurs (motion, acquisition)
- Contrôles (pause, resume, cancel)
- Patterns de trajectoire

### MotionControlService
**Responsabilité** : Contrôler le mouvement
**Tests** :
- Commandes de base (jog, move_to, home)
- Profils de mouvement
- Arrêt d'urgence

### ContinuousAcquisitionService
**Responsabilité** : Acquisition continue
**Tests** :
- Démarrage/arrêt acquisition
- Streaming de données
- Gestion d'erreurs

---

## Fixtures Réutilisables

### `base/test_fixtures.py`
```python
def create_scan_config(zone, pattern, points):
    """Factory pour StepScanConfig"""
    
def create_mock_motion_port(profile=None, delay_ms=50.0):
    """Factory pour MockMotionPort configuré"""
    
def create_mock_acquisition_port():
    """Factory pour MockAcquisitionPort"""
    
def create_scan_service_with_mocks():
    """Factory pour ScanApplicationService avec mocks"""
```

---

## Implémentation

**Phase 1** : Créer structure + fixtures
**Phase 2** : Tests ScanApplicationService (priorité)
**Phase 3** : Tests autres services
**Phase 4** : Tests intégration



