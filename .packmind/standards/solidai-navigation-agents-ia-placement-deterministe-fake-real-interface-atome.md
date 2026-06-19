# SolidAI — Navigation Agents IA : Placement Déterministe Fake, Real, Interface, Atome

Ce standard définit les règles de navigation et de placement que les agents IA doivent suivre dans la codebase SolidAI. Le placement est déterministe : connaître le type d'un fichier (Interface, Fake, Real) suffit à déduire son chemin sans chercher. Les agents Architectes naviguent dans le Meta-Domain (Markdown, Gherkin), les agents Développeurs naviguent dans src/. Le fichier <module>_intention.md est le pont synchronisé entre les deux niveaux. La séparation des tests est par couche architecturale, jamais par nature unit/integration.

## Rules

* Appliquer la règle de placement unique pour tout nouveau fichier : Interface (IXxx/Port) → domain/repositories/, Fake* → infrastructure/fake/, Real* → infrastructure/real/
* Utiliser le fichier <module>_intention.md comme pont de synchronisation entre le Meta-Domain (Markdown, Gherkin) et le code — le maintenir à jour quand l'implémentation diverge de la spécification
* Séparer les tests par couche architecturale (domain/, application/, infrastructure/) et non par nature unit/integration — co-localiser chaque test dans le _tests/ de son module
