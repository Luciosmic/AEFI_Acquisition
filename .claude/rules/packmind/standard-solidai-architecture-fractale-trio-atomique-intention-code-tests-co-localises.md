---
name: 'SolidAI — Architecture Fractale Trio Atomique : Intention, Code, Tests Co-localisés'
alwaysApply: true
description: 'Enforce the SolidAI “Trio Atomique” fractal module layout—<module>_intention.md (Rationale/Responsibility/Design), <module>.py, and co-localized _tests/<module>_test.py at distance 1 (never .test.py)—to standardize DDD architecture, preserve Python import resolution, and make intent, implementation, and validation auditable while minimizing architectural debt.'
---

# Standard: SolidAI — Architecture Fractale Trio Atomique : Intention, Code, Tests Co-localisés

Enforce the SolidAI “Trio Atomique” fractal module layout—<module>_intention.md (Rationale/Responsibility/Design), <module>.py, and co-localized _tests/<module>_test.py at distance 1 (never .test.py)—to standardize DDD architecture, preserve Python import resolution, and make intent, implementation, and validation auditable while minimizing architectural debt. :
* Appliquer la structure du trio atomique (<module>_intention.md + <module>.py + _tests/) de manière uniforme à toutes les couches DDD sans exception
* Créer un fichier <module>_intention.md pour chaque module en utilisant le template Rationale / Responsibility / Design, même si le contenu est vide au départ
* Nommer les fichiers de test avec le suffixe _test.py (underscore) et jamais .test.py (point) — le point dans un nom de fichier Python casse la résolution des imports
* Placer les tests dans un sous-dossier _tests/ à l'intérieur du dossier du module — c'est le principe de distance minimale : chaque fichier est à exactement 1 niveau de son test
* Respecter l'ordre TDD lors de la création d'un atome : d'abord <module>_intention.md, puis <module>_test.py, puis l'implémentation <module>.py
* Structurer chaque atome avec <module>_intention.md et le code de production à la racine, et les tests dans _tests/ — les trois éléments restent dans le même arbre de dossiers

Full standard is available here for further request: [SolidAI — Architecture Fractale Trio Atomique : Intention, Code, Tests Co-localisés](../../../.packmind/standards/solidai-architecture-fractale-trio-atomique-intention-code-tests-co-localises.md)