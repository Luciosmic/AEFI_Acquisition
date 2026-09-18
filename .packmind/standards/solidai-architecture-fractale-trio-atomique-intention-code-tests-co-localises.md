# SolidAI — Architecture Fractale Trio Atomique : Intention, Code, Tests Co-localisés

Ce standard formalise le Trio Atomique de SolidAI : chaque unité fonctionnelle (atome) regroupe dans le même dossier son intention (<module>\_intention.md), son implémentation (code source) et sa validation (tests dans \_tests/). La structure est fractale car elle s'applique uniformément à toutes les couches DDD. Les tests sont placés dans un sous-dossier \_tests/ au plus près du code, garantissant une distance minimale de 1 entre chaque fichier et son test. Un atome incomplet (manque l'un des trois éléments) est une dette architecturale immédiate.

## Rules

* Placer les tests dans un sous-dossier _tests/ à l'intérieur du dossier du module — c'est le principe de distance minimale : chaque fichier est à exactement 1 niveau de son test
* Structurer chaque atome avec <module>_intention.md et le code de production à la racine, et les tests dans _tests/ — les trois éléments restent dans le même arbre de dossiers
* Nommer les fichiers de test avec le suffixe _test.py (underscore) et jamais .test.py (point) — le point dans un nom de fichier Python casse la résolution des imports
* Créer un fichier intention.md pour chaque module en utilisant le template Rationale / Responsibility / Design, même si le contenu est vide au départ
* Respecter l'ordre TDD lors de la création d'un atome : d'abord <module>_intention.md, puis <module>_test.py, puis l'implémentation <module>.py
* Appliquer la structure du trio atomique (<module>_intention.md + <module>.py + _tests/) de manière uniforme à toutes les couches DDD sans exception
* Rédiger le Rationale en partant du problème que le module résout, avant d'introduire la solution — un Rationale qui commence par décrire le module lui-même (ses inputs, ses outputs, son algorithme) est invalide ; cette information appartient aux sections Responsibility et Design
* Le Rationale doit répondre à au moins l'une des deux questions : (1) qu'est-ce qui s'effondre si cet élément n'existe pas — quels couplages apparaissent, quelles responsabilités migrent ailleurs, quels invariants se cassent ? (2) qu'est-ce que la couche appelante y perd — testabilité, séparabilité des causes de changement, lisibilité du domaine ?
* Construire le Rationale comme une chaîne de conséquences : "Sans ce module, X arrive, ce qui signifie Y, ce qui force Z" — le lecteur doit pouvoir ressentir le problème avant de comprendre la solution
