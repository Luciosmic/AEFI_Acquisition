# continuous_acquisition_events — Intention

## Rationale

Modéliser les transitions d'état de l'acquisition continue (streaming temps réel) comme des événements domain distincts des événements de scan step-by-step. Permettent à la UI d'afficher un oscilloscope en direct sans dépendance directe sur l'exécuteur.

## Responsibility

- Événements du cycle de vie de l'acquisition continue : démarrage, sample reçu, arrêt, erreur.
- Chaque sample d'acquisition reçu peut être propagé pour affichage temps réel.

## Design

- **`@dataclass`** héritant de `DomainEvent`.
- Séparés des `scan_events` pour préserver la cohésion sémantique : scan = mesure positionnée, acquisition continue = stream brut.
