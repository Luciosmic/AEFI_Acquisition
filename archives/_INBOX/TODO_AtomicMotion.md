# TODO: Implémentation AtomicMotion

## Contexte

Refactoriser le système de mouvement pour introduire `AtomicMotion` comme entité domain représentant un déplacement atomique basé sur la distance relative (dx, dy) plutôt que sur les positions absolues.

**Rationale:**
- La distance est ce qui compte pour la sélection du profil de mouvement (petite vs grande distance)
- Les positions absolues sont contextuelles, la distance est universelle
- Réutilise le système d'événements existant (`MotionStarted/Completed` avec `motion_id`)
- Simplifie le modèle et le rend plus réutilisable

## Architecture Proposée

### Concepts Clés

1. **AtomicMotion** (Domain Entity)
   - Identité domain: `id` (UUID) - persistant
   - Identité exécution: `execution_motion_id` (str) - éphémère, lié aux événements
   - Distance relative: `dx`, `dy` (mm)
   - Profil de mouvement: `motion_profile` (sélectionné selon distance)
   - Durée estimée: `estimated_duration_seconds` (calculée)
   - État d'exécution: `execution_state` (PENDING, EXECUTING, COMPLETED, FAILED)

2. **MotionProfileSelector** (Domain Service)
   - Sélectionne le profil approprié basé sur la distance
   - Logique métier: petite distance = lent/précis, grande distance = rapide

3. **ScanTrajectory** transformation
   - Avant: `List[Position2D]` (positions absolues)
   - Après: `List[AtomicMotion]` (mouvements relatifs)

## Tâches par Couche

### Domain Layer

#### 1. Créer `AtomicMotion` Entity
- [ ] Créer `src/domain/entities/motion/atomic_motion.py`
- [ ] Définir structure avec:
  - `id: UUID` (identité domain)
  - `dx: float`, `dy: float` (déplacement relatif)
  - `motion_profile: MotionProfile`
  - `estimated_duration_seconds: float`
  - `execution_motion_id: Optional[str]` (identité exécution)
  - `execution_state: MotionState` (enum)
- [ ] Méthodes:
  - `calculate_estimated_duration()` - calcule durée basée sur distance + profil
  - `start(motion_id: str)` - démarre exécution
  - `complete()` - marque comme complété
  - `fail(error: str)` - marque comme échoué
- [ ] Validation dans `__post_init__`

#### 2. Créer `MotionState` Enum
- [ ] Créer `src/domain/value_objects/motion/motion_state.py`
- [ ] États: `PENDING`, `EXECUTING`, `COMPLETED`, `FAILED`

#### 3. Créer `MotionProfileSelector` Domain Service
- [ ] Créer `src/domain/services/motion_profile_selector.py`
- [ ] Méthode `select_for_distance(distance_mm: float) -> MotionProfile`
- [ ] Logique de sélection:
  - Distance < seuil (ex. 5mm) → profil lent/précis
  - Distance >= seuil → profil rapide
- [ ] Configurable avec seuils et presets

#### 4. Modifier `ScanTrajectoryFactory`
- [ ] Modifier `src/domain/services/scan_trajectory_factory.py`
- [ ] Ajouter méthode `create_motions(positions: List[Position2D], profile_selector: MotionProfileSelector) -> List[AtomicMotion]`
- [ ] Calculer `dx, dy` entre positions consécutives
- [ ] Calculer distance: `sqrt(dx² + dy²)`
- [ ] Sélectionner profil via `profile_selector`
- [ ] Créer `AtomicMotion` avec durée estimée calculée

#### 5. Modifier `StepScan` Aggregate
- [ ] Modifier `src/domain/aggregates/step_scan.py`
- [ ] Ajouter `_motions: List[AtomicMotion]` (en plus de `_points`)
- [ ] Méthode `add_motion(motion: AtomicMotion)` si nécessaire
- [ ] Méthode `get_motions() -> List[AtomicMotion]`
- [ ] Lier motions aux points (un motion = un segment entre deux points)

### Application Layer

#### 6. Modifier `ScanApplicationService`
- [ ] Modifier `src/application/services/scan_application_service/scan_application_service.py`
- [ ] Après génération de trajectoire, créer `AtomicMotions`
- [ ] Passer `AtomicMotions` à l'exécuteur au lieu de `ScanTrajectory` (positions)

#### 7. Créer/Modifier DTOs si nécessaire
- [ ] Vérifier si `Scan2DConfigDTO` doit inclure des infos de profil
- [ ] Adapter si besoin

### Infrastructure Layer

#### 8. Modifier `StepScanExecutor`
- [ ] Modifier `src/infrastructure/execution/step_scan_executor.py`
- [ ] Remplacer `for position in trajectory` par `for motion in motions`
- [ ] Calculer target: `current_position + (motion.dx, motion.dy)`
- [ ] Appliquer `motion.motion_profile` avant `move_to()`
- [ ] Mapping `motion_id` → `AtomicMotion`:
  - Créer `_motion_mapping: Dict[str, AtomicMotion]`
  - Stocker mapping au démarrage
  - Utiliser pour corréler événements
- [ ] Gérer événements:
  - `MotionStarted` → `motion.start(motion_id)`
  - `MotionCompleted` → trouver motion via mapping → `motion.complete()`
  - `MotionFailed` → trouver motion → `motion.fail(error)`

#### 9. Modifier `IMotionPort` (si nécessaire)
- [ ] Vérifier si `move_to()` doit accepter `MotionProfile`
- [ ] Ou créer `apply_motion_profile(profile: MotionProfile)` séparé
- [ ] Adapter `ArcusAdapter` et `MockMotionPort` en conséquence

### Tests

#### 10. Tests Unitaires Domain
- [ ] Test `AtomicMotion.calculate_estimated_duration()` avec différents profils
- [ ] Test `MotionProfileSelector` avec différentes distances
- [ ] Test `ScanTrajectoryFactory.create_motions()` génère correctement

#### 11. Tests Intégration
- [ ] Test exécution scan avec `AtomicMotion`
- [ ] Test mapping événements → motions
- [ ] Test sélection profil selon distance

## Points d'Attention

### Calcul de Durée Estimée

Formule trapèze de vitesse:
- Distance: `distance = sqrt(dx² + dy²)`
- Temps accélération: `t_acc = (target_speed - min_speed) / acceleration`
- Distance accélération: `d_acc = min_speed * t_acc + 0.5 * acceleration * t_acc²`
- Temps décélération: `t_dec = (target_speed - min_speed) / deceleration`
- Distance décélération: `d_dec = target_speed * t_dec - 0.5 * deceleration * t_dec²`

Cas:
- Si `distance < d_acc + d_dec`: mouvement sans phase constante
- Sinon: `t_total = t_acc + (distance - d_acc - d_dec) / target_speed + t_dec`

### Sélection de Profil

- Définir seuils de distance (ex. 5mm pour "petite")
- Définir profils par défaut pour chaque catégorie
- Rendre configurable (presets)

### Premier Mouvement

- Décider: depuis position actuelle ou depuis premier point de trajectoire?
- Probablement: depuis position actuelle (plus flexible)

## Questions Ouvertes

1. **Seuils de distance**: Quelles valeurs pour "petite" vs "grande" distance?
2. **Profils par défaut**: Quels profils pour chaque catégorie?
3. **Direction**: Faut-il stocker direction (angle) ou seulement distance totale?
4. **Réexécution**: Un `AtomicMotion` peut-il être réexécuté (nouveau `execution_motion_id`)?
5. **Événements**: Créer `AtomicMotionStarted/Completed` ou réutiliser `MotionStarted/Completed`?

## Ordre d'Implémentation Recommandé

1. Domain Layer d'abord (AtomicMotion, MotionState, MotionProfileSelector)
2. Tests unitaires domain
3. Modification ScanTrajectoryFactory
4. Modification StepScan
5. Modification StepScanExecutor
6. Tests intégration
7. Application Layer (ScanApplicationService)

## Références

- `MotionProfile`: `src/domain/model/test_bench/value_objects/motion_profile.py`
- `MotionEvents`: `src/domain/events/motion_events.py`
- `ScanTrajectoryFactory`: `src/domain/services/scan_trajectory_factory.py`
- `StepScan`: `src/domain/aggregates/step_scan.py`
- `StepScanExecutor`: `src/infrastructure/execution/step_scan_executor.py`


