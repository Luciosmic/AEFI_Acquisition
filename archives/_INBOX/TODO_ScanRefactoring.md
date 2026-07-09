Analyse de la structure actuelle pour clarifier la hiérarchie DDD :


[5 tools called]


Analyse de la structure DDD actuelle et des options :


[4 tools called]


## Analyse DDD — Structure des agrégats

**Certitude: probable** — basé sur les principes DDD et la structure actuelle.

### 1. Problème avec l'approche actuelle

#### Structure actuelle
- `SpatialScan` : dans `entities/`, marqué "Entity"
- `StepScan` : dans `aggregates/`, hérite de `SpatialScan`, marqué "Aggregate Root"

#### Problème DDD
- Un Aggregate Root contrôle l'accès aux entités internes
- Les entités internes ont une identité locale (pas globale)
- Ici, `StepScan` a une identité globale (UUID) et gère ses propres invariants

### 2. Options architecturales

#### Option A : `SpatialScan` comme Aggregate Root abstrait (votre suggestion)

```python
# SpatialScan = Aggregate Root (abstrait)
class SpatialScan:
    """Aggregate Root for all spatial scans."""
    id: UUID
    _step_scan: Optional[StepScan] = None  # Entity interne
    _fly_scan: Optional[FlyScan] = None     # Entity interne
    
    def create_step_scan(self, config):
        self._step_scan = StepScan(config)
    
    def create_fly_scan(self, config):
        self._fly_scan = FlyScan(config)
```

Problèmes:
- Un seul scan actif à la fois (`_step_scan` OU `_fly_scan`)
- `StepScan` et `FlyScan` perdent leur identité globale
- Violation: un scan complet devrait avoir une identité globale

#### Option B : `StepScan` et `FlyScan` comme Aggregate Roots séparés (actuel)

```python
# Chaque scan est son propre agrégat
class StepScan:  # Aggregate Root
    id: UUID  # Identité globale
    _points: List[ScanPointResult]  # Value objects internes
    _motions: List[AtomicMotion]    # Entities internes (identité locale)
```

Avantages:
- Chaque scan a une identité globale
- Chaque scan gère ses propres invariants
- Frontières de cohérence claires

Problème:
- `SpatialScan` comme classe de base partagée (héritage) n'est pas idéal en DDD

#### Option C : Composition (recommandé)

```python
# SpatialScan = Aggregate Root (concret, pas abstrait)
class SpatialScan:
    """Aggregate Root for spatial scans."""
    id: UUID
    scan_type: ScanType  # Enum: STEP, FLY
    _step_scan_data: Optional[StepScanData] = None
    _fly_scan_data: Optional[FlyScanData] = None
    
    # Méthodes communes (lifecycle)
    def start(self): ...
    def complete(self): ...
    
    # Méthodes spécifiques (déléguées)
    def add_point_result(self, result):
        if self.scan_type == ScanType.STEP:
            self._step_scan_data.add_point(result)
```

Problème:
- Un seul type de scan par instance (pas de polymorphisme)

### 3. Recommandation : Option B améliorée

#### Structure proposée

```python
# SpatialScan = Base class partagée (technique, pas DDD concept)
# Déplacé de entities/ vers aggregates/ comme classe abstraite
class SpatialScan:
    """Base class for spatial scan aggregates (shared behavior)."""
    # Lifecycle commun
    id: UUID
    status: ScanStatus
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    
    def start(self): ...  # Template method
    def complete(self): ...

# StepScan = Aggregate Root concret
class StepScan(SpatialScan):
    """Aggregate Root for step-by-step scans."""
    _points: List[ScanPointResult]  # Value objects
    _motions: List[AtomicMotion]    # Entities internes (identité locale)
    
    # Invariants spécifiques à step scan
    def add_point_result(self, result): ...

# FlyScan = Aggregate Root concret (futur)
class FlyScan(SpatialScan):
    """Aggregate Root for fly scans."""
    _trajectory: FlyTrajectory  # Value object
    _motions: List[AtomicMotion]  # Entities internes
    
    # Invariants spécifiques à fly scan
```

#### Rationale
- Chaque scan est un Aggregate Root indépendant
- `SpatialScan` est une classe de base technique (code partagé)
- `AtomicMotion` est une entité interne avec identité locale
- Frontières de cohérence claires par scan

### 4. Réorganisation proposée

#### Structure de fichiers
```
domain/
  aggregates/
    spatial_scan.py          # Base class (shared behavior)
    step_scan.py             # Aggregate Root (concret)
    fly_scan.py              # Aggregate Root (concret, futur)
  entities/
    atomic_motion.py         # Entity interne (identité locale)
```

#### Clarification des responsabilités

| Composant | Type | Identité | Responsabilité |
|-----------|------|----------|----------------|
| `SpatialScan` | Base class | N/A (abstrait) | Comportement partagé (lifecycle) |
| `StepScan` | Aggregate Root | Globale (UUID) | Invariants step scan |
| `FlyScan` | Aggregate Root | Globale (UUID) | Invariants fly scan |
| `AtomicMotion` | Entity interne | Locale (dans scan) | Segment de mouvement |

### 5. Réponse à votre question

- `StepScan` doit rester un Aggregate Root (pas une entité interne)
- `SpatialScan` ne devrait pas être l'agrégat qui contient `StepScan` et `FlyScan`
- Raison: chaque scan a une identité globale et gère ses propres invariants

#### Structure correcte DDD
```
SpatialScan (base class technique)
  ├── StepScan (Aggregate Root)
  │     └── AtomicMotion (Entity interne, identité locale)
  └── FlyScan (Aggregate Root)
        └── AtomicMotion (Entity interne, identité locale)
```

### 6. Action recommandée

1. Déplacer `SpatialScan` de `entities/` vers `aggregates/`
2. Renommer en "base class" plutôt qu'Entity
3. Clarifier que `StepScan` et `FlyScan` sont des Aggregate Roots indépendants
4. `AtomicMotion` sera une Entity interne avec identité locale

**Certitude: probable** — cette structure respecte mieux DDD tout en conservant le partage de code via la classe de base.

Souhaitez-vous que je détaille la réorganisation ou la relation entre `AtomicMotion` (entité interne) et `StepScan` (agrégat root) ?