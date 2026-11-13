# frequency_sweep_dtos — Intention

## Rationale

Le panneau et l'export ne doivent dépendre ni de l'agrégat `FrequencySweep` ni de ses value objects : la frontière du service ne laisse passer que des primitives.

## Responsibility

- `FrequencySweepRequestDTO` : la demande de l'opérateur (rôle, bornes et nombre de fréquences, N par fréquence, hauteur de la table, opérateur). Ses valeurs par défaut sont la seule source des valeurs pré-remplies du panneau.
- `FrequencyPointDTO` : une fréquence acquise (moyenne et écart-type des 6 voies, décalage de phase de la référence de détection synchrone appliqué à cette fréquence).
- `FrequencySweepSampleDTO` : un échantillon brut gardé, pour l'export.
- `FrequencySweepResultDTO` : le balayage tel qu'il s'est terminé, avec son statut et son dossier d'export.
- `VALUE_CHANNELS` : l'ordre des 6 valeurs de chaque tuple ; `ROLE_LABELS` : identifiants stables des rôles et leurs libellés.

## Design

- `@dataclass(frozen=True)`, primitives seulement.
- Le rôle voyage par son identifiant stable (valeur de `FrequencySweepRole`) ; le service le traduit.
- Bornes par défaut (100 Hz à 10 kHz, 21 fréquences) : point de départ à corriger au premier essai au banc.
