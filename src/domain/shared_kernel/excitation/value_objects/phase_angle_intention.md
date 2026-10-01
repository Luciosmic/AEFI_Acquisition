# phase_angle — Intention

## Rationale

Les phases DDS circulaient jusqu'ici comme entiers bruts 16-bit (0-65535,
ex. `32768` pour 180°) directement dans `adapter_excitation_configuration_ad9106.py`,
sans validation ni sémantique — une valeur métier (un angle) déguisée en détail
registre. Nécessaire pour calculer un déphasage entre deux sphères sans
réinventer l'arithmétique modulo 360 à chaque appelant.

## Responsibility

- Représenter un angle de phase en degrés, toujours normalisé [0, 360).
- Calculer la phase complémentaire (+180°) d'une sortie différentielle DDS.
- Calculer un déphasage signé entre deux phases (le plus court chemin angulaire).
- Convertir depuis/vers le registre 16-bit AD9106 (`from_register`/`to_register`),
  pont explicite entre la réalité domaine et le détail hardware.

## Design

- `@dataclass(frozen=True)`, normalisation modulo 360 dans `__post_init__`.
- Pas de levée d'erreur sur les valeurs hors [0,360) — un angle est cyclique,
  la normalisation est la sémantique correcte, pas une validation d'erreur.
- `DDS_REGISTER_RANGE = 65536` documente explicitement la résolution du
  registre AD9106 (16 bits) sans magic number ailleurs.
