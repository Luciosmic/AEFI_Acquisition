# Modules externes

Dossiers **hors cœur applicatif** (`src/`) : outils autonomes (post-traitement, visualisation 3D, etc.).

- **Lancement** : depuis le **dashboard** principal (panneaux dédiés) avec le même interpréteur Python que l’app (`uv` / `.venv` à la racine du dépôt).
- **Objectif** : séparation claire et évolution modulaire ; une intégration plus poussée pourra venir plus tard sans mélanger ces arbres avec `src/`.

Sous-modules actuels : `post_processor_module/`, `cube_visualizer/`.

**Note** : le `.venv` sous `tools/` servait à un environnement isolé (ex. ancien outil « plot scan ») ; **il n’est pas requis** pour les boutons du dashboard, qui réutilisent les dépendances du projet principal.
