# SolidAI — Test Doubles DDD : Fake In-Memory vs Mock, Placement Infrastructure

Ce standard formalise la distinction entre Fake et Mock selon DDD, et impose le placement des Fakes en co-localisation avec leur Real dans infrastructure/<adapter>/fake/. Un Fake est une implémentation réelle et fonctionnelle d'une interface de domaine, simplifiée pour le référentiel Test (in-memory, pas d'I/O). Un Mock vérifie des interactions (behaviour). Les Fakes permettent la propagation garantie des tests : Domain → Application (via Fake) → Infrastructure (via contrat). Les Fakes ne sont créés que pour les adapters qui en bénéficient (effets de bord, coût d'exécution non trivial) ; pour les adapters purement calculatoires sans I/O, le Real lui-même tient lieu de double de test. Le Fake doit lui-même avoir son propre trio atomique avec des tests validant le contrat de l'interface.

## Rules

* Placer les Fakes dans infrastructure/<adapter>/fake/ (co-localisés avec leur Real) avec le trio atomique complet (intention.md + implémentation + _tests/)
* Utiliser des Fakes (implémentation in-memory fonctionnelle) plutôt que des Mocks (vérification d'interactions) pour tester les use cases applicatifs — le Fake permet la vérification d'état, le Mock vérifie les appels
* Tester le Fake lui-même pour garantir qu'il respecte le contrat de l'interface Domain — cette validation est le garant de la propagation des tests vers l'infrastructure réelle
* Créer un Fake quand l'adapter Real a des effets de bord (I/O, réseau, randomness) ou un coût d'exécution non trivial — pour les adapters purement calculatoires sans effets de bord, le Real lui-même tient lieu de double de test
