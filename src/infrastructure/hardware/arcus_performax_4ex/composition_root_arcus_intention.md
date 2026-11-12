# composition_root_arcus — Intention

## Rationale

Point de composition des dépendances pour le sous-système Arcus. Instancie le driver, les adaptateurs motion et lifecycle, et les assemble pour être injectés dans le composition root global. Centraliser cette construction évite la duplication dans les tests et les scripts.

## Responsibility

- Instancier `DriverArcusPerformax4EX`, `AdapterMotionPortArcusPerformax4EX`, `AdapterLifecycleArcusPerformax4EX`.
- Retourner les adaptateurs prêts à l'injection dans les services applicatifs.

## Design

- **Module de composition** (pas une classe) : fonctions ou dataclass de résultat.
- Utilisé depuis le composition root global de l'application (`main.py`).
