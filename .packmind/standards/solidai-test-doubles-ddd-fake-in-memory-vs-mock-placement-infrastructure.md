# SolidAI — Test Doubles DDD : Fake In-Memory vs Mock, Placement Infrastructure

Ce standard formalise la distinction entre Fake et Mock selon DDD, et impose le placement des Fakes dans infrastructure/fake/. Un Fake est une implémentation réelle et fonctionnelle d'une interface de domaine, simplifiée pour le référentiel Test (in-memory, pas d'I/O). Un Mock vérifie des interactions (behaviour). Les Fakes permettent la propagation garantie des tests : Domain → Application (via Fake) → Infrastructure (via contrat). Sans Fake testé, l'équation de conduction ne peut pas se propager de proche en proche. Le Fake doit lui-même avoir son propre trio atomique avec des tests validant le contrat de l'interface.

## Rules

* Placer les Fakes dans infrastructure/fake/[catégorie]/[module]/ avec le trio atomique complet (<module>_intention.md + implémentation + _tests/)
* Utiliser des Fakes (implémentation in-memory fonctionnelle) plutôt que des Mocks (vérification d'interactions) pour tester les use cases applicatifs — le Fake permet la vérification d'état, le Mock vérifie les appels
* Tester le Fake lui-même pour garantir qu'il respecte le contrat de l'interface Domain — cette validation est le garant de la propagation des tests vers l'infrastructure réelle
* S'assurer que pour chaque interface Domain (IXxx), il existe un Fake correspondant dans infrastructure/fake/ — sans Fake, les tests Application nécessitent l'infrastructure réelle et le développement devient séquentiel
