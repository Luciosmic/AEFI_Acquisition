# excitation_mode — Intention

## Rationale

Enum domain définissant les modes d'excitation disponibles sur l'AD9106 (sinusoïdal, DDS, etc.). Typer le mode évite les strings magiques dans `ExcitationParameters` et `AdapterExcitationConfigurationAD9106`.

## Responsibility

- Définir les modes d'excitation valides du système AEFI.

## Design

- **`enum.Enum`** Python standard.
- Référencé dans `ExcitationParameters` et dans l'adaptateur AD9106.
