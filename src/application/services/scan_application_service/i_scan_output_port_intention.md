# i_scan_output_port — Intention

## Rationale

Définir le contrat de présentation des événements de scan vers la UI sans que le service applicatif ne connaisse PySide6 ou une technologie UI particulière. C'est le port de sortie (outbound) du `ScanApplicationService` vers la couche `interface/`.

## Responsibility

- Déclarer les méthodes `present_scan_started`, `present_scan_progress`, `present_scan_completed`, `present_scan_failed`, `present_scan_cancelled`, `present_scan_paused`, `present_scan_resumed`.
- Chaque méthode reçoit des primitives ou DTOs simples (pas d'objets domain).

## Design

- **Port outbound (output port)** : l'Application publie, l'Interface consomme.
- Implémenté par `ScanPresenter` dans `interface/presenters/` qui émet des signaux Qt.
- `ScanApplicationService` appelle ce port depuis `_on_domain_event()` après avoir reçu les événements domain du bus.
