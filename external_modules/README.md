# Modules externes

Dossiers **hors cœur applicatif** (`src/`) : outils autonomes (post-traitement, visualisation 3D, etc.).

- **Lancement** : depuis le panneau **External Modules** du dashboard (entrées pour chaque outil) avec le même interpréteur Python que l’app (`uv` / `.venv` à la racine du dépôt).
- **Objectif** : séparation claire et évolution modulaire ; une intégration plus poussée pourra venir plus tard sans mélanger ces arbres avec `src/`.

Sous-modules actuels : `post_processor_module/`, `cube_visualizer/`.
