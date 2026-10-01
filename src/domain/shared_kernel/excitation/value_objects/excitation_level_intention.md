# excitation_level — Intention

## Rationale

Value object représentant le niveau d'excitation (amplitude) en unités domain (volts ou valeur normalisée). Séparer le niveau d'excitation des paramètres complets permet une manipulation granulaire dans l'UI de configuration.

## Responsibility

- Stocker et valider le niveau d'excitation.
- Fournir une conversion si nécessaire (ex. valeur normalisée → DAC count).

## Design

- **`@dataclass(frozen=True)`** ou `enum`.
- Cohérent avec `ExcitationParameters` dont il est un champ.
