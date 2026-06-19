---
name: 'SolidAI — Nomenclature : snake_case, Préfixes I/fake_, Dossier _tests/, Suffixe _test.py'
alwaysApply: true
description: 'Standardize SolidAI file, folder, and class naming with snake_case, _tests/ for test directories, _test.py (never .test.py) for Python tests, I-prefixed Domain interfaces, fake_-prefixed Fakes, and <module>_intention.md (module-prefixed) to enable deterministic O(1) navigation and avoid Python import-resolution issues.'
---

# Standard: SolidAI — Nomenclature : snake_case, Préfixes I/fake_, Dossier _tests/, Suffixe _test.py

Standardize SolidAI file, folder, and class naming with snake_case, _tests/ for test directories, _test.py (never .test.py) for Python tests, I-prefixed Domain interfaces, fake_-prefixed Fakes, and <module>_intention.md (module-prefixed) to enable deterministic O(1) navigation and avoid Python import-resolution issues. :
* Nommer le dossier de tests _tests/ (avec underscore préfixe) pour le distinguer visuellement du code de production et le faire apparaître en premier dans le tri alphabétique
* Nommer les fichiers de test avec le suffixe _test.py (underscore) et jamais .test.py (point) — le point dans un nom de fichier Python casse la résolution des imports de modules
* Nommer tous les fichiers et dossiers Python en snake_case — jamais de camelCase, PascalCase ou tirets dans les noms de fichiers et dossiers
* Préfixer les classes et fichiers Fake avec fake_ pour identifier immédiatement qu'il s'agit d'une implémentation d'infrastructure pour le référentiel Test
* Préfixer les interfaces de Domain avec I (majuscule) pour les distinguer des implémentations et les placer dans domain/repositories/ ou application/X_service/
* Nommer le fichier d'intention <module>_intention.md en préfixant le nom du module — ce pattern évite les collisions de noms dans les éditeurs et garantit l'unicité dans la navigation des agents IA

Full standard is available here for further request: [SolidAI — Nomenclature : snake_case, Préfixes I/fake_, Dossier _tests/, Suffixe _test.py](../../../.packmind/standards/solidai-nomenclature-snakecase-prefixes-ifake-dossier-tests-suffixe-testpy.md)