# SolidAI — Nomenclature : snake_case, Préfixes I/fake_, Dossier _tests/, Suffixe _test.py

Ce standard définit les conventions de nommage uniformes pour tous les fichiers, dossiers et classes de SolidAI. L'objectif est une navigation déterministe O(1) : connaître le type d'un élément permet de déduire immédiatement son nom et son emplacement. Les conventions couvrent les fichiers Python (snake_case), les tests (_test.py avec underscore, jamais point), le dossier de tests (_tests/ avec underscore préfixe), les interfaces (préfixe I), les Fakes (préfixe fake_) et le fichier d'intention nommé <module>_intention.md.

## Rules

* Nommer tous les fichiers et dossiers Python en snake_case — jamais de camelCase, PascalCase ou tirets dans les noms de fichiers et dossiers
* Nommer les fichiers de test avec le suffixe _test.py (underscore) et jamais .test.py (point) — le point dans un nom de fichier Python casse la résolution des imports de modules
* Nommer le dossier de tests _tests/ (avec underscore préfixe) pour le distinguer visuellement du code de production et le faire apparaître en premier dans le tri alphabétique
* Préfixer les interfaces de Domain avec I (majuscule) pour les distinguer des implémentations et les placer dans domain/repositories/ ou application/X_service/
* Préfixer les classes et fichiers Fake avec fake_ pour identifier immédiatement qu'il s'agit d'une implémentation d'infrastructure pour le référentiel Test
* Nommer le fichier d'intention <module>_intention.md en préfixant le nom du module — ce pattern évite les collisions de noms dans les éditeurs et garantit l'unicité dans la navigation des agents IA
