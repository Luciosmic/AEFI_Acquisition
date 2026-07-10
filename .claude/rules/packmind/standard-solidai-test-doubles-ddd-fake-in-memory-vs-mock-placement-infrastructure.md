---
name: 'SolidAI — Test Doubles DDD : Fake In-Memory vs Mock, Placement Infrastructure'
alwaysApply: true
description: 'Standardize DDD test doubles by colocating functional in-memory Fakes beside their Real in infrastructure/<adapter>/fake/ (with intention.md, implementation, and _tests/) and preferring them over interaction-based Mocks for application use cases to validate domain contracts, ensure test propagation to real infrastructure, and avoid unnecessary doubles for pure computational adapters.'
---

# Standard: SolidAI — Test Doubles DDD : Fake In-Memory vs Mock, Placement Infrastructure

Standardize DDD test doubles by colocating functional in-memory Fakes beside their Real in infrastructure/<adapter>/fake/ (with intention.md, implementation, and _tests/) and preferring them over interaction-based Mocks for application use cases to validate domain contracts, ensure test propagation to real infrastructure, and avoid unnecessary doubles for pure computational adapters. :
* Créer un Fake quand l'adapter Real a des effets de bord (I/O, réseau, randomness) ou un coût d'exécution non trivial — pour les adapters purement calculatoires sans effets de bord, le Real lui-même tient lieu de double de test
* Placer les Fakes dans infrastructure/<adapter>/fake/ (co-localisés avec leur Real) avec le trio atomique complet (intention.md + implémentation + _tests/)
* Tester le Fake lui-même pour garantir qu'il respecte le contrat de l'interface Domain — cette validation est le garant de la propagation des tests vers l'infrastructure réelle
* Utiliser des Fakes (implémentation in-memory fonctionnelle) plutôt que des Mocks (vérification d'interactions) pour tester les use cases applicatifs — le Fake permet la vérification d'état, le Mock vérifie les appels

Full standard is available here for further request: [SolidAI — Test Doubles DDD : Fake In-Memory vs Mock, Placement Infrastructure](../../../.packmind/standards/solidai-test-doubles-ddd-fake-in-memory-vs-mock-placement-infrastructure.md)