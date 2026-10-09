# i_unit_of_work — Intention

## Rationale

Sans frontière transactionnelle, les boucles de scan publient les événements à la main pendant qu'elles mutent l'état, ce qui signifie qu'un échec après publication laisse des observateurs (UI, audit, handlers) avec un fait jamais validé, ce qui force à raisonner sur des états à moitié appliqués. La règle « un agrégat par transaction » du domaine scan n'a aucun support tant que ce port n'existe pas.

## Responsibility

- Délimiter une transaction (`with uow:`), avec `commit()` explicite.
- Rollback implicite si exception dans le bloc ou si `commit()` n'est jamais appelé.
- Collecter les événements des agrégats enregistrés via `register(aggregate)` et les publier uniquement après commit.

## Design

- ABC pure, aucun attribut-repository pour l'instant : ils arriveront avec leurs repositories.
- Les agrégats exposent `domain_events` (retourne puis vide la liste, convention de `StepScan`).
- La publication a lieu après fermeture de la transaction : un handler peut ouvrir une autre UoW.
