# SolidAI — Règles d'Import DDD : Isolation Domain, Application, Infrastructure

Ce standard définit les règles strictes d'import entre les couches DDD de SolidAI. Le Domain est pur : il n'importe jamais l'Infrastructure. L'Application importe le Domain et utilise les Fakes co-localisés (infrastructure/<adapter>/fake/) dans ses tests. Les implémentations Real et leurs Fakes co-existent dans le même dossier d'adapter ; l'Infrastructure implémente les interfaces du Domain sans créer de dépendances inverses. Ces règles garantissent l'isolation des couches, la testabilité indépendante et la possibilité de développement parallèle.

## Rules

* Ne jamais importer de code infrastructure dans la couche domain/ — le Domain est pur et doit pouvoir être testé sans aucune dépendance externe
* Dans les tests de la couche application/, importer uniquement les Fakes depuis infrastructure/<adapter>/fake/ et jamais l'implémentation Real depuis infrastructure/<adapter>/<adapter>.py
* Implémenter les interfaces du Domain dans la couche Infrastructure (Real à la racine de l'adapter, Fake co-localisé dans <adapter>/fake/) sans créer de dépendances inverses vers l'Application
