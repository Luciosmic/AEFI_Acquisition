# AEFI 4Sphere Post-Processor - Domain Layer Notes

> Notes de conception DDD extraites du diagramme `domain_layer.puml`

---

## Principes DDD (selon RAG Eric Evans)

### 1. Aggregate = Boundary de cohérence

- 1 Aggregate = 1 unité de cohérence transactionnelle
- Invariants maintenus à l'intérieur de l'agrégat
- Règles ne peuvent s'étendre entre agrégats
- **Exemple:** `object_type` cohérent pour toutes simulations

### 2. Règles de référence (RAG)

- Objets externes référencent seulement **Aggregate Root**
- Objets internes (`Simulation`) accessibles uniquement par traversal depuis Root
- Autre agrégat peut référencer `SimulationCollection` mais **PAS** `Simulation` directement
- Delete Root → tout l'agrégat supprimé (garbage collection)

### 3. Identity vs Equality

**Entity (Simulation):**

- Identité conceptuelle (`SimulationId`)
- `sim1.equals(sim2)` → compare IDs
- Peut être rechargée → même entité, nouvelle instance

**Value Object (SpatialScanSimulationResults):**

- Pas d'identité
- Égalité par valeur de tous attributs
- Interchangeable si valeurs identiques
- Immutable → pas de side effects

### 4. Langage ubiquitaire (termes métier)

| Terme            | Description                            | Localisation                                                            |
| ---------------- | -------------------------------------- | ----------------------------------------------------------------------- |
| `SensorPosition` | Position du capteur qui **se déplace** | Liste dans `SpatialScanSimulationResults` - varie pendant le scan       |
| `ObjectPosition` | Position **fixe** de l'objet testé     | Dans `ObjectParameters` (configuration) - ne change pas pendant le scan |

### 5. Paramètres traités uniformément

Tous via `SimulationConfiguration`:

- `object_parameters` (type, dimensions, object_position)
- `environment_parameters` (couches, conductivités)
- `background_parameters` (milieu extérieur)
- `device_parameters` (électrodes, courant)
- `study_parameters` (fréquence, type étude)
- `swept_parameters` (paramètres variés dans étude)

### 6. Référentiels (ReferenceFrame)

- `testbench_frame`: référentiel du banc d'essai (root)
- `sensor_frame`: référentiel du capteur (parent=testbench)
- `object_position` exprimée dans `testbench_frame`
- `sensor_positions` exprimées dans `sensor_frame`
- Transformation via `CoordinateTransformationService`

### 7. Granularité d'une Simulation

**1 Simulation = 1 scan spatial avec paramètres FIXES**

| Type de sweep                          | Résultat                             |
| -------------------------------------- | ------------------------------------ |
| Scan spatial (grille sensor_positions) | 1 Simulation, N SensorPositions      |
| Sweep fréquentiel                      | N Simulations (1 par fréquence)      |
| Sweep object_position                  | N Simulations (1 par position objet) |

### 8. Domain Services (stateless, QUERY-ONLY)

**Pattern `compute_xxx` / `get_xxx`:**

- `compute_xxx`: calcule champ/structure complète
- `get_xxx`: extrait valeur spécifique d'un résultat

**Services disponibles:**
| Service | Responsabilité |
|---------|---------------|
| `SpatialDerivationService` | Dérivées spatiales (∇U, ∇²U) |
| `ScanOptimizationService` | Optimise échantillonnage futur |
| `ResultsInterpolationService` | Reconstruit champs continus |
| `CoordinateTransformationService` | Transforme entre frames |

**Tous QUERY-ONLY (CQS):**

- Lisent Value Objects immutables
- Retournent nouveaux Value Objects
- Aucune mutation d'état

---

## Anticorruption Layer (Adapter)

`simulation_provider` adapter = Couche anticorruption protégeant domaine de détails externes

### Input (Infrastructure)

- CSV/HTML (COMSOL) → détails implémentation
- VTU (FEniCS) → format simulateur
- Autres sources → technologie variable

### Translation (Adapter)

1. Parse tensions `V_pos`, `V_neg` (détail technique)
2. Calcule `U = V_pos - V_neg` (concept domaine)
3. Extrait TOUS les paramètres (depuis HTML)
4. Traduit en langage ubiquitaire du domaine

### Output (Domain concepts)

```python
Simulation(
    id=SimulationId(...),                    # ← Entity identity
    metadata=SimulationMetadata(
        configuration=SimulationConfiguration(
            object_parameters=ObjectParameters(...),
            study_parameters=StudyParameters(
                frequency=10000              # ← Paramètre comme les autres
            ),
            swept_parameters=SweptParameters(...)
        )
    ),
    measurements=SpatialScanSimulationResults(
        U_fields=VoltageFields(...)          # ← VO domaine
    )
)
```

### Isolation

- `V_pos`, `V_neg` ne traversent **JAMAIS** la boundary
- Domaine ne connaît que `U` (réalité physique)
- Changement de simulateur → seul adapter modifié

---

## Infrastructure (persistence HDF5)

Le domaine est persisté en HDF5 mais la structure domaine est **INDÉPENDANTE**:

```
SimulationCollection → Parallelepiped.h5
  /simulations/sim_XXX/
    /measurements/              ← SpatialScanSimulationResults
      - sensor_positions        (capteur se déplace)
      - U_fields
    /metadata/                  ← SimulationMetadata
      /configuration/           ← SimulationConfiguration
        /object_parameters/
          - object_position     (objet fixe)
          - dimensions
          - material
        - environment_parameters
        - background_parameters
        - device_parameters
        - study_parameters      (frequency, etc.)
        - swept_parameters
  /catalog/                     ← Index (optimisation infra)
```

> **Le domaine ne connaît PAS HDF5.** L'infrastructure traduit domaine ↔ HDF5.

---

## Exemples d'utilisation (Application Layer)

```python
# Créer collection pour Parallelepiped
collection = SimulationCollection(
    object_type=ObjectType.PARALLELEPIPED
)

# Ajouter simulation (fournie par adapter)
simulation = simulation_provider.load_from_source(
    csv_path="...", html_path="..."
)
collection.add_simulation(simulation)

# Requêter simulations par paramètres
sims = collection.query(
    QueryCriteria(
        study_parameters={'frequency': 10000},
        object_parameters={'x_center': (-5, 5)},
        timestamp_range=(start_date, end_date)
    )
)

# Accéder aux mesures
sim = collection.get_simulation(sim_id)
U = sim.measurements.U_fields.U_y

# Comparer simulations
comparison = collection.compare_simulations(
    sim_ids=[id1, id2],
    component="U_y"
)
```
