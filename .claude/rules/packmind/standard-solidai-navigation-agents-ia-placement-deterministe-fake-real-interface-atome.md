---
name: 'SolidAI — Navigation Agents IA : Placement Déterministe Fake, Real, Interface, Atome'
alwaysApply: true
description: 'Appliquer un placement déterministe des fichiers (Interfaces/Ports → domain/repositories/ ou application/<service>/ports/, Real → infrastructure/<adapter>/<adapter>.py, Fake → infrastructure/<adapter>/fake/fake_<adapter>.py) en synchronisant le Meta-Domain (Markdown/Gherkin) et src/ via intention.md et en organisant les tests par couche (domain/application/infrastructure) pour accélérer la navigation, réduire l’ambiguïté et maintenir l’architecture cohérente.'
---

# Standard: SolidAI — Navigation Agents IA : Placement Déterministe Fake, Real, Interface, Atome

Appliquer un placement déterministe des fichiers (Interfaces/Ports → domain/repositories/ ou application/<service>/ports/, Real → infrastructure/<adapter>/<adapter>.py, Fake → infrastructure/<adapter>/fake/fake_<adapter>.py) en synchronisant le Meta-Domain (Markdown/Gherkin) et src/ via intention.md et en organisant les tests par couche (domain/application/infrastructure) pour accélérer la navigation, réduire l’ambiguïté et maintenir l’architecture cohérente. :
* Appliquer la règle de placement unique pour tout nouveau fichier : Interface (IXxx/Port) → domain/repositories/ ou application/<service>/ports/, implémentation Real → infrastructure/<adapter>/<adapter>.py, Fake (quand pertinent) → infrastructure/<adapter>/fake/fake_<adapter>.py co-localisé avec le Real
* Séparer les tests par couche architecturale (domain/, application/, infrastructure/) et non par nature unit/integration — co-localiser chaque test dans le _tests/ de son module
* Utiliser le fichier intention.md comme pont de synchronisation entre le Meta-Domain (Markdown, Gherkin) et le code — le maintenir à jour quand l'implémentation diverge de la spécification

Full standard is available here for further request: [SolidAI — Navigation Agents IA : Placement Déterministe Fake, Real, Interface, Atome](../../../.packmind/standards/solidai-navigation-agents-ia-placement-deterministe-fake-real-interface-atome.md)