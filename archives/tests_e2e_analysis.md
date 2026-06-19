# Analyse des Tests E2E - Plan de Refactoring

## Tests E2E Existants

### 1. `test_base_agent.py`
**Type** : Classe de base pour tests diagram-friendly
**Responsabilité** : Fournir infrastructure de logging pour diagrammes de séquence
**Caractéristiques** :
- Logging structuré d'interactions
- Génération de JSON pour diagrammes
- Support pour assertions avec expect/got

### 2. `test_scan_executor_backend_mock_refinement.py`
**Type** : Tests backend avec mocks
**Tests** :
- `test_event_based_execution` : Test nominal avec événements
- `test_motion_failure_handling` : Test de gestion d'erreur
- `test_physics_based_execution` : Test avec profil de mouvement réaliste

**Mocks utilisés** :
- `MockMotionPort` (avec event_bus)
- `MockAcquisitionPort`
- `InMemoryEventBus`

### 3. `e2e_test_environment.py`
**Type** : Environnement de test complet
**Responsabilité** : Bootstrap complet de l'application avec mocks
**Composants** :
- QApplication (PyQt)
- Services (ScanApplicationService, HardwareConfigurationService)
- Presenters (ScanPresenter, ExcitationPresenter, ContinuousAcquisitionPresenter)
- MainWindow
- EventBus + Mocks

---

## Structure Recommandée pour Tests E2E

### Organisation par Fonctionnalité

```
tests_e2e/
├── base/
│   ├── test_base_agent.py          # Classe de base (existant)
│   ├── e2e_test_environment.py     # Environnement (existant)
│   └── test_fixtures.py            # Fixtures réutilisables (à créer)
│
├── scan/
│   ├── test_scan_nominal_flow.py           # Flux nominal complet
│   ├── test_scan_with_atomic_motions.py    # Scan avec AtomicMotion
│   ├── test_scan_cancellation.py            # Annulation de scan
│   ├── test_scan_pause_resume.py            # Pause/Resume
│   ├── test_scan_failure_handling.py        # Gestion d'erreurs
│   └── test_scan_trajectory_patterns.py     # Différents patterns (serpentine, raster, comb)
│
├── motion/
│   ├── test_motion_control_basic.py          # Contrôles de base
│   ├── test_motion_profiles.py              # Profils de mouvement
│   └── test_motion_emergency_stop.py        # Arrêt d'urgence
│
├── acquisition/
│   ├── test_continuous_acquisition.py       # Acquisition continue
│   ├── test_acquisition_sequence.py         # Séquence d'acquisition
│   └── test_acquisition_averaging.py        # Moyennage
│
└── integration/
    ├── test_scan_with_acquisition.py        # Scan + Acquisition
    ├── test_hardware_configuration.py       # Configuration matérielle
    └── test_full_workflow.py                # Workflow complet
```

---

## Tests à Créer (Priorité)

### Phase 1 : Tests Scan (Critique)

#### 1. `test_scan_nominal_flow.py`
**Objectif** : Valider le flux complet d'un scan nominal
**Scénario** :
- Configuration scan (zone, pattern, points)
- Génération trajectoire
- Création AtomicMotions
- Exécution complète
- Vérification résultats

**Mocks** :
- MockMotionPort (avec profil réaliste)
- MockAcquisitionPort
- InMemoryEventBus

**Assertions** :
- Scan status = COMPLETED
- Nombre de points acquis = attendu
- Tous les AtomicMotions = COMPLETED
- Événements émis (ScanStarted, ScanPointAcquired, ScanCompleted)

#### 2. `test_scan_with_atomic_motions.py`
**Objectif** : Valider l'intégration AtomicMotion dans le scan
**Scénario** :
- Génération de motions depuis trajectoire
- Sélection de profils selon distance
- Exécution avec mapping motion_id
- Vérification états des motions

**Assertions** :
- Motions créées correctement
- Profils sélectionnés selon distance
- Mapping motion_id → AtomicMotion fonctionne
- Durées estimées calculées

#### 3. `test_scan_cancellation.py`
**Objectif** : Valider l'annulation de scan
**Scénario** :
- Démarrer scan
- Annuler pendant exécution
- Vérifier arrêt propre

**Assertions** :
- Scan status = CANCELLED
- Motions en cours arrêtées
- Événement ScanCancelled émis

#### 4. `test_scan_pause_resume.py`
**Objectif** : Valider pause/resume
**Scénario** :
- Démarrer scan
- Pause à mi-parcours
- Resume
- Vérifier continuation

**Assertions** :
- Scan status transitions (RUNNING → PAUSED → RUNNING)
- Points acquis avant pause conservés
- Événements ScanPaused/ScanResumed

#### 5. `test_scan_failure_handling.py`
**Objectif** : Valider gestion d'erreurs
**Scénarios** :
- Échec motion
- Échec acquisition
- Timeout

**Assertions** :
- Scan status = FAILED
- Motions en échec identifiées
- Événement ScanFailed émis
- Raison d'échec capturée

#### 6. `test_scan_trajectory_patterns.py`
**Objectif** : Valider différents patterns de scan
**Scénarios** :
- Pattern SERPENTINE
- Pattern RASTER
- Pattern COMB

**Assertions** :
- Trajectoires générées correctement
- Ordre des points conforme au pattern
- AtomicMotions créés entre points consécutifs

---

### Phase 2 : Tests Motion (Important)

#### 7. `test_motion_control_basic.py`
**Objectif** : Contrôles de base (jog, move_to, home)
**Mocks** : MockMotionPort

#### 8. `test_motion_profiles.py`
**Objectif** : Validation des profils de mouvement
**Scénarios** :
- Profil lent (petite distance)
- Profil rapide (grande distance)
- Calcul de durée estimée

---

### Phase 3 : Tests Acquisition (Important)

#### 9. `test_continuous_acquisition.py`
**Objectif** : Acquisition continue
**Mocks** : MockAcquisitionPort, MockContinuousAcquisitionExecutor

#### 10. `test_acquisition_sequence.py`
**Objectif** : Séquence d'acquisition avec moyennage

---

### Phase 4 : Tests Intégration (Complémentaire)

#### 11. `test_scan_with_acquisition.py`
**Objectif** : Intégration scan + acquisition
**Scénario** : Scan complet avec acquisition réelle

#### 12. `test_full_workflow.py`
**Objectif** : Workflow complet utilisateur
**Scénario** :
- Configuration matérielle
- Configuration scan
- Exécution
- Export résultats

---

## Principes de Design

### 1. Isolation
- Chaque test est indépendant
- Setup/Teardown propre
- Pas de dépendances entre tests

### 2. Diagram-Friendly
- Utiliser `DiagramFriendlyTest` comme base
- Logger toutes les interactions importantes
- Générer JSON pour visualisation

### 3. Mocks Configurables
- Mocks avec paramètres configurables (délais, profils, erreurs)
- Injection de comportements spécifiques
- Validation des appels

### 4. Assertions Claires
- Assertions explicites avec messages
- Vérification d'états (domain + infrastructure)
- Vérification d'événements

### 5. Performance
- Tests rapides (< 1s pour tests unitaires backend)
- Tests e2e complets (< 5s)
- Utiliser timeouts appropriés

---

## Fixtures à Créer

### `test_fixtures.py`
```python
def create_scan_config(zone, pattern, points):
    """Factory pour StepScanConfig"""
    
def create_mock_motion_port(profile=None, delay_ms=50.0):
    """Factory pour MockMotionPort configuré"""
    
def create_mock_acquisition_port():
    """Factory pour MockAcquisitionPort"""
    
def create_test_environment():
    """Factory pour TestEnvironment complet"""
```

---

## Prochaines Étapes

1. ✅ Corriger erreur d'import DataValidationResult
2. Créer structure de dossiers
3. Créer fixtures réutilisables
4. Implémenter tests Phase 1 (Scan)
5. Implémenter tests Phase 2 (Motion)
6. Implémenter tests Phase 3 (Acquisition)
7. Implémenter tests Phase 4 (Integration)



