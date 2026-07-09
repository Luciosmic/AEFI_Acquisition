# scan_mode — Intention

## Rationale

Enum domain distinguant les modes de scan disponibles (ex. STEP, FLY). Typer le mode permet d'étendre le système avec un fly-scan sans modifier les interfaces existantes.

## Responsibility

- Définir les modes de scan supportés.

## Design

- **`enum.Enum`**.
- Utilisé pour discriminer la stratégie d'exécution dans le composition root.
