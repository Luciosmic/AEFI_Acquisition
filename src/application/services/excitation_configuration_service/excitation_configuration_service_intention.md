# excitation_configuration_service — Intention

## Rationale

Isoler la configuration du générateur d'excitation DDS (AD9106) de la UI et du domain. La couche applicative traduit les intentions utilisateur (paramètres d'excitation) vers le port outbound `IExcitationPort` sans connaître les détails du protocole SPI/série.

## Responsibility

- Appliquer une configuration d'excitation (fréquence, amplitude, mode) via `IExcitationPort`.
- Valider les paramètres domain si nécessaire avant de les transmettre.
- Fournir un point d'entrée unique pour toute configuration d'excitation.

## Design

- **Dépendance unique `IExcitationPort`** : le service ne connaît que le contrat, pas l'implémentation AD9106.
- **Pattern service applicatif thin** : délègue la logique hardware au port, ne contient pas de calculs DDS.
