---
name: 'SolidAI — Navigation Agents IA : Placement Déterministe Fake, Real, Interface, Atome'
alwaysApply: true
description: 'SolidAI — Navigation Agents IA : Placement Déterministe Fake, Real, Interface, Atome'
---

# Standard: SolidAI — Navigation Agents IA : Placement Déterministe Fake, Real, Interface, Atome

Ce standard définit les règles de navigation et de placement que les agents IA doivent suivre dans la codebase SolidAI. Le placement est déterministe : connaître le type d'un fichier (Interface, Fake,... :
* Appliquer la règle de placement unique pour tout nouveau fichier : Interface (IXxx/Port) → domain/repositories/ ou application/<service>/ports/, implémentation Real → infrastructure/<adapter>/<adapter>.py, Fake (quand pertinent) → infrastructure/<adapter>/fake/fake_<adapter>.py co-localisé avec le Real
* Séparer les tests par couche architecturale (domain/, application/, infrastructure/) et non par nature unit/integration — co-localiser chaque test dans le _tests/ de son module
* Utiliser le fichier intention.md comme pont de synchronisation entre le Meta-Domain (Markdown, Gherkin) et le code — le maintenir à jour quand l'implémentation diverge de la spécification

Full standard is available here for further request: [SolidAI — Navigation Agents IA : Placement Déterministe Fake, Real, Interface, Atome](../../../.packmind/standards/solidai-navigation-agents-ia-placement-deterministe-fake-real-interface-atome.md)