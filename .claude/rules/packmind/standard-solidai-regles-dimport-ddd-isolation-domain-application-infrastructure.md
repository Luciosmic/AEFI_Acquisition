---
name: 'SolidAI — Règles d''Import DDD : Isolation Domain, Application, Infrastructure'
alwaysApply: true
description: 'Enforce strict DDD import rules where domain/ never imports infrastructure/, application/ imports only Domain and uses infrastructure/<adapter>/fake/ in tests (never the Real adapter), and Infrastructure implements Domain interfaces with Real and Fake co-located to preserve layer isolation, independent testability, and parallel development.'
---

# Standard: SolidAI — Règles d'Import DDD : Isolation Domain, Application, Infrastructure

Enforce strict DDD import rules where domain/ never imports infrastructure/, application/ imports only Domain and uses infrastructure/<adapter>/fake/ in tests (never the Real adapter), and Infrastructure implements Domain interfaces with Real and Fake co-located to preserve layer isolation, independent testability, and parallel development. :
* Dans les tests de la couche application/, importer uniquement les Fakes depuis infrastructure/<adapter>/fake/ et jamais l'implémentation Real depuis infrastructure/<adapter>/<adapter>.py
* Implémenter les interfaces du Domain dans la couche Infrastructure (Real à la racine de l'adapter, Fake co-localisé dans <adapter>/fake/) sans créer de dépendances inverses vers l'Application
* Ne jamais importer de code infrastructure dans la couche domain/ — le Domain est pur et doit pouvoir être testé sans aucune dépendance externe

Full standard is available here for further request: [SolidAI — Règles d'Import DDD : Isolation Domain, Application, Infrastructure](../../../.packmind/standards/solidai-regles-dimport-ddd-isolation-domain-application-infrastructure.md)