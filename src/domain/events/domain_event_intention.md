# domain_event — Intention

## Rationale

Classe de base pour tous les événements domain du système AEFI. Fournit un `event_id` UUID et un `occurred_at` timestamp automatiques afin que tous les événements soient traçables et ordonnables dans le temps.

## Responsibility

- Définir les champs communs : `event_id` (UUID4) et `occurred_at` (datetime UTC).
- Servir de type commun pour le dispatch typé dans les handlers et sur `IDomainEventBus`.

## Design

- **`@dataclass`** avec champs optionnels à valeur par défaut (`field(default_factory=...)`).
- **Héritée par tous les événements domain** : ScanEvents, MotionEvents, SystemEvents, etc.
- Pas de logique métier — pure structure de données.
