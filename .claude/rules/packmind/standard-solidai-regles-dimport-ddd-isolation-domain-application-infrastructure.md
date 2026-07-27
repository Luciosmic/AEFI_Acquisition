---
name: 'SolidAI — Règles d''Import DDD : Isolation Domain, Application, Infrastructure'
alwaysApply: true
description: 'SolidAI — Règles d''Import DDD : Isolation Domain, Application, Infrastructure'
---

# Standard: SolidAI — Règles d'Import DDD : Isolation Domain, Application, Infrastructure

Ce standard définit les règles strictes d'import entre les couches DDD de SolidAI. Le Domain est pur : il n'importe jamais l'Infrastructure. L'Application importe le Domain et utilise les Fakes co-loc... :
* Dans les tests de la couche application/, importer uniquement les Fakes depuis infrastructure/<adapter>/fake/ et jamais l'implémentation Real depuis infrastructure/<adapter>/<adapter>.py
* Implémenter les interfaces du Domain dans la couche Infrastructure (Real à la racine de l'adapter, Fake co-localisé dans <adapter>/fake/) sans créer de dépendances inverses vers l'Application
* Ne jamais importer de code infrastructure dans la couche domain/ — le Domain est pur et doit pouvoir être testé sans aucune dépendance externe

Full standard is available here for further request: [SolidAI — Règles d'Import DDD : Isolation Domain, Application, Infrastructure](../../../.packmind/standards/solidai-regles-dimport-ddd-isolation-domain-application-infrastructure.md)