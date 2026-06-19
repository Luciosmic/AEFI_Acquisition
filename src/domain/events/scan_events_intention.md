# scan_events — Intention

## Rationale

Modéliser les transitions d'état du scan comme des faits immuables passés. Chaque événement capture les données pertinentes au moment de la transition afin que les consommateurs (UI, handlers de persistence, analytics) puissent réagir sans requêter l'agrégat.

## Responsibility

- `ScanStarted` : scan_id + config complète (pour calculer le total_points côté UI).
- `ScanPointAcquired` : scan_id + point_index + position + measurement (donnée brute pour la carte 2D en temps réel).
- `ScanCompleted` : scan_id + total_points.
- `ScanFailed` : scan_id + reason (string explicative).
- `ScanCancelled` : scan_id.
- `ScanPaused` : scan_id + current_point_index.
- `ScanResumed` : scan_id + resume_from_point_index.

## Design

- **`@dataclass`** héritant de `DomainEvent`.
- Chaque événement est **immuable** : les consommateurs ne peuvent pas le modifier.
- `ScanPointAcquired` porte la `measurement (VoltageMeasurement)` complète pour éviter un second accès à l'agrégat depuis la UI.
