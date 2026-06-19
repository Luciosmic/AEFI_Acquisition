---
name: 'SolidAI — Test Doubles DDD : Fake In-Memory vs Mock, Placement Infrastructure'
alwaysApply: true
description: 'Définit la distinction Fake (implémentation in-memory) vs Mock (vérification d''interactions), impose leur placement dans infrastructure/fake/ avec le trio atomique complet, et exige que chaque interface Domain ait un Fake correspondant testé.'
---

# Standard: SolidAI — Test Doubles DDD : Fake In-Memory vs Mock, Placement Infrastructure

Définit la distinction Fake (implémentation in-memory) vs Mock (vérification d'interactions), impose leur placement dans infrastructure/fake/ avec le trio atomique complet, et exige que chaque interface Domain ait un Fake correspondant testé. :
* Placer les Fakes dans infrastructure/fake/[catégorie]/[module]/ avec le trio atomique complet (<module>_intention.md + implémentation + _tests/)
* S'assurer que pour chaque interface Domain (IXxx), il existe un Fake correspondant dans infrastructure/fake/ — sans Fake, les tests Application nécessitent l'infrastructure réelle et le développement devient séquentiel
* Tester le Fake lui-même pour garantir qu'il respecte le contrat de l'interface Domain — cette validation est le garant de la propagation des tests vers l'infrastructure réelle
* Utiliser des Fakes (implémentation in-memory fonctionnelle) plutôt que des Mocks (vérification d'interactions) pour tester les use cases applicatifs — le Fake permet la vérification d'état, le Mock vérifie les appels

Full standard is available here for further request: [SolidAI — Test Doubles DDD : Fake In-Memory vs Mock, Placement Infrastructure](../../../.packmind/standards/solidai-test-doubles-ddd-fake-in-memory-vs-mock-placement-infrastructure.md)