# adapter_mock_excitation_aware_acquisition — Intention

## Rationale

Mock spécialisé combinant une acquisition simulée sensible à la configuration d'excitation courante. Utilisé dans les tests d'intégration où la mesure doit répondre aux changements de fréquence/amplitude d'excitation.

## Responsibility

- Simuler `IAcquisitionPort` avec des mesures dépendant de l'état d'excitation configuré.
- Permettre la validation de la cohérence entre configuration d'excitation et données mesurées dans les tests.

## Design

- **`infrastructure/mocks/`**.
- Dépend du mock d'excitation pour accéder à la config courante et générer des mesures cohérentes.
