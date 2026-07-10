# scan_trajectory — Intention

## Rationale

Value object encapsulant la séquence ordonnée de `Position2D` constituant la trajectoire d'un scan. Retourner un type dédié plutôt qu'une liste brute permet d'itérer proprement dans `StepScanExecutor` et d'ajouter des métadonnées (longueur totale, durée estimée) sans modifier les signatures.

## Responsibility

- Stocker la liste ordonnée de `Position2D`.
- Exposer `__len__`, `__iter__` pour permettre l'usage direct dans la boucle d'exécution.

## Design

- **Wrapper typé** autour de `List[Position2D]`.
- **Immuable** (frozen ou tuple interne) pour éviter la modification accidentelle en cours d'exécution.
