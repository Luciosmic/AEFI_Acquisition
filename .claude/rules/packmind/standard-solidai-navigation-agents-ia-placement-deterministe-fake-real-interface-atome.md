---
name: 'SolidAI — Navigation Agents IA : Placement Déterministe Fake, Real, Interface, Atome'
alwaysApply: true
description: 'Définit le placement déterministe O(1) pour les agents IA : Fake → infrastructure/fake/, Real → infrastructure/real/, Interface → domain/repositories/, co-localisation dans _tests/, séparation par couche architecturale et non unit/integration.'
---

# Standard: SolidAI — Navigation Agents IA : Placement Déterministe Fake, Real, Interface, Atome

Définit le placement déterministe O(1) pour les agents IA : Fake → infrastructure/fake/, Real → infrastructure/real/, Interface → domain/repositories/, co-localisation dans _tests/, séparation par couche architecturale et non unit/integration. :
* Appliquer la règle de placement unique pour tout nouveau fichier : Interface (IXxx/Port) → domain/repositories/, Fake* → infrastructure/fake/, Real* → infrastructure/real/
* Séparer les tests par couche architecturale (domain/, application/, infrastructure/) et non par nature unit/integration — co-localiser chaque test dans le _tests/ de son module
* Utiliser le fichier <module>_intention.md comme pont de synchronisation entre le Meta-Domain (Markdown, Gherkin) et le code — le maintenir à jour quand l'implémentation diverge de la spécification

Full standard is available here for further request: [SolidAI — Navigation Agents IA : Placement Déterministe Fake, Real, Interface, Atome](../../../.packmind/standards/solidai-navigation-agents-ia-placement-deterministe-fake-real-interface-atome.md)