# domain_event — Intention

## Rationale

Classe de base pour tous les événements domain du système AEFI. Fournit un `event_id` UUID et un `occurred_on` timestamp automatiques afin que tous les événements soient traçables et ordonnables dans le temps — condition nécessaire pour l'event audit log (voir `_system/self/event_store.md`) qui persiste chaque événement publié sur `IDomainEventBus`.

## Responsibility

- Définir les champs communs : `event_id` (UUID4) et `occurred_on` (datetime UTC).
- Servir de type commun pour le dispatch typé dans les handlers et sur `IDomainEventBus`.

## Design

- **`@dataclass`** avec champs optionnels à valeur par défaut (`field(default_factory=...)`).
- **Héritée par tous les événements domain** : ScanEvents, MotionEvents, SystemEvents, etc.
- Pas de logique métier — pure structure de données.
- Pas de `correlation_id` au niveau de la base : les événements qui ont besoin d'être corrélés entre eux (un scan complet, une acquisition) portent déjà leur propre `scan_id`/`acquisition_id` — pas de champ dupliqué tant qu'un seul scan tourne à la fois.
