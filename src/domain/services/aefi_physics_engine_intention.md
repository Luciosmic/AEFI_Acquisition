# aefi_physics_engine — Intention

## Rationale

Service domain encapsulant le modèle physique du problème direct AEFI : calcul du champ électrique quasi-statique généré par les sources de l'instrument à une position donnée. C'est le cœur de la physique du problème direct, indépendant du hardware et des données expérimentales.

## Responsibility

- Calculer la réponse du champ électrique attendue pour une configuration de sources et une position de scan donnée.
- Fournir les fonctions de base pour la validation des données expérimentales et l'inversion.

## Design

- **Service domain pur** : aucune dépendance infrastructure, entrée = value objects domain, sortie = value objects domain.
- Candidat à l'utilisation dans les tests de validation (comparer mesures expérimentales vs modèle).
